# LM Studio Setup for HPC Systems

## 🎯 **Overview**
LM Studio is a desktop application for running Large Language Models (LLMs) locally. Since HPC systems typically don't have GUI support, we'll set up web-based alternatives.

## 🖥️ **HPC-Compatible Solutions**

### **Option 1: LM Studio Web Interface (Recommended)**
```bash
# SSH to HPC
ssh zwu09@login.pax.tufts.edu

# Get compute node with GPU
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash

# Download LM Studio web interface
wget https://github.com/lmstudio-ai/lms/releases/download/v0.2.20/lms-0.2.20-linux-x64.tar.gz
tar -xzf lms-0.2.20-linux-x64.tar.gz
cd lms-0.2.20-linux-x64

# Start LM Studio web interface
./lms server --host 0.0.0.0 --port 8080
```

### **Option 2: Ollama (Alternative)**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull a model
ollama pull llama2

# Run model
ollama run llama2
```

### **Option 3: Text Generation Inference (TGI)**
```bash
# Install TGI
pip install text-generation-inference

# Start TGI server
text-generation-launcher --model-id microsoft/DialoGPT-medium --port 8080
```

## 🚀 **Quick Setup Commands for HPC**

### **Step 1: Connect to HPC**
```bash
ssh zwu09@login.pax.tufts.edu
```

### **Step 2: Get Compute Node**
```bash
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash
```

### **Step 3: Set up LM Studio**
```bash
# Create workspace
mkdir -p /cluster/tufts/datalab/zwu09/lmstudio
cd /cluster/tufts/datalab/zwu09/lmstudio

# Download LM Studio
wget https://github.com/lmstudio-ai/lms/releases/download/v0.2.20/lms-0.2.20-linux-x64.tar.gz
tar -xzf lms-0.2.20-linux-x64.tar.gz
cd lms-0.2.20-linux-x64

# Start web interface
./lms server --host 0.0.0.0 --port 8080
```

### **Step 4: Access from Browser**
- Open browser and go to: `http://localhost:8080`
- Or tunnel: `ssh -J zwu09@login.pax.tufts.edu -L 8080:127.0.0.1:8080 zwu09@NODE`

## 📋 **What You Get**

1. **Web-based LM Studio interface**
2. **Model download and management**
3. **Chat interface with AI models**
4. **API access for integration**
5. **GPU acceleration support**

## 🔧 **Alternative: Use Ollama**

If LM Studio doesn't work, use Ollama:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start service
ollama serve &

# Pull models
ollama pull llama2
ollama pull codellama
ollama pull mistral

# Run models
ollama run llama2
```

## 📞 **Support**

If you encounter issues:
1. Check GPU availability: `nvidia-smi`
2. Check memory usage: `free -h`
3. Check disk space: `df -h /cluster/tufts/datalab`
4. Use tunnel for web access: `ssh -L 8080:127.0.0.1:8080`

## 🎯 **Recommended Models for HPC**

- **Llama 2 7B** - Good balance of performance and resource usage (~14GB)
- **Code Llama** - For code generation (~14GB)
- **Mistral 7B** - High performance (~14GB)
- **Phi-3** - Microsoft's efficient model (~28GB)

## ⚠️ **Critical Issues & Solutions**

### **Python Version Problem**
- **Issue**: Default Python 3.6.8 too old for modern ML libraries
- **Solution**: Use Python 3.11 from anaconda:
  ```bash
  /cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11 -m venv $DATALAB_BASE/envs/py311
  source $DATALAB_BASE/envs/py311/bin/activate
  ```

### **Storage Management**
- **Issue**: Clean setup scripts may accumulate junk, limiting space for large LLMs
- **Solution**: Monitor storage with `df -h /cluster/tufts/datalab/zwu09`
- **LLM Storage**: 7B+ models need 10-50GB each. Clean unused environments regularly.

Remember: Always work in `/cluster/tufts/datalab/zwu09` to avoid HOME directory issues!





