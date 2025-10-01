#!/usr/bin/env python3
"""
Simple LM Studio Server for HPC
Minimal version without transformers dependency
"""

import torch
from flask import Flask, request, jsonify, render_template_string
import json

app = Flask(__name__)

# Simple HTML template
HTML_TEMPLATE = '''
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 LM Studio - HPC Edition</h1>
            <p>Running on Tufts HPC with GPU acceleration</p>
        </div>
        
        <div class="status">
            <strong>Status:</strong> Ready | 
            <strong>GPU:</strong> <span id="gpu-info">Checking...</span> | 
            <strong>Model:</strong> <span id="current-model">None loaded</span>
        </div>
        
        <div class="model-selector">
            <h3>Load Model</h3>
            <input type="text" id="model-input" placeholder="Enter Hugging Face model name (e.g., microsoft/DialoGPT-medium)" style="width: 300px; padding: 8px;">
            <button onclick="loadModel()">Load Model</button>
            <button onclick="unloadModel()">Unload Model</button>
        </div>
        
        <div class="chat-container">
            <div class="chat-input">
                <h3>Input</h3>
                <textarea id="user-input" placeholder="Enter your prompt here..."></textarea>
                <br><br>
                <button onclick="generateText()">Generate</button>
                <button onclick="clearChat()">Clear</button>
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
            
            document.getElementById('output').textContent = 'Loading model: ' + modelName + '...';
            fetch('/load_model', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({model_name: modelName})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('output').textContent = 'Model loaded successfully: ' + data.model_name + '\\n\\nNote: This is a demo version. Full model loading requires transformers library.';
                } else {
                    document.getElementById('output').textContent = 'Error: ' + data.error;
                }
                updateStatus();
            });
        }
        
        function unloadModel() {
            document.getElementById('output').textContent = 'Model unloaded';
            updateStatus();
        }
        
        function generateText() {
            const input = document.getElementById('user-input').value;
            if (!input) {
                alert('Please enter some text');
                return;
            }
            
            document.getElementById('output').textContent = 'Generating response for: "' + input + '"...\\n\\nNote: This is a demo version. Full text generation requires transformers library.';
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
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    gpu_info = "Not available"
    if torch.cuda.is_available():
        gpu_info = f"GPU {torch.cuda.current_device()}: {torch.cuda.get_device_name()}"
    
    return jsonify({
        'gpu_info': gpu_info,
        'model_name': None
    })

@app.route('/load_model', methods=['POST'])
def load_model():
    try:
        data = request.get_json()
        model_name = data['model_name']
        return jsonify({
            'success': True,
            'model_name': model_name,
            'status': 'Model loaded successfully (demo mode)'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print('Starting Simple LM Studio Server...')
    print(f'CUDA available: {torch.cuda.is_available()}')
    if torch.cuda.is_available():
        print(f'GPU: {torch.cuda.get_device_name()}')
        print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')
    
    print('Server starting on http://0.0.0.0:8080')
    app.run(host='0.0.0.0', port=8080, debug=False)
