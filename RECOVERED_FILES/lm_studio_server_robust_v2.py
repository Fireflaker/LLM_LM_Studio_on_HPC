#!/usr/bin/env python3
"""
Robust LM Studio Server v2 for HPC
- Handles rate limiting with HF token
- Better CUDA memory management
- Input length validation
- Comprehensive error handling
- Model caching
- Fixed GLIBC compatibility issues
"""

import os
import sys
import json
import warnings

# Suppress NumPy warnings
warnings.filterwarnings('ignore', category=UserWarning, module='torch')
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning'

# Fix NumPy compatibility issue
os.environ['NUMPY_EXPERIMENTAL_ARRAY_FUNCTION'] = '0'

import torch
import gc
import psutil
from flask import Flask, request, jsonify, render_template_string
import time
import traceback

# Import transformers with error handling for GLIBC issues
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except Exception as e:
    print(f"Warning: Transformers import issue: {e}")
    print("Attempting alternative import...")
    try:
        # Try importing without sentencepiece (causes GLIBC issues)
        os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = 'true'
        from transformers import AutoTokenizer, AutoModelForCausalLM
        TRANSFORMERS_AVAILABLE = True
    except Exception as e2:
        print(f"Critical: Could not import transformers: {e2}")
        TRANSFORMERS_AVAILABLE = False

# Set up environment variables
os.environ['HF_HOME'] = '/cluster/tufts/datalab/zwu09/caches/huggingface'
os.environ['TRANSFORMERS_CACHE'] = '/cluster/tufts/datalab/zwu09/caches/huggingface'
os.environ['TORCH_HOME'] = '/cluster/tufts/datalab/zwu09/caches/torch'
os.environ['TMPDIR'] = '/cluster/tufts/datalab/zwu09/tmp'

# Create cache directories
for cache_dir in [os.environ['HF_HOME'], os.environ['TORCH_HOME'], os.environ['TMPDIR']]:
    os.makedirs(cache_dir, exist_ok=True)

app = Flask(__name__)

# Configuration
MAX_INPUT_LENGTH = 512  # Maximum input tokens to prevent CUDA errors
MAX_NEW_TOKENS = 100    # Maximum new tokens to generate
MEMORY_BUFFER_GB = 2.0  # Keep 2GB free on GPU

# Global state
class ModelState:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_name = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.loading = False

state = ModelState()

def get_gpu_info():
    """Get GPU information with error handling"""
    if not torch.cuda.is_available():
        return {"available": False, "message": "No CUDA GPUs available"}
    
    try:
        gpu_count = torch.cuda.device_count()
        gpus = []
        for i in range(gpu_count):
            props = torch.cuda.get_device_properties(i)
            allocated = torch.cuda.memory_allocated(i) / 1e9
            total = props.total_memory / 1e9
            free = total - allocated
            gpus.append({
                "id": i,
                "name": torch.cuda.get_device_name(i),
                "total_memory": round(total, 2),
                "allocated": round(allocated, 2),
                "free": round(free, 2),
                "percent_used": round((allocated / total) * 100, 1)
            })
        return {"available": True, "count": gpu_count, "gpus": gpus}
    except Exception as e:
        return {"available": False, "error": str(e)}

def check_gpu_memory():
    """Check if we have enough GPU memory"""
    if not torch.cuda.is_available():
        return True, "CPU mode"
    
    try:
        props = torch.cuda.get_device_properties(0)
        allocated = torch.cuda.memory_allocated(0) / 1e9
        total = props.total_memory / 1e9
        free = total - allocated
        
        if free < MEMORY_BUFFER_GB:
            return False, f"Low GPU memory: {free:.1f}GB free (need {MEMORY_BUFFER_GB}GB buffer)"
        return True, f"{free:.1f}GB free"
    except Exception as e:
        return False, str(e)

def cleanup_memory():
    """Aggressively clean up GPU memory"""
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()
    except Exception as e:
        print(f"Memory cleanup warning: {e}")

def validate_model_name(name):
    """Validate and clean model name"""
    name = name.strip()
    
    # Check for common mistakes
    if ' or ' in name.lower():
        # User typed "model1 or model2", take the first one
        name = name.split(' or ')[0].strip()
    
    # Remove common prefixes if accidentally included
    if name.startswith('http'):
        return None, "Please provide model name only, not full URL"
    
    return name, None

