#!/usr/bin/env python3
"""
Enhanced LM Studio Server for HPC Environments
- Better error handling and memory management
- GPU memory monitoring and debugging
- Improved UI with real-time status
- Model size recommendations
"""

import os
import sys
import json
import torch
import gc
import psutil
import time
from flask import Flask, request, jsonify, render_template_string
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import threading
import subprocess

# Set up environment variables for datalab
os.environ['HF_HOME'] = '/cluster/tufts/datalab/zwu09/caches/huggingface'
os.environ['TRANSFORMERS_CACHE'] = '/cluster/tufts/datalab/zwu09/caches/huggingface'
os.environ['TORCH_HOME'] = '/cluster/tufts/datalab/zwu09/caches/torch'
os.environ['TMPDIR'] = '/cluster/tufts/datalab/zwu09/tmp'

# Create cache directories
for cache_dir in [os.environ['HF_HOME'], os.environ['TORCH_HOME'], os.environ['TMPDIR']]:
    os.makedirs(cache_dir, exist_ok=True)

app = Flask(__name__)

# Global variables for model management
current_model = None
current_tokenizer = None
model_name = None
device = "cuda" if torch.cuda.is_available() else "cpu"
server_start_time = time.time()

def get_gpu_memory_info():
    """Get detailed GPU memory information"""
    if not torch.cuda.is_available():
        return {"available": False, "total": 0, "used": 0, "free": 0}
    
    try:
        total_memory = torch.cuda.get_device_properties(0).total_memory
        allocated_memory = torch.cuda.memory_allocated(0)
        cached_memory = torch.cuda.memory_reserved(0)
        free_memory = total_memory - allocated_memory
        
        return {
            "available": True,
            "total": total_memory / 1e9,  # Convert to GB
            "used": allocated_memory / 1e9,
            "cached": cached_memory / 1e9,
            "free": free_memory / 1e9,
            "device_name": torch.cuda.get_device_name(0)
        }
    except Exception as e:
        return {"available": False, "error": str(e)}

