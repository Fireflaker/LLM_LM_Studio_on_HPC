#!/usr/bin/env python3
"""
Fixed LM Studio Server for HPC
- Fixed variable scope issues
- Improved text generation with proper parameters
- Better error handling
"""

import os
import sys
import json
import torch
import gc
import psutil
from flask import Flask, request, jsonify, render_template_string
from transformers import AutoTokenizer, AutoModelForCausalLM
import time

# Set up environment variables
os.environ['HF_HOME'] = '/cluster/tufts/datalab/zwu09/caches/huggingface'
os.environ['TRANSFORMERS_CACHE'] = '/cluster/tufts/datalab/zwu09/caches/huggingface'
os.environ['TORCH_HOME'] = '/cluster/tufts/datalab/zwu09/caches/torch'
os.environ['TMPDIR'] = '/cluster/tufts/datalab/zwu09/tmp'

app = Flask(__name__)

# Global state
class ModelState:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_name = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

state = ModelState()

def get_gpu_info():
    """Get GPU information"""
    if not torch.cuda.is_available():
        return {"available": False}
    
    try:
        gpu_count = torch.cuda.device_count()
        gpus = []
        for i in range(gpu_count):
            props = torch.cuda.get_device_properties(i)
            gpus.append({
                "id": i,
                "name": torch.cuda.get_device_name(i),
                "total_memory": props.total_memory / 1e9,
                "allocated": torch.cuda.memory_allocated(i) / 1e9,
                "free": (props.total_memory - torch.cuda.memory_allocated(i)) / 1e9
            })
        return {"available": True, "count": gpu_count, "gpus": gpus}
    except Exception as e:
        return {"available": False, "error": str(e)}

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LM Studio - HPC Edition (Fixed)</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        .header { text-align: center; color: #333; margin-bottom: 30px; }
        .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .model-selector { margin-bottom: 20px; }
        .chat-container { display: flex; gap: 20px; }
        .chat-input, .chat-output { flex: 1; }
        .chat-output { background: #f9f9f9; padding: 15px; border-radius: 5px; min-height: 400px; }
        textarea { width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        button:disabled { background: #6c757d; cursor: not-allowed; }
        .info { background: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .warning { background: #fff3cd; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .error { background: #f8d7da; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .success { background: #d4edda; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .recommendations { background: #fff3cd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 LM Studio - HPC Edition (Fixed)</h1>
            <p>Running on Tufts HPC with GPU acceleration</p>
        </div>
        
        <div class="status">
            <strong>Status:</strong> <span id="status">Ready</span> | 
            <strong>GPU:</strong> <span id="gpu-info">Checking...</span> | 
            <strong>Model:</strong> <span id="current-model">None</span>
        </div>
        
        <div class="recommendations">
            <h3>💡 Recommended Models</h3>
            <p><strong>Small (test):</strong> <code>gpt2</code> or <code>microsoft/DialoGPT-small</code></p>
            <p><strong>Medium:</strong> <code>microsoft/DialoGPT-medium</code> or <code>mistralai/Mistral-7B-Instruct-v0.1</code></p>
            <p><strong>Large:</strong> <code>meta-llama/Llama-2-7b-chat-hf</code> or <code>codellama/CodeLlama-7b-Python-hf</code></p>
            <p><strong>Very Large (2xH100):</strong> <code>meta-llama/Llama-2-13b-chat-hf</code> or <code>codellama/CodeLlama-34b-Python-hf</code></p>
        </div>
        
        <div class="model-selector">
            <h3>Model Management</h3>
            <input type="text" id="model-input" placeholder="Enter model name (e.g., gpt2)" style="width: 400px; padding: 8px;">
            <button onclick="loadModel()" id="load-btn">Load Model</button>
            <button onclick="unloadModel()" id="unload-btn">Unload Model</button>
        </div>
        
        <div class="info" id="model-info" style="display: none;">
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
                <label>Max New Tokens: <input type="number" id="max-tokens" value="50" min="10" max="200" style="width: 80px;"></label>
                <label>Temperature: <input type="number" id="temperature" value="0.8" step="0.1" min="0.1" max="2" style="width: 80px;"></label>
                <label>Top P: <input type="number" id="top-p" value="0.9" step="0.05" min="0" max="1" style="width: 80px;"></label>
            </div>
            
            <div class="chat-output">
                <h3>Output</h3>
                <div id="output" style="white-space: pre-wrap;"></div>
            </div>
        </div>
        
        <div id="messages"></div>
    </div>

    <script>
        function showMessage(msg, type='info') {
            const div = document.createElement('div');
            div.className = type;
            div.textContent = msg;
            document.getElementById('messages').appendChild(div);
            setTimeout(() => div.remove(), 5000);
        }
        
        function updateStatus() {
            fetch('/status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('status').textContent = data.status;
                    document.getElementById('gpu-info').textContent = data.gpu_info;
                    document.getElementById('current-model').textContent = data.model_name || 'None';
                })
                .catch(e => console.error('Status update failed:', e));
        }
        
        function loadModel() {
            const modelName = document.getElementById('model-input').value.trim();
            if (!modelName) {
                showMessage('Please enter a model name', 'error');
                return;
            }
            
            document.getElementById('load-btn').disabled = true;
            showMessage('Loading model: ' + modelName, 'info');
            
            fetch('/load_model', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({model_name: modelName})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('model-info').style.display = 'block';
                    document.getElementById('model-details').innerHTML = 
                        '<strong>Model:</strong> ' + data.model_name + '<br>' +
                        '<strong>Device:</strong> ' + data.device + '<br>' +
                        '<strong>Parameters:</strong> ' + (data.parameters || 'Unknown');
                    showMessage('Model loaded successfully!', 'success');
                } else {
                    showMessage('Error: ' + data.error, 'error');
                }
                document.getElementById('load-btn').disabled = false;
                updateStatus();
            })
            .catch(e => {
                showMessage('Network error: ' + e, 'error');
                document.getElementById('load-btn').disabled = false;
            });
        }
        
        function unloadModel() {
            fetch('/unload_model', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('model-info').style.display = 'none';
                        showMessage('Model unloaded', 'success');
                    }
                    updateStatus();
                });
        }
        
        function generateText() {
            const input = document.getElementById('user-input').value.trim();
            if (!input) {
                showMessage('Please enter some text', 'error');
                return;
            }
            
            document.getElementById('generate-btn').disabled = true;
            document.getElementById('output').textContent = 'Generating...';
            
            fetch('/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    text: input,
                    max_new_tokens: parseInt(document.getElementById('max-tokens').value),
                    temperature: parseFloat(document.getElementById('temperature').value),
                    top_p: parseFloat(document.getElementById('top-p').value)
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('output').textContent = data.generated_text;
                    showMessage('Generated successfully!', 'success');
                } else {
                    document.getElementById('output').textContent = 'Error: ' + data.error;
                    showMessage('Generation failed: ' + data.error, 'error');
                }
                document.getElementById('generate-btn').disabled = false;
            })
            .catch(e => {
                document.getElementById('output').textContent = 'Error: ' + e;
                showMessage('Network error: ' + e, 'error');
                document.getElementById('generate-btn').disabled = false;
            });
        }
        
        function clearChat() {
            document.getElementById('user-input').value = '';
            document.getElementById('output').textContent = '';
        }
        
        setInterval(updateStatus, 3000);
        updateStatus();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    gpu_info_data = get_gpu_info()
    gpu_text = "Not available"
    
    if gpu_info_data.get('available'):
        gpu_count = gpu_info_data.get('count', 0)
        if gpu_count > 0:
            gpu_names = [g['name'] for g in gpu_info_data['gpus']]
            gpu_text = f"{gpu_count}x {gpu_names[0]}"
    
    return jsonify({
        'status': 'Ready' if state.model is None else 'Model loaded',
        'gpu_info': gpu_text,
        'model_name': state.model_name,
        'gpu_details': gpu_info_data
    })