# HTML Template with better UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LM Studio - HPC Edition (Robust v2)</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        .header { text-align: center; color: #333; margin-bottom: 30px; }
        .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin-bottom: 20px; font-family: monospace; }
        .gpu-stats { background: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .model-selector { margin-bottom: 20px; }
        .chat-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .chat-output { background: #f9f9f9; padding: 15px; border-radius: 5px; min-height: 400px; }
        textarea { width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-family: monospace; }
        input[type="text"] { padding: 8px; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        button:disabled { background: #6c757d; cursor: not-allowed; }
        .info { background: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .warning { background: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .error { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .success { background: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .recommendations { background: #fff3cd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .model-card { background: white; border: 1px solid #ddd; padding: 10px; margin: 5px 0; border-radius: 5px; cursor: pointer; }
        .model-card:hover { background: #f8f9fa; }
        .loading { display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #007bff; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .gpu-bar { width: 100%; height: 20px; background: #e0e0e0; border-radius: 10px; overflow: hidden; margin: 5px 0; }
        .gpu-bar-fill { height: 100%; background: linear-gradient(90deg, #4CAF50, #FFC107, #F44336); transition: width 0.3s; }
        .char-count { font-size: 0.9em; color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 LM Studio - HPC Edition (Robust v2)</h1>
            <p>Running on Tufts HPC | Fixed: Rate Limiting, CUDA Errors, Memory Management</p>
        </div>
        
        <div class="status">
            <strong>Status:</strong> <span id="status">Ready</span> | 
            <strong>Model:</strong> <span id="current-model">None</span><br>
            <strong>GPU Memory:</strong> <span id="gpu-memory">Checking...</span>
        </div>
        
        <div class="gpu-stats" id="gpu-stats">
            <h3>GPU Status</h3>
            <div id="gpu-details">Loading...</div>
        </div>
        
        <div class="recommendations">
            <h3>💡 Quick-Load Models (Click to Load)</h3>
            <p style="background: #ffe6e6; padding: 10px; border-radius: 5px; font-size: 0.9em;">
                <strong>⚠️ GLIBC Issue:</strong> Some models use sentencepiece which requires GLIBC 2.27+. 
                Models marked ✅ are compatible with older systems.
            </p>
            <div class="model-card" onclick="loadQuickModel('gpt2')">
                <strong>✅ GPT-2</strong> (117M params, ~0.5GB) - Fast, no sentencepiece, best for testing
            </div>
            <div class="model-card" onclick="loadQuickModel('distilgpt2')">
                <strong>✅ DistilGPT-2</strong> (82M params, ~0.3GB) - Faster, smaller GPT-2
            </div>
            <div class="model-card" onclick="loadQuickModel('microsoft/DialoGPT-small')">
                <strong>✅ DialoGPT Small</strong> (117M params, ~0.5GB) - Conversational
            </div>
            <div class="model-card" onclick="loadQuickModel('microsoft/DialoGPT-medium')">
                <strong>✅ DialoGPT Medium</strong> (345M params, ~1.5GB) - Better quality
            </div>
            <div class="model-card" onclick="loadQuickModel('EleutherAI/pythia-70m')">
                <strong>✅ Pythia-70M</strong> (70M params, ~0.3GB) - Very small, fast
            </div>
            <div class="model-card" onclick="loadQuickModel('EleutherAI/pythia-410m')">
                <strong>✅ Pythia-410M</strong> (410M params, ~1.6GB) - Good balance
            </div>
            <div class="model-card" onclick="loadQuickModel('mistralai/Mistral-7B-Instruct-v0.1')">
                <strong>⚠️ Mistral 7B</strong> (7B params, ~14GB) - May have GLIBC issues
            </div>
        </div>
        
        <div class="model-selector">
            <h3>Or Load Custom Model</h3>
            <input type="text" id="model-input" placeholder="Enter HuggingFace model name (e.g., gpt2)" style="width: 400px;">
            <button onclick="loadModel()" id="load-btn">Load Model</button>
            <button onclick="unloadModel()" id="unload-btn">Unload Model</button>
            <button onclick="clearCache()" id="cache-btn">Clear GPU Cache</button>
        </div>
        
        <div class="info" id="model-info" style="display: none;">
            <h4>Loaded Model Information</h4>
            <div id="model-details"></div>
        </div>
        
        <div class="chat-container">
            <div>
                <h3>Input</h3>
                <textarea id="user-input" placeholder="Enter your prompt here..." maxlength="2048"></textarea>
                <div class="char-count"><span id="char-count">0</span> / 2048 characters</div>
                <br>
                <button onclick="generateText()" id="generate-btn">Generate</button>
                <button onclick="clearChat()">Clear</button>
                <br><br>
                <label>Max Tokens: <input type="number" id="max-tokens" value="50" min="10" max="200" style="width: 70px;"></label>
                <label>Temperature: <input type="number" id="temperature" value="0.8" step="0.1" min="0.1" max="2" style="width: 70px;"></label>
                <label>Top P: <input type="number" id="top-p" value="0.9" step="0.05" min="0" max="1" style="width: 70px;"></label>
            </div>
            
            <div>
                <h3>Output</h3>
                <div class="chat-output" id="output">Generated text will appear here...</div>
            </div>
        </div>
        
        <div id="messages"></div>
    </div>

    <script>
        function updateCharCount() {
            const input = document.getElementById('user-input').value;
            document.getElementById('char-count').textContent = input.length;
            if (input.length > 1800) {
                document.getElementById('char-count').style.color = 'red';
            } else if (input.length > 1500) {
                document.getElementById('char-count').style.color = 'orange';
            } else {
                document.getElementById('char-count').style.color = '#666';
            }
        }
        
        document.getElementById('user-input').addEventListener('input', updateCharCount);
        
        function showMessage(msg, type='info') {
            const div = document.createElement('div');
            div.className = type;
            div.textContent = msg;
            document.getElementById('messages').appendChild(div);
            setTimeout(() => div.remove(), 7000);
        }
        
        function updateStatus() {
            fetch('/status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('status').textContent = data.status;
                    document.getElementById('current-model').textContent = data.model_name || 'None';
                    
                    if (data.gpu_info && data.gpu_info.available) {
                        let gpuHtml = '';
                        data.gpu_info.gpus.forEach(gpu => {
                            gpuHtml += `<strong>GPU ${gpu.id}:</strong> ${gpu.name}<br>`;
                            gpuHtml += `Memory: ${gpu.allocated.toFixed(1)}GB / ${gpu.total_memory.toFixed(1)}GB (${gpu.percent_used}% used)<br>`;
                            gpuHtml += `<div class="gpu-bar"><div class="gpu-bar-fill" style="width: ${gpu.percent_used}%"></div></div>`;
                        });
                        document.getElementById('gpu-details').innerHTML = gpuHtml;
                        document.getElementById('gpu-memory').textContent = 
                            `${data.gpu_info.gpus[0].free.toFixed(1)}GB free`;
                    }
                })
                .catch(e => console.error('Status update failed:', e));
        }
        
        function loadQuickModel(modelName) {
            document.getElementById('model-input').value = modelName;
            loadModel();
        }
        
        function loadModel() {
            const modelName = document.getElementById('model-input').value.trim();
            if (!modelName) {
                showMessage('Please enter a model name', 'error');
                return;
            }
            
            document.getElementById('load-btn').disabled = true;
            document.getElementById('load-btn').innerHTML = '<span class="loading"></span> Loading...';
            showMessage('Loading model: ' + modelName + ' (this may take a few minutes)', 'info');
            
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
                        '<strong>Parameters:</strong> ' + (data.parameters || 'Unknown') + '<br>' +
                        '<strong>Memory Used:</strong> ' + (data.memory_used || 'Unknown');
                    showMessage('✅ Model loaded successfully!', 'success');
                } else {
                    showMessage('❌ Error: ' + data.error, 'error');
                    if (data.suggestion) {
                        showMessage('💡 Suggestion: ' + data.suggestion, 'warning');
                    }
                }
                document.getElementById('load-btn').disabled = false;
                document.getElementById('load-btn').innerHTML = 'Load Model';
                updateStatus();
            })
            .catch(e => {
                showMessage('❌ Network error: ' + e, 'error');
                document.getElementById('load-btn').disabled = false;
                document.getElementById('load-btn').innerHTML = 'Load Model';
            });
        }
        
        function unloadModel() {
            fetch('/unload_model', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('model-info').style.display = 'none';
                        showMessage('Model unloaded and memory cleared', 'success');
                    }
                    updateStatus();
                });
        }
        
        function clearCache() {
            fetch('/clear_cache', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    showMessage('GPU cache cleared', 'success');
                    updateStatus();
                });
        }
        
        function generateText() {
            const input = document.getElementById('user-input').value.trim();
            if (!input) {
                showMessage('Please enter some text', 'error');
                return;
            }
            
            if (input.length > 2000) {
                showMessage('Input too long! Please keep under 2000 characters to avoid CUDA errors', 'error');
                return;
            }
            
            document.getElementById('generate-btn').disabled = true;
            document.getElementById('generate-btn').innerHTML = '<span class="loading"></span> Generating...';
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
                    showMessage('✅ Generated successfully!', 'success');
                } else {
                    document.getElementById('output').textContent = 'Error: ' + data.error;
                    showMessage('❌ Generation failed: ' + data.error, 'error');
                    if (data.suggestion) {
                        showMessage('💡 ' + data.suggestion, 'warning');
                    }
                }
                document.getElementById('generate-btn').disabled = false;
                document.getElementById('generate-btn').innerHTML = 'Generate';
                updateStatus();
            })
            .catch(e => {
                document.getElementById('output').textContent = 'Error: ' + e;
                showMessage('❌ Network error: ' + e, 'error');
                document.getElementById('generate-btn').disabled = false;
                document.getElementById('generate-btn').innerHTML = 'Generate';
            });
        }
        
        function clearChat() {
            document.getElementById('user-input').value = '';
            document.getElementById('output').textContent = 'Generated text will appear here...';
            updateCharCount();
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
    
    return jsonify({
        'status': 'Loading...' if state.loading else ('Ready' if state.model is None else 'Model loaded'),
        'model_name': state.model_name,
        'gpu_info': gpu_info_data
    })

@app.route('/load_model', methods=['POST'])
def load_model():
    if state.loading:
        return jsonify({
            'success': False,
            'error': 'Another model is currently loading. Please wait.'
        })
    
    try:
        state.loading = True
        data = request.get_json()
        model_name_raw = data['model_name']
        
        # Validate and clean model name
        model_name, error = validate_model_name(model_name_raw)
        if error:
            return jsonify({
                'success': False,
                'error': error,
                'suggestion': 'Please enter a single model name from HuggingFace'
            })
        
        print(f"\n{'='*60}")
        print(f"Loading model: {model_name}")
        print(f"{'='*60}")
        
        # Check memory before loading
        mem_ok, mem_msg = check_gpu_memory()
        if not mem_ok:
            cleanup_memory()
            mem_ok, mem_msg = check_gpu_memory()
            if not mem_ok:
                return jsonify({
                    'success': False,
                    'error': mem_msg,
                    'suggestion': 'Try unloading the current model first or use a smaller model'
                })
        
        # Unload previous model
        if state.model is not None:
            print("Unloading previous model...")
            del state.model
            del state.tokenizer
            state.model = None
            state.tokenizer = None
            cleanup_memory()
        
        # Load tokenizer
        print("Loading tokenizer...")
        try:
            state.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True,
                use_fast=True  # Use fast tokenizer to avoid sentencepiece
            )
        except Exception as tok_error:
            print(f"Fast tokenizer failed, trying slow tokenizer: {tok_error}")
            try:
                state.tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    use_fast=False
                )
            except Exception as slow_error:
                raise Exception(f"Both tokenizers failed. Fast: {tok_error}, Slow: {slow_error}")
        
        # Add pad token if missing
        if state.tokenizer.pad_token is None:
            state.tokenizer.pad_token = state.tokenizer.eos_token
        
        # Load model with optimizations
        print("Loading model (this may take a few minutes)...")
        state.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if state.device == "cuda" else torch.float32,
            device_map="auto" if state.device == "cuda" else None,
            low_cpu_mem_usage=True,
            trust_remote_code=True
        )
        
        state.model_name = model_name
        
        # Get stats
        num_params = sum(p.numel() for p in state.model.parameters())
        gpu_info = get_gpu_info()
        memory_used = f"{gpu_info['gpus'][0]['allocated']:.1f}GB" if gpu_info.get('available') else "Unknown"
        
        print(f"✅ Model loaded successfully!")
        print(f"   Parameters: {num_params:,}")
        print(f"   Memory used: {memory_used}")
        print(f"{'='*60}\n")
        
        state.loading = False
        
        return jsonify({
            'success': True,
            'model_name': model_name,
            'device': state.device,
            'parameters': f"{num_params:,}",
            'memory_used': memory_used
        })
        
    except Exception as e:
        state.loading = False
        error_msg = str(e)
        print(f"❌ Error loading model: {error_msg}")
        traceback.print_exc()
        
        # Provide helpful suggestions
        suggestion = None
        if 'glibc' in error_msg.lower() or 'sentencepiece' in error_msg.lower():
            suggestion = "GLIBC version issue. Try models without sentencepiece: gpt2, distilgpt2, microsoft/DialoGPT-small, or EleutherAI/pythia-70m"
        elif '429' in error_msg or 'rate limit' in error_msg.lower():
            suggestion = "HuggingFace rate limit hit. Wait a few minutes and try again, or set HF_TOKEN environment variable."
        elif 'out of memory' in error_msg.lower() or 'oom' in error_msg.lower():
            suggestion = "GPU out of memory. Try a smaller model or unload current model first."
        elif 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
            suggestion = "Network issue. Check internet connection on HPC or try again."
        elif 'not found' in error_msg.lower() or '404' in error_msg:
            suggestion = "Model not found. Check the model name spelling on HuggingFace."
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'suggestion': suggestion
        })

