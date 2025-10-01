# LM Studio Complete Setup Guide
**Date**: September 30, 2025  
**User**: zwu09@tufts.edu  
**Goal**: Set up LM Studio incrementally following proven methods

---

## 🚨 CRITICAL RULES (from prior experience)

### **NEVER Load Modules**
- ❌ **DO NOT** run `module load` commands
- ❌ **DO NOT** use precompiled modules (including CUDA 12.2)
- ❌ Both Python 3.11 tufts ai and Python 3.12 modules are **CORRUPTED**
- ✅ Use **conda directly** without loading any modules

### **Storage Policy**
- ✅ Work in `/cluster/tufts/datalab/zwu09` (not home directory)
- ❌ Home directory is small and should stay empty
- ✅ Put ALL caches, envs, and temporary files in datalab

### **Proven Working Method**
- ✅ Use conda to create environment with Python 3.11
- ✅ Install PyTorch with CUDA 12.1 (not 12.2) from pip
- ✅ Follow the `llm-dfuse-env` approach that worked before

---

## 📋 Step-by-Step Setup

### **Step 1: SSH to HPC**
```bash
# From your local machine (Git Bash or PowerShell)
ssh zwu09@login.pax.tufts.edu
# Password: Leowzd832126
# Use Duo 2FA (option 1 for push)
```

### **Step 2: Check Current Allocations**
```bash
# Check if any jobs are running
squeue -u $USER

# If jobs exist, cancel them
scancel <JOBID>

# Or cancel all your jobs
scancel -u $USER
```

### **Step 3: Request GPU Allocation**

**Option A: Single A100 (recommended for initial setup)**
```bash
srun -p preempt --gres=gpu:a100:1 -c 40 --mem=100G -t 03:00:00 --pty bash
```

**Option B: Two A100s (for larger models)**
```bash
srun -p preempt --gres=gpu:a100:2 -c 80 --mem=200G -t 04:00:00 --pty bash
```

**Option C: If A100 not available, try other GPUs**
```bash
# L40 (good alternative)
srun -p preempt --gres=gpu:l40:1 -c 40 --mem=100G -t 03:00:00 --pty bash

# V100 (older but works)
srun -p preempt --gres=gpu:v100:1 -c 32 --mem=64G -t 02:00:00 --pty bash
```

### **Step 4: Verify GPU Allocation**
Once you get a compute node:
```bash
# Check where you are
hostname
echo "Job ID: $SLURM_JOB_ID"

# Verify GPU
nvidia-smi

# Check resources
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory: $SLURM_MEM_PER_NODE MB"
echo "GPUs: $CUDA_VISIBLE_DEVICES"
```

### **Step 5: Initialize Conda (DO NOT LOAD MODULES)**
```bash
# Navigate to datalab
cd /cluster/tufts/datalab/zwu09

# Initialize conda directly (no module load!)
source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh

# Verify conda is available
conda --version
```

### **Step 6: Create Conda Environment**
```bash
# Create environment with Python 3.11
conda create -n lmstudio python=3.11 -y

# Activate environment
conda activate lmstudio

# Verify Python version
python --version  # Should show Python 3.11.x
which python      # Should point to conda env
```

### **Step 7: Upgrade pip**
```bash
pip install --upgrade pip setuptools wheel
```

### **Step 8: Install PyTorch with CUDA 12.1**
```bash
# Install PyTorch with CUDA 12.1 support (NOT 12.2!)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### **Step 9: Install LM Studio Dependencies**
```bash
# Install transformers and related packages
pip install transformers accelerate

# Install Flask for web interface
pip install flask psutil

# Optional: Install sentencepiece (may fail due to GLIBC issues)
pip install sentencepiece || echo "sentencepiece install failed (expected on CentOS 7)"
```

### **Step 10: Verify CUDA Detection**
```bash
python << 'EOF'
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU count: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
else:
    print("⚠️  CUDA not detected - check installation")
EOF
```

**Expected output:**
```
PyTorch version: 2.x.x+cu121
CUDA available: True
CUDA version: 12.1
GPU count: 1 (or 2)
  GPU 0: NVIDIA A100-PCIE-80GB
```

### **Step 11: Download LM Studio Server**
```bash
cd /cluster/tufts/datalab/zwu09

# The server file should already exist: lm_studio_server_robust_v2.py
ls -lh lm_studio_server_robust_v2.py

# If not, it's in the HPC folder
```

### **Step 12: Set Environment Variables**
```bash
# Disable user site packages to avoid conflicts
export PYTHONNOUSERSITE=1

# Set cache directories
export HF_HOME=/cluster/tufts/datalab/zwu09/caches/huggingface
export TRANSFORMERS_CACHE=/cluster/tufts/datalab/zwu09/caches/huggingface
export TORCH_HOME=/cluster/tufts/datalab/zwu09/caches/torch
export TMPDIR=/cluster/tufts/datalab/zwu09/tmp