@app.route('/load_model', methods=['POST'])
def load_model():
    try:
        data = request.get_json()
        model_name = data['model_name']
        
        # Unload previous model
        if state.model is not None:
            del state.model
            del state.tokenizer
            torch.cuda.empty_cache()
            gc.collect()
        
        print(f"Loading model: {model_name}")
        
        # Load tokenizer
        state.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Add pad token if missing (common for GPT-2 models)
        if state.tokenizer.pad_token is None:
            state.tokenizer.pad_token = state.tokenizer.eos_token
        
        # Load model
        state.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if state.device == "cuda" else torch.float32,
            device_map="auto" if state.device == "cuda" else None,
            low_cpu_mem_usage=True
        )
        
        state.model_name = model_name
        
        # Get parameter count
        num_params = sum(p.numel() for p in state.model.parameters())
        
        print(f"Model loaded successfully: {num_params:,} parameters")
        
        return jsonify({
            'success': True,
            'model_name': model_name,
            'device': state.device,
            'parameters': f"{num_params:,}"
        })
        
    except Exception as e:
        print(f"Error loading model: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/unload_model', methods=['POST'])
def unload_model():
    try:
        if state.model is not None:
            del state.model
            del state.tokenizer
            torch.cuda.empty_cache()
            gc.collect()
        
        state.model = None
        state.tokenizer = None
        state.model_name = None
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate', methods=['POST'])
def generate():
    try:
        if state.model is None or state.tokenizer is None:
            return jsonify({
                'success': False,
                'error': 'No model loaded. Please load a model first.'
            })
        
        data = request.get_json()
        text = data['text']
        max_new_tokens = data.get('max_new_tokens', 50)
        temperature = data.get('temperature', 0.8)
        top_p = data.get('top_p', 0.9)
        
        print(f"Generating text for: '{text[:50]}...'")
        
        # Tokenize input
        inputs = state.tokenizer(text, return_tensors='pt', padding=True)
        
        if state.device == "cuda":
            inputs = {k: v.to(state.device) for k, v in inputs.items()}
        
        input_length = inputs['input_ids'].shape[1]
        print(f"Input tokens: {input_length}")
        
        # Generate with better parameters
        with torch.no_grad():
            outputs = state.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=state.tokenizer.pad_token_id,
                eos_token_id=state.tokenizer.eos_token_id,
                repetition_penalty=1.1,  # Reduce repetition
                no_repeat_ngram_size=3   # Avoid repeating 3-grams
            )
        
        # Decode only the new tokens
        generated_text = state.tokenizer.decode(outputs[0][input_length:], skip_special_tokens=True)
        
        print(f"Generated text: '{generated_text[:100]}...'")
        
        return jsonify({
            'success': True,
            'generated_text': generated_text
        })
        
    except Exception as e:
        print(f"Error during generation: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("🚀 Starting Fixed LM Studio Server...")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        print(f"GPU Count: {gpu_count}")
        for i in range(gpu_count):
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            props = torch.cuda.get_device_properties(i)
            print(f"GPU {i} Memory: {props.total_memory / 1e9:.1f} GB")
    
    print(f"Working directory: {os.getcwd()}")
    print(f"Cache directory: {os.environ['HF_HOME']}")
    
    app.run(host='0.0.0.0', port=8080, debug=False)
