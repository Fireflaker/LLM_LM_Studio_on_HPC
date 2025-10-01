#!/usr/bin/env python3
"""
LM Studio-like server for HPC environments
Provides a web interface for running language models on GPU
"""

import os
import sys
import json
import torch
from flask import Flask, request, jsonify, render_template_string
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import threading
import time

# Set up environment variables for datalab
os.environ['HF_HOME'] = '/cluster/tufts/datalab/zwu09/caches/huggingface'
os.environ['TRANSFORMERS_CACHE'] = '/cluster/tufts/datalab/zwu09/caches/huggingface'
os.environ['TORCH_HOME'] = '/cluster/tufts/datalab/zwu09/caches/torch'

app = Flask(__name__)

# Global variables for model management
current_model = None
current_tokenizer = None
model_name = None
device = "cuda" if torch.cuda.is_available() else "cpu"

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LM Studio - HPC Edition</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #333; margin-bottom: 30px; }
        .status { background: #e8f5e8; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        .model-selector { margin-bottom: 20px; }
        .chat-container { display: flex; gap: 20px; }
        .chat-input { flex: 1; }
        .chat-output { flex: 1; background: #f9f9f9; padding: 15px; border-radius: 5px; min-height: 400px; }
        textarea { width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #0056b3; }
        .model-info { background: #f0f8ff; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 LM Studio - HPC Edition</h1>
            <p>Running on Tufts HPC with GPU acceleration</p>
        </div>
        
        <div class="status">
            <strong>Status:</strong> 
            <span id="status">Ready</span> | 
            <strong>GPU:</strong> <span id="gpu-info">Checking...</span> | 
            <strong>Model:</strong> <span id="current-model">None loaded</span>
        </div>
        
        <div class="model-selector">
            <h3>Load Model</h3>
            <input type="text" id="model-input" placeholder="Enter Hugging Face model name (e.g., microsoft/DialoGPT-medium)" style="width: 300px; padding: 8px;">
            <button onclick="loadModel()">Load Model</button>
            <button onclick="unloadModel()">Unload Model</button>
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
                <button onclick="generateText()">Generate</button>
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
    </div>

    <script>
        function updateStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').textContent = data.status;
                    document.getElementById('gpu-info').textContent = data.gpu_info;
                    document.getElementById('current-model').textContent = data.model_name || 'None loaded';
                });
        }
        
        function loadModel() {
            const modelName = document.getElementById('model-input').value;
            if (!modelName) {
                alert('Please enter a model name');
                return;
            }
            
            document.getElementById('status').textContent = 'Loading model...';
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
                        <strong>Status:</strong> ${data.status}
                    `;
                } else {
                    alert('Error loading model: ' + data.error);
                }
                updateStatus();
            });
        }
        
        function unloadModel() {
            fetch('/unload_model', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    document.getElementById('model-info').style.display = 'none';
                    updateStatus();
                });
        }
        
        function generateText() {
            const input = document.getElementById('user-input').value;
            const maxLength = parseInt(document.getElementById('max-length').value);
            const temperature = parseFloat(document.getElementById('temperature').value);
            
            if (!input) {
                alert('Please enter some text');
                return;
            }
            
            document.getElementById('status').textContent = 'Generating...';
            document.getElementById('output').textContent = 'Generating response...';
            
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
                } else {
                    document.getElementById('output').textContent = 'Error: ' + data.error;
                }
                updateStatus();
            });
        }
        
        function clearChat() {
            document.getElementById('user-input').value = '';
            document.getElementById('output').textContent = '';
        }
        
        // Update status every 5 seconds
        setInterval(updateStatus, 5000);
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
    gpu_info = "Not available"
    if torch.cuda.is_available():
        gpu_info = f"GPU {torch.cuda.current_device()}: {torch.cuda.get_device_name()}"
    
    return jsonify({
        'status': 'Ready' if current_model is None else 'Model loaded',
        'gpu_info': gpu_info,
        'model_name': model_name
    })

@app.route('/load_model', methods=['POST'])
def load_model():
    global current_model, current_tokenizer, model_name
    
    try:
        data = request.get_json()
        model_name = data['model_name']
        
        # Unload previous model to free memory
        if current_model is not None:
            del current_model
            del current_tokenizer
            torch.cuda.empty_cache()
        
        print(f"Loading model: {model_name}")
        
        # Load tokenizer and model
        current_tokenizer = AutoTokenizer.from_pretrained(model_name)
        current_model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None
        )
        
        # Move to device if not using device_map
        if device == "cuda" and not hasattr(current_model, 'hf_device_map'):
            current_model = current_model.to(device)
        
        # Get model info
        num_params = sum(p.numel() for p in current_model.parameters())
        
        return jsonify({
            'success': True,
            'model_name': model_name,
            'device': device,
            'parameters': f"{num_params:,}",
            'status': 'Loaded successfully'
        })
        
    except Exception as e:
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
        
        current_model = None
        current_tokenizer = None
        model_name = None
        
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
                pad_token_id=current_tokenizer.eos_token_id
            )
        
        # Decode output
        generated_text = current_tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove input from output
        if generated_text.startswith(text):
            generated_text = generated_text[len(text):].strip()
        
        return jsonify({
            'success': True,
            'generated_text': generated_text
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("Starting LM Studio Server...")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name()}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    app.run(host='0.0.0.0', port=8080, debug=False)