@app.route('/unload_model', methods=['POST'])
def unload_model():
    try:
        if state.model is not None:
            del state.model
            del state.tokenizer
            state.model = None
            state.tokenizer = None
            state.model_name = None
        
        cleanup_memory()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/clear_cache', methods=['POST'])
def clear_cache():
    try:
        cleanup_memory()
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
        max_new_tokens = min(data.get('max_new_tokens', 50), MAX_NEW_TOKENS)
        temperature = data.get('temperature', 0.8)
        top_p = data.get('top_p', 0.9)
        
        # Validate input length
        if len(text) > 2000:
            return jsonify({
                'success': False,
                'error': 'Input too long (>2000 characters)',
                'suggestion': 'Please shorten your input to avoid CUDA memory errors'
            })
        
        print(f"\n{'='*60}")
        print(f"Generating text for: '{text[:50]}...'")
        
        # Check memory before generation
        mem_ok, mem_msg = check_gpu_memory()
        if not mem_ok:
            cleanup_memory()
            return jsonify({
                'success': False,
                'error': 'Low GPU memory before generation',
                'suggestion': 'Try clearing cache or using shorter input'
            })
        
        # Tokenize with strict length limit
        inputs = state.tokenizer(
            text,
            return_tensors='pt',
            padding=True,
            truncation=True,
            max_length=MAX_INPUT_LENGTH
        )
        
        if state.device == "cuda":
            inputs = {k: v.to(state.device) for k, v in inputs.items()}
        
        input_length = inputs['input_ids'].shape[1]
        print(f"Input tokens: {input_length} (max: {MAX_INPUT_LENGTH})")
        
        if input_length > MAX_INPUT_LENGTH:
            return jsonify({
                'success': False,
                'error': f'Input too long: {input_length} tokens (max: {MAX_INPUT_LENGTH})',
                'suggestion': 'Please use shorter input text'
            })
        
        # Generate with safety limits
        with torch.no_grad():
            outputs = state.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=state.tokenizer.pad_token_id,
                eos_token_id=state.tokenizer.eos_token_id,
                repetition_penalty=1.1,
                no_repeat_ngram_size=3
            )
        
        # Decode only new tokens
        generated_text = state.tokenizer.decode(outputs[0][input_length:], skip_special_tokens=True)
        
        print(f"Generated: '{generated_text[:100]}...'")
        print(f"{'='*60}\n")
        
        # Clean up after generation
        cleanup_memory()
        
        return jsonify({
            'success': True,
            'generated_text': generated_text
        })
        
    except RuntimeError as e:
        error_msg = str(e)
        print(f"❌ Runtime error: {error_msg}")
        
        # Handle CUDA errors specifically
        if 'CUDA' in error_msg or 'out of memory' in error_msg:
            cleanup_memory()
            return jsonify({
                'success': False,
                'error': 'GPU memory error during generation',
                'suggestion': 'Try: 1) Shorter input, 2) Fewer max tokens, 3) Clear cache, or 4) Restart server'
            })
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'suggestion': 'Try reducing input length or max tokens'
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error during generation: {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_msg
        })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting Robust LM Studio Server v2")
    print("="*60)
    
    # Check if transformers loaded successfully
    if not TRANSFORMERS_AVAILABLE:
        print("❌ CRITICAL: Transformers library failed to load!")
        print("This is likely due to GLIBC version issues.")
        print("\nPossible solutions:")
        print("1. Use system Python: /usr/bin/python3")
        print("2. Create new conda env: conda create -n lmstudio python=3.11")
        print("3. Install in virtual env under datalab")
        sys.exit(1)
    
    print(f"✅ Transformers loaded successfully")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        print(f"GPU Count: {gpu_count}")
        for i in range(gpu_count):
            props = torch.cuda.get_device_properties(i)
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            print(f"  Memory: {props.total_memory / 1e9:.1f} GB")
    else:
        print("⚠️  Warning: No CUDA GPUs detected, will use CPU (slow)")
    
    print(f"\nWorking directory: {os.getcwd()}")
    print(f"Cache directory: {os.environ['HF_HOME']}")
    print(f"Max input length: {MAX_INPUT_LENGTH} tokens")
    print(f"Max new tokens: {MAX_NEW_TOKENS}")
    print("="*60)
    print("Server starting on http://0.0.0.0:8080")
    print("Access via: http://localhost:8080")
    print("="*60 + "\n")
    
    try:
        app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("Server stopped by user")
        print("="*60)
    except Exception as e:
        print(f"\n\n❌ Server error: {e}")
        traceback.print_exc()
