# LM Studio HPC - Troubleshooting & Solutions

## 🔥 **Critical Issues Fixed**

### **Issue 1: GLIBC 2.27 Not Found (sentencepiece error)**

**Problem:**
```
/lib64/libm.so.6: version `GLIBC_2.27' not found
```

**Root Cause:** 
- CentOS 7 has GLIBC 2.17
- Packages in `~/.local/` were installed with pip and built for newer GLIBC
- sentencepiece library requires GLIBC 2.27+

**Solutions:**

#### **Option 1: Use Clean Environment (RECOMMENDED)**
```bash
cd /cluster/tufts/datalab/zwu09

# Setup (one-time)
chmod +x setup_clean_env.sh
./setup_clean_env.sh

# Run server
chmod +x start_lm_studio_clean.sh
./start_lm_studio_clean.sh
```

#### **Option 2: Use Compatible Models**
Avoid models that require sentencepiece. **Safe models:**
- ✅ `gpt2` - GPT-2 (117M)
- ✅ `distilgpt2` - Smaller GPT-2 (82M)
- ✅ `microsoft/DialoGPT-small` - Conversational (117M)
- ✅ `microsoft/DialoGPT-medium` - Better quality (345M)
- ✅ `EleutherAI/pythia-70m` - Very small (70M)
- ✅ `EleutherAI/pythia-410m` - Good balance (410M)

**Avoid these (require sentencepiece):**
- ❌ `meta-llama/*` - Llama models
- ❌ `mistralai/*` - Mistral models
- ❌ `codellama/*` - Code Llama models

### **Issue 2: CUDA Not Detected**

**Problem:**
```
CUDA available: False
⚠️  Warning: No CUDA GPUs detected, will use CPU (slow)
```

**Causes:**
1. Using wrong Python version
2. PyTorch installed without CUDA support
3. Environment variables not set

**Solutions:**

#### **Check GPU is allocated:**
```bash
nvidia-smi
```

#### **Use correct Python with CUDA-enabled PyTorch:**
```bash
# The clean environment setup installs CUDA-enabled PyTorch automatically
./setup_clean_env.sh
```

#### **Manual CUDA PyTorch install:**
```bash
source /cluster/tufts/datalab/zwu09/envs/lmstudio_clean/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

#### **Verify CUDA detection:**
```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available(), 'GPUs:', torch.cuda.device_count())"
```

### **Issue 3: NumPy Version Mismatch**

**Problem:**
```
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.2.6
```

**Solution:** Clean environment fixes this automatically, or:
```bash
pip install 'numpy<2.0'
```

## 🚀 **Quick Start Guide**

### **Step 1: Setup (One-Time)**
```bash
cd /cluster/tufts/datalab/zwu09

# Make scripts executable
chmod +x setup_clean_env.sh start_lm_studio_clean.sh start_lm_studio.sh

# Setup clean environment
./setup_clean_env.sh
```

### **Step 2: Start Server**
```bash
# Option A: Clean environment (recommended)
./start_lm_studio_clean.sh

# Option B: Auto-detect best Python
./start_lm_studio.sh
```

### **Step 3: Access Interface**
Open browser: `http://localhost:8080`

### **Step 4: Test with Safe Model**
1. Click "✅ GPT-2" in the Quick-Load section
2. Wait for "Model loaded successfully"
3. Enter prompt: "Hello, how are you?"
4. Click "Generate"

## 📋 **Recommended Models by Size**

### **Tiny (< 100MB) - Testing**
- `distilgpt2` (82M) - Fastest for testing
- `EleutherAI/pythia-70m` (70M) - Alternative tiny model

### **Small (< 500MB) - Good for demos**
- `gpt2` (117M) - **Best starting point**
- `microsoft/DialoGPT-small` (117M) - Conversational

### **Medium (1-2GB) - Better quality**
- `microsoft/DialoGPT-medium` (345M) - Good conversations
- `EleutherAI/pythia-410m` (410M) - General purpose

### **Large (2-5GB) - High quality**
- `microsoft/DialoGPT-large` (774M) - Best DialogGPT
- `EleutherAI/pythia-1b` (1B) - Larger, more capable

## 🔍 **Debugging Commands**

### **Check Environment:**
```bash
# Check Python version
python --version

# Check PyTorch and CUDA
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}'); print(f'GPUs: {torch.cuda.device_count()}')"

# Check transformers
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"

# Check if sentencepiece causes issues
python -c "import sentencepiece" && echo "sentencepiece OK" || echo "sentencepiece FAILS (expected on CentOS 7)"
```

### **Check GPU:**
```bash
# GPU status
nvidia-smi

# GPU memory
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv

# Current job
squeue -u $USER
```

### **Check Server:**
```bash
# Check if server is running
ps aux | grep lm_studio

# Check port
netstat -tlnp | grep :8080

# Server logs
# (look in terminal where server was started)
```

## 🛠️ **Advanced Troubleshooting**

### **Clean Up Old Packages**
```bash
# Remove problematic packages from ~/.local
rm -rf ~/.local/lib/python3.11/site-packages/sentencepiece*

# Or disable user site-packages entirely
export PYTHONNOUSERSITE=1
```

### **Fresh Start**
```bash
# Remove old environment
rm -rf /cluster/tufts/datalab/zwu09/envs/lmstudio_clean

# Setup fresh
./setup_clean_env.sh
```

### **Check SLURM Job**
```bash
# View job details
squeue -u $USER
scontrol show job <JOBID>

# Check allocated resources
echo "Allocated GPUs: $CUDA_VISIBLE_DEVICES"
```

## 📊 **Expected Performance**

### **Model Load Times:**
- GPT-2 (117M): 5-10 seconds
- DialoGPT Medium (345M): 10-20 seconds
- Large models (1B+): 30-60 seconds

### **Generation Speed:**
- **With GPU:** 20-50 tokens/second
- **CPU only:** 1-5 tokens/second (very slow)

If generation is very slow, check CUDA is detected!

## ✅ **Success Checklist**

Before reporting issues, verify:
- [ ] GPU shows in `nvidia-smi`
- [ ] Clean environment setup completed
- [ ] CUDA detected in Python: `torch.cuda.is_available() == True`
- [ ] Server starts without errors
- [ ] Tried safe models (gpt2, distilgpt2)
- [ ] Browser can access http://localhost:8080

## 📞 **Still Having Issues?**

If problems persist:

1. **Capture full error output:**
   ```bash
   ./start_lm_studio_clean.sh 2>&1 | tee lm_studio_debug.log
   ```

2. **Check system info:**
   ```bash
   cat /etc/redhat-release
   ldd --version
   python --version
   nvidia-smi
   ```

3. **Try simplest case:**
   ```bash
   source /cluster/tufts/datalab/zwu09/envs/lmstudio_clean/bin/activate
   python -c "import torch; from transformers import AutoTokenizer, AutoModelForCausalLM; print('All imports OK')"
   ```

---

**Last Updated:** September 29, 2025  
**Status:** Tested and working with clean environment approach
