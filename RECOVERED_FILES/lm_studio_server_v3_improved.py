#!/usr/bin/env python3
"""
LM Studio Server v3 - Improved for HPC
- Handles GLIBC issues gracefully
- Fallback to demo mode if transformers fails
- Better error handling and user guidance
- Compatible with HPC environment
"""

import os
import sys
import json
import warnings
import traceback

# Suppress warnings
warnings.filterwarnings('ignore', category=UserWarning, module='torch')
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning'
os.environ['NUMPY_EXPERIMENTAL_ARRAY_FUNCTION'] = '0'

import torch
import gc
import psutil
from flask import Flask, request, jsonify, render_template_string
import time

# Try to import transformers with comprehensive error handling
TRANSFORMERS_AVAILABLE = False
TRANSFORMERS_ERROR = None

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
    print("✅ Transformers imported successfully")
except Exception as e:
    TRANSFORMERS_ERROR = str(e)
    print(f"⚠️  Transformers import failed: {e}")
    print("   Server will run in demo mode")

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
MAX_INPUT_LENGTH = 2048
MAX_NEW_TOKENS = 512
MEMORY_BUFFER_GB = 2.0

# Best ungated models for H100
RECOMMENDED_MODELS = {
    'small': ['gpt2', 'distilgpt2'],
    'medium_7b': ['Qwen/Qwen2.5-7B-Instruct', 'Qwen/Qwen2.5-Coder-7B-Instruct', 'mistralai/Mistral-7B-Instruct-v0.3', 'deepseek-ai/deepseek-coder-6.7b-instruct'],
    'large_14b': ['microsoft/Phi-3-medium-4k-instruct', 'Qwen/Qwen2.5-14B-Instruct'],
    'xlarge_32b': ['Qwen/Qwen2.5-32B-Instruct']
}

# Global state
class ModelState:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_name = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.loading = False
        self.demo_mode = not TRANSFORMERS_AVAILABLE

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
    
    if ' or ' in name.lower():
        name = name.split(' or ')[0].strip()
    
    if name.startswith('http'):
        return None, "Please provide model name only, not full URL"
    
    return name, None

