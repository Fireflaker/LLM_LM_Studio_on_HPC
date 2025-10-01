# HPC LM Studio Setup - Current Status & Next Steps

## 🎯 **Current Situation**
- **User**: zwu09@tufts.edu
- **Password**: Leowzd832126
- **Status**: User shut down all shells and released current allocation to request better resources
- **Goal**: Set up LM Studio on Tufts HPC with GPU acceleration for language model inference

## 📋 **What Was Accomplished**

### ✅ **Completed Setup Steps:**
1. **HPC Connection**: Successfully connected to Tufts HPC login node
2. **GPU Allocation**: Had H100 GPU with 81GB memory allocated (job 16337731)
3. **Datalab Environment**: Set up proper storage in `/cluster/tufts/datalab/zwu09`
4. **LM Studio Server**: Created improved server with better error handling
5. **Web Interface**: Working web interface with model management
6. **Storage Check**: Datalab at 85% usage (370GB available - not a storage issue)

### 🔧 **Technical Details:**
- **Node**: s1cmp010.pax.tufts.edu
- **GPU**: NVIDIA H100 PCIe with 81GB memory
- **Python**: `/cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11`
- **Server Port**: 8080
- **Server File**: `/cluster/tufts/datalab/zwu09/lm_studio_server_improved.py`

## 🚨 **Issues Encountered & Solutions**

### **Problem 1: Large Model Memory Issues**
- **Issue**: CodeLlama-34b-Python-hf (34B parameters) caused out-of-memory errors
- **Solution**: Created improved server with better memory management and smaller model recommendations

### **Problem 2: Server Crashes During Generation**
- **Issue**: Server crashed when generating text with large models
- **Solution**: Added comprehensive error handling, memory cleanup, and GPU memory monitoring

### **Problem 3: Connection Refused Errors**
- **Issue**: SSH tunnel connection refused
- **Solution**: Server wasn't running properly due to background process issues

## 📝 **Next Steps for New Session**

### **Step 1: Connect to HPC**
```bash
ssh zwu09@login.pax.tufts.edu
# Password: Leowzd832126
# Use Duo 2FA (option 1 for push)
```

### **Step 2: Request Better GPU Resources**
```bash
# Request more resources (suggested improvements):
srun -p preempt --gres=gpu:h100:2 -c 80 --mem=200G -t 04:00:00 --pty bash
# OR for even better resources:
srun -p gpu --gres=gpu:a100:2 -c 80 --mem=200G -t 04:00:00 --pty bash
```

### **Step 3: Set Up Environment**
```bash
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
cd $DATALAB_BASE
nvidia-smi  # Verify GPU access
```

### **Step 4: Start Improved LM Studio Server**
```bash
cd /cluster/tufts/datalab/zwu09
/cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11 lm_studio_server_improved.py
```

### **Step 5: Create SSH Tunnel (from local computer)**
```bash
ssh -J zwu09@login.pax.tufts.edu -L 8080:127.0.0.1:8080 zwu09@NODE_HOSTNAME
```

### **Step 6: Access Web Interface**
- Open browser to: `http://localhost:8080`
- Start with small models: GPT-2 (117M) or DialoGPT Small (117M)
- Test with simple prompts: "Hello, how are you?"

## 🎯 **Recommended Model Progression**

### **Start Small (Test First):**
1. **GPT-2 (117M)** - Fastest, lowest memory
2. **DialoGPT Small (117M)** - Good for conversations
3. **DialoGPT Medium (345M)** - Better quality

### **Medium Models (If Small Work):**
4. **DialoGPT Large (774M)** - High quality conversations
5. **Mistral 7B** - Modern, efficient model

### **Large Models (Only if Resources Allow):**
6. **CodeLlama-34b-Python-hf** - Code generation (34B parameters)
7. **Other large models** - Test gradually

## 🔧 **Server Features (Already Implemented)**

### **Error Handling:**
- Comprehensive error messages
- GPU memory monitoring
- Out-of-memory protection
- Model loading/unloading with cleanup

### **UI Improvements:**
- Error/success message display
- Button states (disabled during operations)
- Real-time status updates
- Debug information panel

### **Memory Management:**
- Automatic model cleanup
- GPU memory clearing
- Garbage collection
- Low CPU memory usage loading

## 📊 **Resource Recommendations**

### **For Small Models (GPT-2, DialoGPT Small):**
- **GPU**: 1x H100 or 1x A100
- **Memory**: 50GB RAM
- **CPUs**: 20-40 cores

### **For Medium Models (Mistral 7B, DialoGPT Large):**
- **GPU**: 1x H100 or 2x A100
- **Memory**: 100GB RAM
- **CPUs**: 40-60 cores

### **For Large Models (CodeLlama-34b):**
- **GPU**: 2x H100 or 4x A100
- **Memory**: 200GB+ RAM
- **CPUs**: 60-80 cores

## 🚨 **Common Issues & Solutions**

### **"Connection Refused" Error:**
- Check if server is running: `ps aux | grep lm_studio_server`
- Check if port is listening: `netstat -tlnp | grep :8080`
- Restart server if needed

### **"Out of Memory" Error:**
- Try smaller model first
- Reduce max_length parameter
- Unload current model before loading new one
- Check GPU memory: `nvidia-smi`

### **"Model Loading Failed" Error:**
- Check internet connection on HPC
- Verify model name is correct
- Try different model
- Check storage space: `df -h /cluster/tufts/datalab`

## 📁 **File Locations**

### **Server Files:**
- **Main Server**: `/cluster/tufts/datalab/zwu09/lm_studio_server.py`
- **Improved Server**: `/cluster/tufts/datalab/zwu09/lm_studio_server_improved.py`
- **Caches**: `/cluster/tufts/datalab/zwu09/caches/`

### **Environment Variables:**
```bash
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
export HF_HOME=$DATALAB_BASE/caches/huggingface
export TRANSFORMERS_CACHE=$DATALAB_BASE/caches/huggingface
export TORCH_HOME=$DATALAB_BASE/caches/torch
```

## 🎯 **Success Criteria**

### **Working Setup Should Show:**
1. ✅ Server running on port 8080
2. ✅ Web interface accessible via browser
3. ✅ Small models load successfully
4. ✅ Text generation works without crashes
5. ✅ Error messages are clear and helpful
6. ✅ GPU memory usage is monitored

### **Test Sequence:**
1. Load GPT-2 model
2. Generate text with "Hello, how are you?"
3. Verify response is generated
4. Try larger model if resources allow
5. Test various prompts and parameters

## 📞 **Support Information**

### **HPC System Details:**
- **Login Node**: login.pax.tufts.edu
- **Compute Nodes**: s1cmp010, s1cmp005, etc.
- **Partitions**: gpu, preempt, batch
- **GPU Types**: H100, A100, V100, T4

### **Network Requirements:**
- Use "Tufts Secure" Wi-Fi (not "Secure 6e")
- SSH tunnel required for web access
- Port 8080 for LM Studio server

### **Storage Policy:**
- Work in `/cluster/tufts/datalab/zwu09` (not home directory)
- Keep home directory minimal
- Use datalab for all models and caches

---

**Last Updated**: September 29, 2025
**Status**: Ready for new session with improved resources
**Next Action**: Connect to HPC and request better GPU allocation
