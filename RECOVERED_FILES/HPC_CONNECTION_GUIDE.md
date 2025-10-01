# HPC LM Studio - Enhanced Connection Guide

## 🎯 **Quick Start (Enhanced Server)**

### **Step 1: Connect to HPC**
```bash
ssh zwu09@login.pax.tufts.edu
# Password: Leowzd832126
# Use Duo 2FA (option 1 for push)
```

### **Step 2: Request Optimal GPU Resources**

**For Small Models (GPT-2, DialoGPT):**
```bash
srun -p gpu --gres=gpu:h100:1 -c 20 --mem=50G -t 02:00:00 --pty bash
```

**For Medium Models (Mistral 7B, Llama 2 7B):**
```bash
srun -p gpu --gres=gpu:h100:1 -c 40 --mem=100G -t 03:00:00 --pty bash
```

**For Large Models (Llama 2 13B, CodeLlama 13B):**
```bash
srun -p gpu --gres=gpu:h100:1 -c 60 --mem=150G -t 04:00:00 --pty bash
```

**For Very Large Models (CodeLlama 34B, Llama 2 70B):**
```bash
srun -p gpu --gres=gpu:h100:2 -c 80 --mem=200G -t 06:00:00 --pty bash
```

### **Step 3: Set Up Environment**
```bash
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
cd $DATALAB_BASE

# Verify GPU access
nvidia-smi

# Check available resources
df -h /cluster/tufts/datalab
free -h
```

### **Step 4: Start Enhanced LM Studio Server**
```bash
cd /cluster/tufts/datalab/zwu09

# Install required packages if needed
/cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11 -m pip install flask psutil

# Start the enhanced server
/cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11 lm_studio_server_enhanced.py
```

### **Step 5: Create SSH Tunnel (from your local computer)**
```bash
# Get the compute node hostname first (from the HPC terminal)
echo "NODE=$(hostname)"

# Then create tunnel from your laptop (PowerShell)
& 'C:\Windows\System32\OpenSSH\ssh.exe' -J 'zwu09@login.pax.tufts.edu' -L 8080:127.0.0.1:8080 "zwu09@NODE_HOSTNAME"

# Or Git Bash/WSL
ssh -J zwu09@login.pax.tufts.edu -L 8080:127.0.0.1:8080 zwu09@NODE_HOSTNAME
```

### **Step 6: Access Enhanced Web Interface**
- Open browser to: `http://localhost:8080`
- You'll see the enhanced interface with:
  - Real-time system monitoring
  - GPU memory usage
  - Model size recommendations
  - Better error handling

## 🔧 **Enhanced Features**

### **System Monitoring**
- Real-time GPU memory usage
- CPU and RAM monitoring
- Disk space tracking
- Server uptime display

### **Model Recommendations**
- Automatic model size estimation
- Memory requirement warnings
- Progressive model testing strategy

### **Better Error Handling**
- Clear error messages
- Memory overflow protection
- Automatic cleanup on errors
- Debug information display

### **Improved UI**
- Real-time status updates
- Button state management
- Success/error notifications
- System metrics dashboard

## 📊 **Model Testing Strategy**

### **Phase 1: Small Models (Test Setup)**
1. **GPT-2** (`gpt2`) - 117M parameters, ~0.5GB
2. **DialoGPT Small** (`microsoft/DialoGPT-small`) - 117M parameters, ~0.5GB
3. **DialoGPT Medium** (`microsoft/DialoGPT-medium`) - 345M parameters, ~1.5GB

### **Phase 2: Medium Models (If Small Work)**
4. **Mistral 7B** (`mistralai/Mistral-7B-Instruct-v0.1`) - 7B parameters, ~14GB
5. **Llama 2 7B** (`meta-llama/Llama-2-7b-chat-hf`) - 7B parameters, ~14GB
6. **CodeLlama 7B** (`codellama/CodeLlama-7b-Python-hf`) - 7B parameters, ~14GB

### **Phase 3: Large Models (If Resources Allow)**
7. **Llama 2 13B** (`meta-llama/Llama-2-13b-chat-hf`) - 13B parameters, ~26GB
8. **CodeLlama 13B** (`codellama/CodeLlama-13b-Python-hf`) - 13B parameters, ~26GB

### **Phase 4: Very Large Models (Multi-GPU)**
9. **CodeLlama 34B** (`codellama/CodeLlama-34b-Python-hf`) - 34B parameters, ~68GB
10. **Llama 2 70B** (`meta-llama/Llama-2-70b-chat-hf`) - 70B parameters, ~140GB

## 🚨 **Troubleshooting Guide**

### **Connection Issues**
```bash
# Check if server is running
ps aux | grep lm_studio_server

# Check if port is listening
netstat -tlnp | grep :8080

# Check GPU allocation
nvidia-smi

# Check job status
squeue -u $USER
```

### **Memory Issues**
```bash
# Check GPU memory
nvidia-smi

# Clear GPU cache (in server interface)
# Or restart server

# Check system memory
free -h

# Check disk space
df -h /cluster/tufts/datalab
```

### **Model Loading Issues**
- Start with smallest models first
- Check model name spelling
- Verify internet connection on HPC
- Try different model if one fails
- Use the memory estimation feature

### **Performance Issues**
- Monitor GPU memory usage
- Use appropriate resource allocation
- Clear cache between model switches
- Check for other users on the node

## 📈 **Resource Optimization**

### **Memory Management**
- Unload models when not in use
- Clear GPU cache regularly
- Use appropriate model sizes for your GPU
- Monitor memory usage in real-time

### **Performance Tips**
- Use FP16 precision for models
- Enable low_cpu_mem_usage for large models
- Use device_map="auto" for multi-GPU setups
- Monitor system resources

### **Storage Management**
- Work in `/cluster/tufts/datalab/zwu09`
- Keep home directory minimal
- Use cache directories efficiently
- Clean up unused models

## 🎯 **Success Checklist**

### **Before Starting**
- [ ] Connected to HPC successfully
- [ ] GPU allocation confirmed (`nvidia-smi`)
- [ ] Sufficient resources allocated
- [ ] Environment variables set

### **Server Running**
- [ ] Enhanced server started without errors
- [ ] Web interface accessible
- [ ] System monitoring working
- [ ] GPU memory visible

### **Model Testing**
- [ ] Small model loads successfully
- [ ] Text generation works
- [ ] No memory errors
- [ ] Can switch between models

### **Performance Verified**
- [ ] GPU memory usage reasonable
- [ ] Generation speed acceptable
- [ ] No crashes or errors
- [ ] System resources stable

## 📞 **Support Commands**

### **Quick Diagnostics**
```bash
# System status
nvidia-smi
free -h
df -h /cluster/tufts/datalab

# Process status
ps aux | grep python
ps aux | grep lm_studio

# Network status
netstat -tlnp | grep :8080
ss -tlnp | grep :8080
```

### **Resource Monitoring**
```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi

# System monitoring
htop

# Disk usage
du -sh /cluster/tufts/datalab/zwu09/*
```

---

**Last Updated**: September 29, 2025  
**Status**: Ready for enhanced setup with better debugging  
**Next Action**: Connect to HPC and start with optimal resource allocation
