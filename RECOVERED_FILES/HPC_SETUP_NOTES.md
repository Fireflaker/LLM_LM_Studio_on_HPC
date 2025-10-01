# HPC Setup Notes - Key Findings & Solutions

## 🚨 Critical Issues Found

### 1. **Environment Compatibility Problems**
- **Current**: Python 3.6.8 + PyTorch 1.10.2 + CUDA 10.2
- **Problem**: Too old for A100 GPUs (need CUDA 11.0+)
- **A100 Requirement**: CUDA 11.0+ with PyTorch 1.12+

### 2. **Storage Issues**
- **Datalab**: 95% full (2.2T/2.3T used)
- **Solution**: Use RAM disk (/tmp) - 94GB available
- **Cache Strategy**: Set `PIP_CACHE_DIR=/tmp/gpu_test/pip_cache`

### 3. **vLLM Requirements**
- **Python**: 3.11 or 3.12 (NOT 3.6)
- **CUDA**: 12.2 (current system has 12.2 available)
- **PyTorch**: Latest with CUDA 12.2 support

## ✅ Working Commands

### System Checks
```bash
# Check disk space
df -h /cluster/tufts/datalab

# Check job status
squeue -u $USER

# Check GPU status
nvidia-smi

# Check current environment
hostname && echo "Job ID: $SLURM_JOB_ID" && echo "GPUs: $CUDA_VISIBLE_DEVICES"
```

### RAM Disk Setup
```bash
export TMPDIR=/tmp/gpu_test
export PIP_CACHE_DIR=/tmp/gpu_test/pip_cache
mkdir -p $PIP_CACHE_DIR
```

### Connect to Compute Node
```bash
# From login node to compute node
ssh -o StrictHostKeyChecking=no s1cmp005
```

## 🎯 Next Steps for vLLM

### Current Status
- **✅ Found Python 3.11.4** in `/cluster/tufts/hpc/tools/anaconda/202307/`
- **✅ PyTorch 2.0.1** available with CUDA support
- **❌ vLLM installation fails** due to missing build tools (cmake, gcc, etc.)
- **❌ Missing system dependencies** for compiling C++ extensions

### Next Steps
1. **Install build tools** (cmake, gcc, g++) if available
2. **Use pre-built wheels** instead of compiling from source
3. **Try alternative installation methods** (conda, pip with --no-build-isolation)
4. **Use Docker/containers** if available
5. **Request system administrator** to install missing build dependencies

### Alternative Solutions
- **Text Generation Inference (TGI)** by Hugging Face (pre-built)
- **Ollama** (if available)
- **Custom PyTorch serving** with current environment
- **Use pre-compiled vLLM wheels** if available

## 📝 Lessons Learned

- Always check Python version compatibility first
- Use RAM disk for temporary operations when datalab is full
- A100 GPUs need modern CUDA/PyTorch versions
- Shell commands work better than notebook packaging
- Check `nvidia-smi` to verify GPU availability