def get_system_info():
    """Get system resource information"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/cluster/tufts/datalab')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_total": memory.total / 1e9,
            "memory_used": memory.used / 1e9,
            "memory_percent": memory.percent,
            "disk_total": disk.total / 1e9,
            "disk_used": disk.used / 1e9,
            "disk_percent": (disk.used / disk.total) * 100
        }
    except Exception as e:
        return {"error": str(e)}

def estimate_model_memory(model_name):
    """Estimate memory requirements for different models"""
    model_sizes = {
        # Small models (1B parameters or less)
        "gpt2": {"params": 0.117, "memory_gb": 0.5},
        "microsoft/DialoGPT-small": {"params": 0.117, "memory_gb": 0.5},
        "microsoft/DialoGPT-medium": {"params": 0.345, "memory_gb": 1.5},
        "microsoft/DialoGPT-large": {"params": 0.774, "memory_gb": 3.0},
        
        # Medium models (1B-10B parameters)
        "mistralai/Mistral-7B-Instruct-v0.1": {"params": 7, "memory_gb": 14},
        "meta-llama/Llama-2-7b-chat-hf": {"params": 7, "memory_gb": 14},
        "codellama/CodeLlama-7b-Python-hf": {"params": 7, "memory_gb": 14},
        "meta-llama/Llama-2-13b-chat-hf": {"params": 13, "memory_gb": 26},
        
        # Large models (10B+ parameters)
        "codellama/CodeLlama-34b-Python-hf": {"params": 34, "memory_gb": 68},
        "meta-llama/Llama-2-70b-chat-hf": {"params": 70, "memory_gb": 140},
    }
    
    # Check for exact match first
    if model_name in model_sizes:
        return model_sizes[model_name]
    
    # Try to extract size from model name
    for key, info in model_sizes.items():
        if any(size in model_name.lower() for size in ["7b", "7b-", "13b", "34b", "70b"]):
            return info
    
    # Default estimate based on common patterns
    if "7b" in model_name.lower():
        return {"params": 7, "memory_gb": 14}
    elif "13b" in model_name.lower():
        return {"params": 13, "memory_gb": 26}
    elif "34b" in model_name.lower():
        return {"params": 34, "memory_gb": 68}
    elif "70b" in model_name.lower():
        return {"params": 70, "memory_gb": 140}
    else:
        return {"params": "unknown", "memory_gb": "unknown"}

# HTML template for the enhanced web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LM Studio - HPC Edition (Enhanced)</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #333; margin-bottom: 30px; }
        .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .debug-panel { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid #007bff; }
        .model-selector { margin-bottom: 20px; }
        .chat-container { display: flex; gap: 20px; }
        .chat-input { flex: 1; }
        .chat-output { flex: 1; background: #f9f9f9; padding: 15px; border-radius: 5px; min-height: 400px; }
        .model-recommendations { background: #fff3cd; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid #ffc107; }
        textarea { width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        button:disabled { background: #6c757d; cursor: not-allowed; }
        .model-info { background: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .error { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .success { background: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .warning { background: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .metric { background: #f8f9fa; padding: 10px; border-radius: 5px; text-align: center; }
        .metric-value { font-size: 1.5em; font-weight: bold; color: #007bff; }
        .metric-label { font-size: 0.9em; color: #6c757d; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 LM Studio - HPC Edition (Enhanced)</h1>
            <p>Running on Tufts HPC with GPU acceleration | Enhanced with debugging & monitoring</p>
        </div>
        
        <div class="status">
            <strong>Status:</strong> <span id="status">Ready</span> | 
            <strong>GPU:</strong> <span id="gpu-info">Checking...</span> | 
            <strong>Model:</strong> <span id="current-model">None loaded</span> |
            <strong>Uptime:</strong> <span id="uptime">Calculating...</span>
        </div>
        
        <div class="debug-panel">
            <h3>🔍 System Monitoring</h3>
            <div class="grid">
                <div class="metric">
                    <div class="metric-value" id="gpu-memory-used">-</div>
                    <div class="metric-label">GPU Memory Used (GB)</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="gpu-memory-total">-</div>
                    <div class="metric-label">GPU Memory Total (GB)</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="cpu-usage">-</div>
                    <div class="metric-label">CPU Usage (%)</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="memory-usage">-</div>
                    <div class="metric-label">RAM Usage (%)</div>
                </div>
            </div>
        </div>
        
        <div class="model-recommendations">
            <h3>💡 Model Recommendations</h3>
            <p><strong>Start Small:</strong> <code>microsoft/DialoGPT-small</code> (117M params, ~0.5GB)</p>
            <p><strong>Medium:</strong> <code>mistralai/Mistral-7B-Instruct-v0.1</code> (7B params, ~14GB)</p>
            <p><strong>Large:</strong> <code>meta-llama/Llama-2-13b-chat-hf</code> (13B params, ~26GB)</p>
            <p><strong>Very Large:</strong> <code>codellama/CodeLlama-34b-Python-hf</code> (34B params, ~68GB)</p>
        </div>
        
        <div class="model-selector">
            <h3>Load Model</h3>
            <input type="text" id="model-input" placeholder="Enter Hugging Face model name" style="width: 400px; padding: 8px;">
            <button onclick="loadModel()" id="load-btn">Load Model</button>
            <button onclick="unloadModel()" id="unload-btn">Unload Model</button>
            <button onclick="clearCache()" id="cache-btn">Clear GPU Cache</button>
            <div id="model-estimate" style="margin-top: 10px; font-style: italic;"></div>
        </div>
        
        <div class="model-info" id="model-info" style="display: none;">
            <h4>Model Information</h4>
            <div id="model-details"></div>
        </div>
        
        <div class="chat-container">
            <div class="chat-input">
                <h3>Input</h3>
                <textarea id="user-input" placeholder="Enter your prompt here..."></textarea>
                <br><br>
                <button onclick="generateText()" id="generate-btn">Generate</button>
                <button onclick="clearChat()">Clear</button>
                <br><br>
                <label>Max Length: <input type="number" id="max-length" value="100" style="width: 80px;"></label>
                <label>Temperature: <input type="number" id="temperature" value="0.7" step="0.1" min="0" max="2" style="width: 80px;"></label>
            </div>
            
            <div class="chat-output">
                <h3>Output</h3>
                <div id="output" style="white-space: pre-wrap; font-family: monospace;"></div>
            </div>
        </div>
        
        <div id="messages"></div>
    </div>

    <script>
        let startTime = Date.now();
        
        function updateUptime() {
            const uptime = Math.floor((Date.now() - startTime) / 1000);
            const hours = Math.floor(uptime / 3600);
            const minutes = Math.floor((uptime % 3600) / 60);
            const seconds = uptime % 60;
            document.getElementById('uptime').textContent = `${hours}h ${minutes}m ${seconds}s`;
        }
        
        function showMessage(message, type = 'info') {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = type;
            messageDiv.textContent = message;
            messagesDiv.appendChild(messageDiv);
            setTimeout(() => messageDiv.remove(), 5000);
        }
        
        function updateStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').textContent = data.status;
                    document.getElementById('gpu-info').textContent = data.gpu_info;
                    document.getElementById('current-model').textContent = data.model_name || 'None loaded';
                    
                    // Update system metrics
                    if (data.gpu_memory) {
                        document.getElementById('gpu-memory-used').textContent = data.gpu_memory.used.toFixed(1);
                        document.getElementById('gpu-memory-total').textContent = data.gpu_memory.total.toFixed(1);
                    }
                    if (data.system_info) {
                        document.getElementById('cpu-usage').textContent = data.system_info.cpu_percent.toFixed(1);
                        document.getElementById('memory-usage').textContent = data.system_info.memory_percent.toFixed(1);
                    }
                })
                .catch(error => {
                    console.error('Status update failed:', error);
                });
        }
        
        function estimateModelMemory() {
            const modelName = document.getElementById('model-input').value;
            if (!modelName) {
                document.getElementById('model-estimate').textContent = '';
                return;
            }
            
            fetch('/estimate_memory', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({model_name: modelName})
            })
            .then(response => response.json())
            .then(data => {
                if (data.estimate) {
                    const estimate = data.estimate;
                    let text = `Estimated: ${estimate.params}B parameters, ~${estimate.memory_gb}GB memory`;
                    if (data.warning) {
                        text += ` ⚠️ ${data.warning}`;
                    }
                    document.getElementById('model-estimate').textContent = text;
                }
            });
        }
        
        function loadModel() {
            const modelName = document.getElementById('model-input').value;
            if (!modelName) {
                showMessage('Please enter a model name', 'error');
                return;
            }
            
            document.getElementById('load-btn').disabled = true;
            document.getElementById('status').textContent = 'Loading model...';
            showMessage(`Loading model: ${modelName}`, 'info');
            
            fetch('/load_model', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({model_name: modelName})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('model-info').style.display = 'block';
                    document.getElementById('model-details').innerHTML = `
                        <strong>Model:</strong> ${data.model_name}<br>
                        <strong>Device:</strong> ${data.device}<br>
                        <strong>Parameters:</strong> ${data.parameters || 'Unknown'}<br>
                        <strong>Status:</strong> ${data.status}<br>
                        <strong>Memory Used:</strong> ${data.memory_used || 'Unknown'} GB
                    `;
                    showMessage('Model loaded successfully!', 'success');
                } else {
                    showMessage('Error loading model: ' + data.error, 'error');
                }
                document.getElementById('load-btn').disabled = false;
                updateStatus();
            })
            .catch(error => {
                showMessage('Network error: ' + error, 'error');
                document.getElementById('load-btn').disabled = false;
                updateStatus();
            });
        }
        
        function unloadModel() {
            document.getElementById('unload-btn').disabled = true;
            showMessage('Unloading model...', 'info');
            
            fetch('/unload_model', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('model-info').style.display = 'none';
                        showMessage('Model unloaded successfully', 'success');
                    } else {
                        showMessage('Error unloading model: ' + data.error, 'error');
                    }
                    document.getElementById('unload-btn').disabled = false;
                    updateStatus();
                });
        }
        
        function clearCache() {
            document.getElementById('cache-btn').disabled = true;
            showMessage('Clearing GPU cache...', 'info');
            
            fetch('/clear_cache', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showMessage('GPU cache cleared', 'success');
                    } else {
                        showMessage('Error clearing cache: ' + data.error, 'error');
                    }
                    document.getElementById('cache-btn').disabled = false;
                    updateStatus();
                });
        }
        
        function generateText() {
            const input = document.getElementById('user-input').value;
            const maxLength = parseInt(document.getElementById('max-length').value);
            const temperature = parseFloat(document.getElementById('temperature').value);
            
            if (!input) {
                showMessage('Please enter some text', 'error');
                return;
            }
            
            document.getElementById('generate-btn').disabled = true;
            document.getElementById('status').textContent = 'Generating...';
            document.getElementById('output').textContent = 'Generating response...';
            showMessage('Generating text...', 'info');
            
            fetch('/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    text: input,
                    max_length: maxLength,
                    temperature: temperature
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('output').textContent = data.generated_text;
                    showMessage('Text generated successfully!', 'success');
                } else {
                    document.getElementById('output').textContent = 'Error: ' + data.error;
                    showMessage('Generation failed: ' + data.error, 'error');
                }
                document.getElementById('generate-btn').disabled = false;
                updateStatus();
            })
            .catch(error => {
                document.getElementById('output').textContent = 'Network error: ' + error;
                showMessage('Network error: ' + error, 'error');
                document.getElementById('generate-btn').disabled = false;
                updateStatus();
            });
        }
        
        function clearChat() {
            document.getElementById('user-input').value = '';
            document.getElementById('output').textContent = '';
        }
        
        // Update status every 3 seconds
        setInterval(updateStatus, 3000);
        setInterval(updateUptime, 1000);
        
        // Estimate memory when typing model name
        document.getElementById('model-input').addEventListener('input', estimateModelMemory);
        
        // Initial status update
        updateStatus();
        updateUptime();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    gpu_info = "Not available"
    gpu_memory = get_gpu_memory_info()
    system_info = get_system_info()
    
    if torch.cuda.is_available():
        gpu_info = f"GPU {torch.cuda.current_device()}: {torch.cuda.get_device_name()}"
    
    return jsonify({
        'status': 'Ready' if current_model is None else 'Model loaded',
        'gpu_info': gpu_info,
        'model_name': model_name,
        'gpu_memory': gpu_memory,
        'system_info': system_info,
        'uptime': time.time() - server_start_time
    })

@app.route('/estimate_memory', methods=['POST'])
def estimate_memory():
    try:
        data = request.get_json()
        model_name = data['model_name']
        estimate = estimate_model_memory(model_name)
        
        # Check if model will fit in available GPU memory
        gpu_memory = get_gpu_memory_info()
        warning = None
        
        if gpu_memory['available'] and estimate['memory_gb'] != 'unknown':
            if estimate['memory_gb'] > gpu_memory['total']:
                warning = "Model too large for GPU memory!"
            elif estimate['memory_gb'] > gpu_memory['free']:
                warning = "May need to unload current model first"
        
        return jsonify({
            'estimate': estimate,
            'warning': warning
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/load_model', methods=['POST'])
def load_model():
    global current_model, current_tokenizer, model_name
    
    try:
        data = request.get_json()
        model_name = data['model_name']
        
        # Check memory requirements
        estimate = estimate_model_memory(model_name)
        gpu_memory = get_gpu_memory_info()
        
        if gpu_memory['available'] and estimate['memory_gb'] != 'unknown':
            if estimate['memory_gb'] > gpu_memory['total']:
                return jsonify({
                    'success': False,
                    'error': f'Model requires {estimate["memory_gb"]}GB but GPU only has {gpu_memory["total"]:.1f}GB total memory'
                })
        
        # Unload previous model to free memory
        if current_model is not None:
            del current_model
            del current_tokenizer
            torch.cuda.empty_cache()
            gc.collect()
        
        print(f"Loading model: {model_name}")
        print(f"GPU memory before loading: {get_gpu_memory_info()}")
        
        # Load tokenizer and model
        current_tokenizer = AutoTokenizer.from_pretrained(model_name)
        current_model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            low_cpu_mem_usage=True
        )
        
        # Move to device if not using device_map
        if device == "cuda" and not hasattr(current_model, 'hf_device_map'):
            current_model = current_model.to(device)
        
        # Get model info
        num_params = sum(p.numel() for p in current_model.parameters())
        memory_used = get_gpu_memory_info()['used'] if get_gpu_memory_info()['available'] else 'Unknown'
        
        print(f"Model loaded successfully. GPU memory after loading: {get_gpu_memory_info()}")
        
        return jsonify({
            'success': True,
            'model_name': model_name,
            'device': device,
            'parameters': f"{num_params:,}",
            'memory_used': memory_used,
            'status': 'Loaded successfully'
        })
        
    except Exception as e:
        print(f"Error loading model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/unload_model', methods=['POST'])
def unload_model():
    global current_model, current_tokenizer, model_name
    
    try:
        if current_model is not None:
            del current_model
            del current_tokenizer
            torch.cuda.empty_cache()
            gc.collect()
        
        current_model = None
        current_tokenizer = None
        model_name = None
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/clear_cache', methods=['POST'])
def clear_cache():
    try:
        torch.cuda.empty_cache()
        gc.collect()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate', methods=['POST'])
def generate():
    try:
        if current_model is None or current_tokenizer is None:
            return jsonify({
                'success': False,
                'error': 'No model loaded'
            })
        
        data = request.get_json()
        text = data['text']
        max_length = data.get('max_length', 100)
        temperature = data.get('temperature', 0.7)
        
        print(f"Generating text with model: {model_name}")
        print(f"Input: {text[:100]}...")
        print(f"GPU memory before generation: {get_gpu_memory_info()}")
        
        # Tokenize input
        inputs = current_tokenizer.encode(text, return_tensors='pt')
        if device == "cuda":
            inputs = inputs.to(device)
        
        # Generate
        with torch.no_grad():
            outputs = current_model.generate(
                inputs,
                max_length=inputs.shape[1] + max_length,
                temperature=temperature,
                do_sample=True,
                pad_token_id=current_tokenizer.eos_token_id,
                eos_token_id=current_tokenizer.eos_token_id
            )
        
        # Decode output
        generated_text = current_tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove input from output
        if generated_text.startswith(text):
            generated_text = generated_text[len(text):].strip()
        
        print(f"Generation complete. GPU memory after generation: {get_gpu_memory_info()}")
        
        return jsonify({
            'success': True,
            'generated_text': generated_text
        })
        
    except Exception as e:
        print(f"Error during generation: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("🚀 Starting Enhanced LM Studio Server...")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        gpu_info = get_gpu_memory_info()
        print(f"GPU: {gpu_info['device_name']}")
        print(f"GPU Memory: {gpu_info['total']:.1f} GB total, {gpu_info['free']:.1f} GB free")
    
    system_info = get_system_info()
    print(f"System: {system_info['memory_total']:.1f} GB RAM, {system_info['disk_total']:.1f} GB disk")
    print(f"Working directory: {os.getcwd()}")
    print(f"Cache directories: HF_HOME={os.environ['HF_HOME']}")
    
    app.run(host='0.0.0.0', port=8080, debug=False)