# Create directories
mkdir -p "$HF_HOME" "$TRANSFORMERS_CACHE" "$TORCH_HOME" "$TMPDIR"
```

### **Step 13: Start LM Studio Server**
```bash
# Start the server
python lm_studio_server_robust_v2.py
```

The server should start and show:
```
Starting LM Studio Server on port 8080...
Server running at http://127.0.0.1:8080
```

### **Step 14: Create SSH Tunnel (from your laptop)**

**On Windows (Git Bash):**
```bash
# Get the compute node hostname first (from the HPC terminal where server is running)
# It will be something like: s1cmp005.pax.tufts.edu

# Open a NEW terminal on your laptop (Git Bash)
ssh -J zwu09@login.pax.tufts.edu -L 8080:127.0.0.1:8080 zwu09@COMPUTE_NODE_HOSTNAME
```

**On Windows (PowerShell):**
```powershell
& 'C:\Windows\System32\OpenSSH\ssh.exe' -J 'zwu09@login.pax.tufts.edu' -L 8080:127.0.0.1:8080 "zwu09@COMPUTE_NODE_HOSTNAME"
```

Replace `COMPUTE_NODE_HOSTNAME` with the actual hostname from Step 4.

### **Step 15: Access Web Interface**
Open your browser and go to:
```
http://localhost:8080
```

---

## 🎯 Testing with Models

### **Start Small (Test First)**
1. **gpt2** - 117M parameters, ~500MB
2. **distilgpt2** - 82M parameters, ~300MB
3. **microsoft/DialoGPT-small** - 117M parameters

### **Models to AVOID (GLIBC Issues)**
❌ **DO NOT** try these models on CentOS 7:
- `meta-llama/*` (requires sentencepiece)
- `mistralai/*` (requires sentencepiece)
- `codellama/*` (requires sentencepiece)

### **Safe Models for CentOS 7**
✅ These work without sentencepiece:
- `gpt2`
- `distilgpt2`
- `microsoft/DialoGPT-small`
- `microsoft/DialoGPT-medium`
- `EleutherAI/pythia-70m`
- `EleutherAI/pythia-410m`

---

## 🚨 Troubleshooting

### **Problem: CUDA not detected**
```bash
# Check GPU is visible
nvidia-smi

# Verify environment
conda activate lmstudio
python -c "import torch; print(torch.cuda.is_available())"

# If False, reinstall PyTorch
pip install --force-reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### **Problem: Connection refused**
```bash
# Check server is running
ps aux | grep lm_studio

# Check port is listening
netstat -tlnp | grep :8080

# Restart server if needed
```

### **Problem: sentencepiece GLIBC error**
```
/lib64/libm.so.6: version `GLIBC_2.27' not found
```
**Solution**: Use models that don't require sentencepiece (see safe models list above)

### **Problem: Module not found**
```bash
# Make sure you're in the conda environment
conda activate lmstudio

# Reinstall the missing package
pip install <package_name>
```

### **Problem: Out of memory**
- Start with smaller models (gpt2)
- Reduce `max_length` parameter
- Use FP16: add `torch_dtype=torch.float16` when loading model

---

## 📝 Quick Reference Commands

### **Reconnect to Existing Session**
```bash
# SSH to HPC
ssh zwu09@login.pax.tufts.edu

# Check running jobs
squeue -u $USER

# Find the compute node
squeue -u $USER -h -o '%N'

# SSH to compute node
ssh NODE_HOSTNAME

# Reactivate environment
cd /cluster/tufts/datalab/zwu09
source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh
conda activate lmstudio

# Check if server is running
ps aux | grep lm_studio

# Restart server if needed
python lm_studio_server_robust_v2.py
```

### **Start Fresh Session**
```bash
# Cancel all jobs
scancel -u $USER

# Start from Step 3 (Request GPU Allocation)
```

---

## 💡 Key Insights from Prior Experience

1. **Never load modules** - they are broken
2. **Use conda directly** - source the conda.sh file
3. **Python 3.11 from conda** - not from modules
4. **CUDA 12.1 via pip** - not CUDA 12.2 modules
5. **Work in datalab** - not home directory
6. **Avoid sentencepiece models** - GLIBC issues on CentOS 7
7. **Start with small models** - test before going big
8. **Use preempt partition** - faster allocation

---

## 📁 File Locations

- **Conda**: `/cluster/tufts/hpc/tools/anaconda/202307/`
- **Working Directory**: `/cluster/tufts/datalab/zwu09/`
- **Environment**: `/cluster/tufts/hpc/tools/anaconda/202307/envs/lmstudio/`
- **LM Studio Server**: `/cluster/tufts/datalab/zwu09/lm_studio_server_robust_v2.py`
- **Caches**: `/cluster/tufts/datalab/zwu09/caches/`

---

## ✅ Success Checklist

Before using LM Studio, verify:
- [ ] GPU shows in `nvidia-smi`
- [ ] Conda environment activated
- [ ] CUDA detected: `torch.cuda.is_available() == True`
- [ ] Server starts without errors
- [ ] Tunnel connected from laptop
- [ ] Browser can access http://localhost:8080
- [ ] Small model (gpt2) loads successfully

---

**Last Updated**: September 30, 2025  
**Status**: Ready for incremental setup  
**Next Action**: Start from Step 1 when ready

