#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robust LM Studio Server for HPC Environments
Handles long inputs, memory management, and error recovery professionally
"""

import os
import sys
import json
import traceback
import gc
import torch
from flask import Flask, request, jsonify, render_template_string
import threading
import time
import psutil
import logging

# Set up environment variables for datalab
os.environ['HF_HOME'] = '/cluster/tufts/datalab/zwu09/caches/huggingface'
os.environ['TRANSFORMERS_CACHE'] = '/cluster/tufts/datalab/zwu09/caches/huggingface'
os.environ['TORCH_HOME'] = '/cluster/tufts/datalab/zwu09/caches/torch'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variables for model management
current_model = None
current_tokenizer = None
model_name = None
device = "cuda" if torch.cuda.is_available() else "cpu"

# Configuration limits
MAX_INPUT_LENGTH = 2048  # Maximum input tokens
MAX_OUTPUT_LENGTH = 512  # Maximum output tokens
MAX_TOTAL_LENGTH = 2560  # Maximum total sequence length
MIN_FREE_GPU_MEMORY = 2.0  # Minimum free GPU memory in GB

def get_gpu_memory_info():
    """Get detailed GPU memory information"""
    if not torch.cuda.is_available():
        return {"total": 0, "allocated": 0, "free": 0, "percentage": 0}
    
    total = torch.cuda.get_device_properties(0).total_memory / 1e9
    allocated = torch.cuda.memory_allocated() / 1e9
    free = total - allocated
    percentage = (allocated / total) * 100
    
    return {
        "total": round(total, 2),
        "allocated": round(allocated, 2),
        "free": round(free, 2),
        "percentage": round(percentage, 2)
    }

def validate_input(text, max_length=MAX_INPUT_LENGTH):
    """Validate input text and return sanitized version"""
    if not text or not isinstance(text, str):
        raise ValueError("Input must be a non-empty string")
    
    # Remove excessive whitespace
    text = text.strip()
    if len(text) == 0:
        raise ValueError("Input cannot be empty after trimming")
    
    # Check if input is too long (rough estimate: 4 chars per token)
    estimated_tokens = len(text) // 4
    if estimated_tokens > max_length:
        raise ValueError(f"Input too long. Estimated {estimated_tokens} tokens, maximum {max_length} allowed")
    
    return text

def check_memory_constraints():
    """Check if we have enough memory for processing"""
    gpu_mem = get_gpu_memory_info()
    
    if gpu_mem["free"] < MIN_FREE_GPU_MEMORY:
        raise RuntimeError(f"Insufficient GPU memory. Free: {gpu_mem['free']}GB, Required: {MIN_FREE_GPU_MEMORY}GB")
    
    return gpu_mem

def safe_tokenize(tokenizer, text, max_length=MAX_INPUT_LENGTH):
    """Safely tokenize input with length checking"""
    try:
        # Tokenize with truncation if needed
        tokens = tokenizer.encode(text, return_tensors='pt', truncation=True, max_length=max_length)
        
        if tokens.shape[1] > max_length:
            logger.warning(f"Input truncated from {tokens.shape[1]} to {max_length} tokens")
            tokens = tokens[:, :max_length]
        
        return tokens
    except Exception as e:
        logger.error(f"Tokenization failed: {str(e)}")
        raise ValueError(f"Failed to tokenize input: {str(e)}")

def safe_generate(model, tokenizer, inputs, max_new_tokens=MAX_OUTPUT_LENGTH, temperature=0.7):
    """Safely generate text with memory management"""
    try:
        # Check memory before generation
        gpu_mem = check_memory_constraints()
        logger.info(f"Starting generation with {gpu_mem['free']}GB free GPU memory")
        
        # Generate with conservative settings
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                num_return_sequences=1,
                early_stopping=True,
                repetition_penalty=1.1,
                no_repeat_ngram_size=2
            )
        
        # Decode output
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Clean up memory
        del outputs
        torch.cuda.empty_cache()
        gc.collect()
        
        return generated_text
        
    except torch.cuda.OutOfMemoryError as e:
        logger.error(f"GPU out of memory during generation: {str(e)}")
        torch.cuda.empty_cache()
        gc.collect()
        raise RuntimeError(f"GPU out of memory. Try shorter input or smaller model. Error: {str(e)}")
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        raise RuntimeError(f"Generation failed: {str(e)}")

# Improved HTML template with better error handling
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LM Studio - HPC Edition (Robust)</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        .header { text-align: center; color: #333; margin-bottom: 30px; }
        .status { background: #e8f5e8; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        .error { background: #ffe6e6; padding: 10px; border-radius: 5px; margin-bottom: 20px; color: #d00; }
        .success { background: #e6ffe6; padding: 10px; border-radius: 5px; margin-bottom: 20px; color: #060; }
        .warning { background: #fff3cd; padding: 10px; border-radius: 5px; margin-bottom: 20px; color: #856404; }
        textarea { width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .memory-info { background: #f0f8ff; padding: 10px; border-radius: 5px; margin-bottom: 20px; font-family: monospace; font-size: 12px; }
        .input-limits { background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 LM Studio - HPC Edition (Robust)</h1>
            <p>Running on Tufts HPC with 2x H100 GPU acceleration</p>
        </div>
        
        <div class="status">
            <strong>Status:</strong> <span id="status">Ready</span> | 
            <strong>GPU:</strong> <span id="gpu-info">Checking...</span> | 
            <strong>Model:</strong> <span id="current-model">None loaded</span>
        </div>
        
        <div id="error-message" class="error" style="display: none;"></div>
        <div id="success-message" class="success" style="display: none;"></div>
        <div id="warning-message" class="warning" style="display: none;"></div>
        
        <div class="memory-info">
            <h4>System Information</h4>
            <div id="memory-info">Loading...</div>
        </div>
        
        <div class="input-limits">
            <h4>Input Limits</h4>
            <p><strong>Maximum Input Length:</strong> 2048 tokens (~8000 characters)</p>
            <p><strong>Maximum Output Length:</strong> 512 tokens (~2000 characters)</p>
            <p><strong>Note:</strong> Long inputs are automatically truncated to prevent crashes</p>
        </div>
        
        <div>
            <h3>Recommended Models (Start Small!)</h3>
            <button onclick="loadModel('gpt2')">GPT-2 (117M)</button>
            <button onclick="loadModel('microsoft/DialoGPT-small')">DialoGPT Small (117M)</button>
            <button onclick="loadModel('microsoft/DialoGPT-medium')">DialoGPT Medium (345M)</button>
            <br><br>
            <button onclick="loadModel('microsoft/DialoGPT-large')">DialoGPT Large (774M)</button>
            <button onclick="loadModel('mistralai/Mistral-7B-Instruct-v0.1')">Mistral 7B</button>
            <br><br>
            <input type="text" id="model-input" placeholder="Enter Hugging Face model name" style="width: 300px; padding: 8px;">
            <button onclick="loadCustomModel()">Load Custom Model</button>
            <button onclick="unloadModel()">Unload Model</button>
        </div>
        
        <div style="margin-top: 20px;">
            <h3>Input</h3>
            <textarea id="user-input" placeholder="Enter your prompt here (max 8000 characters)...">Hello, how are you?</textarea>
            <div id="char-count" style="text-align: right; font-size: 12px; color: #666;">0 / 8000 characters</div>
            <br><br>
            <button onclick="generateText()" id="generate-btn">Generate</button>
            <button onclick="clearChat()">Clear</button>
            <br><br>
            <label>Max Output Length: <input type="number" id="max-length" value="100" min="10" max="512" style="width: 80px;"></label>
            <label>Temperature: <input type="number" id="temperature" value="0.7" step="0.1" min="0" max="2" style="width: 80px;"></label>
        </div>
        
        <div style="margin-top: 20px;">
            <h3>Output</h3>
            <div id="output" style="background: #f9f9f9; padding: 15px; border-radius: 5px; min-height: 200px; white-space: pre-wrap; font-family: monospace;"></div>
        </div>
    </div>

    <script>
        function showError(message) {
            document.getElementById('error-message').textContent = message;
            document.getElementById('error-message').style.display = 'block';
            document.getElementById('success-message').style.display = 'none';
            document.getElementById('warning-message').style.display = 'none';
        }
        
        function showSuccess(message) {
            document.getElementById('success-message').textContent = message;
            document.getElementById('success-message').style.display = 'block';
            document.getElementById('error-message').style.display = 'none';
            document.getElementById('warning-message').style.display = 'none';
        }
        
        function showWarning(message) {
            document.getElementById('warning-message').textContent = message;
            document.getElementById('warning-message').style.display = 'block';
            document.getElementById('error-message').style.display = 'none';
            document.getElementById('success-message').style.display = 'none';
        }
        
        function hideMessages() {
            document.getElementById('error-message').style.display = 'none';
            document.getElementById('success-message').style.display = 'none';
            document.getElementById('warning-message').style.display = 'none';
        }
        
        function updateCharCount() {
            const input = document.getElementById('user-input').value;
            const count = input.length;
            const maxCount = 8000;
            const charCount = document.getElementById('char-count');
            
            charCount.textContent = `${count} / ${maxCount} characters`;
            
            if (count > maxCount * 0.9) {
                charCount.style.color = '#d00';
                showWarning(`Input is getting long (${count} characters). Consider shortening to avoid crashes.`);
            } else if (count > maxCount * 0.7) {
                charCount.style.color = '#f90';
            } else {
                charCount.style.color = '#666';
            }
        }
        
        function updateStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').textContent = data.status;
                    document.getElementById('gpu-info').textContent = data.gpu_info;
                    document.getElementById('current-model').textContent = data.model_name || 'None loaded';
                    document.getElementById('memory-info').innerHTML = `
                        <strong>GPU Memory:</strong> ${data.gpu_memory || 'Unknown'}<br>
                        <strong>Model Parameters:</strong> ${data.model_params || 'Unknown'}<br>
                        <strong>Last Error:</strong> ${data.last_error || 'None'}
                    `;
                })
                .catch(error => {
                    showError('Failed to get status: ' + error.message);
                });
        }
        
        function loadModel(modelName) {
            loadModelInternal(modelName);
        }
        
        function loadCustomModel() {
            const modelName = document.getElementById('model-input').value;
            if (!modelName) {
                showError('Please enter a model name');
                return;
            }
            loadModelInternal(modelName);
        }
        
        function loadModelInternal(modelName) {
            hideMessages();
            document.getElementById('status').textContent = 'Loading model...';
            document.getElementById('generate-btn').disabled = true;
            
            fetch('/load_model', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({model_name: modelName})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showSuccess('Model loaded successfully!');
                } else {
                    showError('Error loading model: ' + data.error);
                }
                document.getElementById('generate-btn').disabled = false;
                updateStatus();
            })
            .catch(error => {
                showError('Network error: ' + error.message);
                document.getElementById('generate-btn').disabled = false;
                updateStatus();
            });
        }
        
        function unloadModel() {
            hideMessages();
            fetch('/unload_model', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showSuccess('Model unloaded successfully!');
                    } else {
                        showError('Error unloading model: ' + data.error);
                    }
                    updateStatus();
                })
                .catch(error => {
                    showError('Network error: ' + error.message);
                    updateStatus();
                });
        }
        
        function generateText() {
            const input = document.getElementById('user-input').value;
            const maxLength = parseInt(document.getElementById('max-length').value);
            const temperature = parseFloat(document.getElementById('temperature').value);
            
            if (!input) {
                showError('Please enter some text');
                return;
            }
            
            if (input.length > 8000) {
                showError('Input too long! Maximum 8000 characters allowed.');
                return;
            }
            
            hideMessages();
            document.getElementById('status').textContent = 'Generating...';
            document.getElementById('output').textContent = 'Generating response...';
            document.getElementById('generate-btn').disabled = true;
            
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
                    showSuccess('Generation completed!');
                } else {
                    document.getElementById('output').textContent = 'Error: ' + data.error;
                    showError('Generation failed: ' + data.error);
                }
                document.getElementById('generate-btn').disabled = false;
                updateStatus();
            })
            .catch(error => {
                document.getElementById('output').textContent = 'Network error: ' + error.message;
                showError('Network error: ' + error.message);
                document.getElementById('generate-btn').disabled = false;
                updateStatus();
            });
        }
        
        function clearChat() {
            document.getElementById('user-input').value = '';
            document.getElementById('output').textContent = '';
            hideMessages();
            updateCharCount();
        }
        
        // Add event listener for character count
        document.getElementById('user-input').addEventListener('input', updateCharCount);
        
        // Update status every 3 seconds
        setInterval(updateStatus, 3000);
        updateStatus();
        updateCharCount();
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
    gpu_memory = "Unknown"
    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        gpu_names = [torch.cuda.get_device_name(i) for i in range(gpu_count)]
        gpu_info = f"{gpu_count}x GPU: {', '.join(gpu_names)}"
        
        # Get detailed memory info
        mem_info = get_gpu_memory_info()
        gpu_memory = f"{mem_info['allocated']}GB / {mem_info['total']}GB ({mem_info['percentage']}%)"
    
    model_params = "Unknown"
    if current_model is not None:
        try:
            model_params = f"{sum(p.numel() for p in current_model.parameters()):,}"
        except:
            model_params = "Error counting parameters"
    
    return jsonify({
        'status': 'Ready' if current_model is None else 'Model loaded',
        'gpu_info': gpu_info,
        'gpu_memory': gpu_memory,
        'model_name': model_name,
        'model_params': model_params,
        'last_error': getattr(app, 'last_error', None)
    })

@app.route('/load_model', methods=['POST'])
def load_model():
    global current_model, current_tokenizer, model_name
    
    try:
        data = request.get_json()
        model_name = data['model_name']
        
        logger.info(f"Loading model: {model_name}")
        
        # Check memory before loading
        gpu_mem = get_gpu_memory_info()
        logger.info(f"GPU memory before loading: {gpu_mem}")
        
        # Unload previous model to free memory
        if current_model is not None:
            logger.info("Unloading previous model...")
            del current_model
            del current_tokenizer
            torch.cuda.empty_cache()
            gc.collect()
        
        # Import here to avoid issues
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        logger.info("Loading tokenizer...")
        current_tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Add padding token if it doesn't exist
        if current_tokenizer.pad_token is None:
            current_tokenizer.pad_token = current_tokenizer.eos_token
        
        logger.info("Loading model...")
        current_model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            low_cpu_mem_usage=True
        )
        
        logger.info(f"Model loaded successfully: {model_name}")
        app.last_error = None
        
        return jsonify({'success': True})
        
    except Exception as e:
        error_msg = f"Error loading model: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        app.last_error = error_msg
        
        # Clean up on error
        if current_model is not None:
            del current_model
            del current_tokenizer
            torch.cuda.empty_cache()
            gc.collect()
        
        current_model = None
        current_tokenizer = None
        model_name = None
        
        return jsonify({'success': False, 'error': error_msg})

@app.route('/unload_model', methods=['POST'])
def unload_model():
    global current_model, current_tokenizer, model_name
    
    try:
        if current_model is not None:
            logger.info("Unloading model...")
            del current_model
            del current_tokenizer
            torch.cuda.empty_cache()
            gc.collect()
        
        current_model = None
        current_tokenizer = None
        model_name = None
        app.last_error = None
        
        return jsonify({'success': True})
        
    except Exception as e:
        error_msg = f"Error unloading model: {str(e)}"
        logger.error(error_msg)
        app.last_error = error_msg
        return jsonify({'success': False, 'error': error_msg})

@app.route('/generate', methods=['POST'])
def generate():
    try:
        if current_model is None or current_tokenizer is None:
            return jsonify({'success': False, 'error': 'No model loaded'})
        
        data = request.get_json()
        text = data['text']
        max_length = data.get('max_length', 100)
        temperature = data.get('temperature', 0.7)
        
        # Validate input
        try:
            text = validate_input(text, MAX_INPUT_LENGTH)
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)})
        
        # Check memory constraints
        try:
            gpu_mem = check_memory_constraints()
        except RuntimeError as e:
            return jsonify({'success': False, 'error': str(e)})
        
        logger.info(f"Generating text for: '{text[:50]}...' (length: {len(text)})")
        
        # Safely tokenize input
        try:
            inputs = safe_tokenize(current_tokenizer, text, MAX_INPUT_LENGTH)
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)})
        
        if device == "cuda":
            inputs = inputs.to(device)
        
        logger.info(f"Input tokens: {inputs.shape[1]}")
        
        # Safely generate text
        try:
            generated_text = safe_generate(
                current_model, 
                current_tokenizer, 
                inputs, 
                max_length, 
                temperature
            )
            
            # Remove input from output
            if generated_text.startswith(text):
                generated_text = generated_text[len(text):].strip()
            
            logger.info(f"Generated text: '{generated_text[:100]}...'")
            app.last_error = None
            
            return jsonify({'success': True, 'generated_text': generated_text})
            
        except RuntimeError as e:
            error_msg = str(e)
            logger.error(error_msg)
            app.last_error = error_msg
            return jsonify({'success': False, 'error': error_msg})
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        app.last_error = error_msg
        return jsonify({'success': False, 'error': error_msg})

if __name__ == '__main__':
    print("Starting Robust LM Studio Server...")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU Count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            print(f"GPU {i} Memory: {torch.cuda.get_device_properties(i).total_memory / 1e9:.1f} GB")
    
    print(f"Input limits: {MAX_INPUT_LENGTH} tokens, {MAX_OUTPUT_LENGTH} output tokens")
    print(f"Minimum free GPU memory: {MIN_FREE_GPU_MEMORY}GB")
    
    app.run(host='0.0.0.0', port=8081, debug=False)