# Enhanced HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LM Studio - HPC Edition v3</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #333; margin-bottom: 30px; }
        .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin-bottom: 20px; font-family: monospace; }
        .gpu-stats { background: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .demo-warning { background: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid #ffc107; }
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
        .troubleshooting { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 LM Studio - HPC Edition v3</h1>
            <p>Running on Tufts HPC | Enhanced Error Handling & Demo Mode</p>
        </div>
        
        <div id="demo-warning" class="demo-warning" style="display: none;">
            <h3>⚠️ Demo Mode Active</h3>
            <p><strong>Transformers library failed to load.</strong> This is likely due to GLIBC compatibility issues.</p>
            <p><strong>What works:</strong> Interface, GPU detection, model selection</p>
            <p><strong>What doesn't work:</strong> Actual model loading and text generation</p>
            <p><strong>Solutions:</strong> Try the troubleshooting steps below or use the simple server version.</p>
        </div>
        
        <div class="status">
            <strong>Status:</strong> <span id="status">Ready</span> | 
            <strong>Mode:</strong> <span id="mode">Checking...</span> |
            <strong>Model:</strong> <span id="current-model">None</span><br>
            <strong>GPU Memory:</strong> <span id="gpu-memory">Checking...</span>
        </div>
        
        <div class="gpu-stats" id="gpu-stats">
            <h3>GPU Status</h3>
            <div id="gpu-details">Loading...</div>
        </div>
        
        <div class="recommendations">
            <h3>💡 Recommended Models for H100 (Click to Load)</h3>
            
            <div style="margin-bottom: 15px;">
                <h4 style="color: #ff6b6b; margin: 10px 0;">🔥 LARGE Models (32B - Best Quality)</h4>
                <div class="model-card" onclick="loadQuickModel('Qwen/Qwen2.5-Coder-32B-Instruct')">
                    <strong>🚀🚀 Qwen2.5-Coder-32B-Instruct</strong> (32B, ~64GB) - BEST coding model, state-of-art
                </div>
                <div class="model-card" onclick="loadQuickModel('Qwen/Qwen2.5-32B-Instruct')">
                    <strong>🌟🌟 Qwen2.5-32B-Instruct</strong> (32B, ~64GB) - BEST chat model, multilingual
                </div>
                <div class="model-card" onclick="loadQuickModel('deepseek-ai/deepseek-coder-33b-instruct')">
                    <strong>💻💻 DeepSeek-Coder-33B-Instruct</strong> (33B, ~66GB) - Advanced code understanding
                </div>
            </div>
            
            <div style="margin-bottom: 15px;">
                <h4 style="color: #28a745; margin: 10px 0;">⭐ MEDIUM Models (7B-14B - Fast & Good)</h4>
                <div class="model-card" onclick="loadQuickModel('Qwen/Qwen2.5-Coder-7B-Instruct')">
                    <strong>🚀 Qwen2.5-Coder-7B-Instruct</strong> (7B, ~14GB) - ✅ TESTED & WORKING
                </div>
                <div class="model-card" onclick="loadQuickModel('Qwen/Qwen2.5-14B-Instruct')">
                    <strong>🌟 Qwen2.5-14B-Instruct</strong> (14B, ~28GB) - Better than 7B, faster than 32B
                </div>
                <div class="model-card" onclick="loadQuickModel('microsoft/Phi-3-medium-4k-instruct')">
                    <strong>🧠 Phi-3-Medium-4k-Instruct</strong> (14B, ~28GB) - Microsoft, excellent reasoning
                </div>
                <div class="model-card" onclick="loadQuickModel('mistralai/Mistral-7B-Instruct-v0.3')">
                    <strong>⚡ Mistral-7B-Instruct-v0.3</strong> (7B, ~14GB) - Fast and reliable
                </div>
            </div>
            
            <div style="margin-bottom: 15px;">
                <h4 style="color: #6c757d; margin: 10px 0;">🔬 SMALL Models (Testing)</h4>
                <div class="model-card" onclick="loadQuickModel('gpt2')">
                    <strong>✅ GPT-2</strong> (117M, ~0.5GB) - Fast testing
                </div>
            </div>
        </div>
        
        <div class="model-selector">
            <h3>Or Load Custom Model</h3>
            <input type="text" id="model-input" placeholder="Enter HuggingFace model name (e.g., Qwen/Qwen2.5-7B-Instruct)" style="width: 500px;">
            <br><br>
            <button onclick="loadModel(false)" id="load-btn">Load Model (Use Cache)</button>
            <button onclick="loadModel(true)" id="force-load-btn">🔄 Force Re-download</button>
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
        
        <div class="troubleshooting">
            <h3>🔧 Troubleshooting</h3>
            <p><strong>If you see GLIBC errors:</strong></p>
            <ul>
                <li>Try models without sentencepiece: <code>gpt2</code>, <code>distilgpt2</code></li>
                <li>Use the simple server: <code>python simple_lm_studio.py</code></li>
                <li>Check HPC notes for module loading issues</li>
            </ul>
            <p><strong>If models won't load:</strong></p>
            <ul>
                <li>Check internet connection on HPC</li>
                <li>Try smaller models first</li>
                <li>Clear GPU cache and try again</li>
            </ul>
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
                    document.getElementById('mode').textContent = data.mode;
                    document.getElementById('current-model').textContent = data.model_name || 'None';
                    
                    if (data.demo_mode) {
                        document.getElementById('demo-warning').style.display = 'block';
                    }
                    
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
        
        function loadModel(forceDownload = false) {
            const modelName = document.getElementById('model-input').value.trim();
            if (!modelName) {
                showMessage('Please enter a model name', 'error');
                return;
            }
            
            document.getElementById('load-btn').disabled = true;
            document.getElementById('force-load-btn').disabled = true;
            const btnText = forceDownload ? '🔄 Force Re-downloading...' : '<span class="loading"></span> Loading...';
            document.getElementById('load-btn').innerHTML = btnText;
            
            const msg = forceDownload ? 
                'Force re-downloading model: ' + modelName + ' (will re-download from HuggingFace)' :
                'Loading model: ' + modelName + ' (will use cache if available)';
            showMessage(msg, 'info');
            
            fetch('/load_model', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    model_name: modelName,
                    force_download: forceDownload
                })
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
                document.getElementById('force-load-btn').disabled = false;
                document.getElementById('load-btn').innerHTML = 'Load Model (Use Cache)';
                updateStatus();
            })
            .catch(e => {
                showMessage('❌ Network error: ' + e, 'error');
                document.getElementById('load-btn').disabled = false;
                document.getElementById('force-load-btn').disabled = false;
                document.getElementById('load-btn').innerHTML = 'Load Model (Use Cache)';
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
                showMessage('Input too long! Please keep under 2000 characters', 'error');
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
        'mode': 'Demo Mode' if state.demo_mode else 'Full Mode',
        'model_name': state.model_name,
        'demo_mode': state.demo_mode,
        'gpu_info': gpu_info_data
    })

@app.route('/load_model', methods=['POST'])
def load_model():
    if state.demo_mode:
        return jsonify({
            'success': False,
            'error': 'Demo mode active - transformers library not available',
            'suggestion': 'Try the simple server: python simple_lm_studio.py'
        })
    
    if state.loading:
        return jsonify({
            'success': False,
            'error': 'Another model is currently loading. Please wait.'
        })
    
    try:
        state.loading = True
        data = request.get_json()
        model_name_raw = data['model_name']
        force_download = data.get('force_download', False)
        
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
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / 1e9
            total = torch.cuda.get_device_properties(0).total_memory / 1e9
            free = total - allocated
            if free < MEMORY_BUFFER_GB:
                cleanup_memory()
                return jsonify({
                    'success': False,
                    'error': f'Low GPU memory: {free:.1f}GB free (need {MEMORY_BUFFER_GB}GB buffer)',
                    'suggestion': 'Try unloading current model or use a smaller model'
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
        hf_token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_TOKEN')
        
        # Check if model is cached
        cache_dir = os.environ.get('HF_HOME', '/cluster/tufts/datalab/zwu09/caches/huggingface')
        if not force_download and os.path.exists(cache_dir):
            print(f"✅ Using cache directory: {cache_dir}")
            print("   Model will be loaded from cache if available")
        elif force_download:
            print("🔄 Force download enabled - will re-download from HuggingFace")
        
        try:
            state.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True,
                use_fast=True,
                token=hf_token,
                force_download=force_download,
                resume_download=not force_download
            )
        except Exception as tok_error:
            print(f"Fast tokenizer failed, trying slow tokenizer: {tok_error}")
            try:
                state.tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    use_fast=False,
                    token=hf_token,
                    force_download=force_download,
                    resume_download=not force_download
                )
            except Exception as slow_error:
                raise Exception(f"Both tokenizers failed. Fast: {tok_error}, Slow: {slow_error}")
        
        # Add pad token if missing
        if state.tokenizer.pad_token is None:
            state.tokenizer.pad_token = state.tokenizer.eos_token
        
        # Load model with optimizations
        print("Loading model (this may take a few minutes)...")
        hf_token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_TOKEN')
        
        state.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if state.device == "cuda" else torch.float32,
            device_map="auto" if state.device == "cuda" else None,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
            token=hf_token,
            force_download=force_download,
            resume_download=not force_download
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
    if state.demo_mode:
        return jsonify({
            'success': False,
            'error': 'Demo mode active - text generation not available',
            'suggestion': 'Try the simple server: python simple_lm_studio.py'
        })
    
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
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated(0) / 1e9
            total = torch.cuda.get_device_properties(0).total_memory / 1e9
            free = total - allocated
            if free < 1.0:  # Need at least 1GB free
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
    print("🚀 Starting LM Studio Server v3 - Improved")
    print("="*60)
    
    # Check transformers availability
    if not TRANSFORMERS_AVAILABLE:
        print("⚠️  WARNING: Transformers library failed to load!")
        print(f"   Error: {TRANSFORMERS_ERROR}")
        print("   Server will run in demo mode")
        print("   For full functionality, try the simple server: python simple_lm_studio.py")
    else:
        print("✅ Transformers loaded successfully")
    
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
