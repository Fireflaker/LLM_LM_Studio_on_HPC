# Tufts HPC LLM Setup: Complete Master Guide

**Last Updated**: October 1, 2025  
**Status**: ✅ Production Ready  
**Purpose**: Single source of truth for running ChatGPT-like LLM interface on Tufts HPC

---

## 📋 Quick Reference

**User**: `zwu09@tufts.edu`  
**HuggingFace Token**: `YOUR_HF_TOKEN_HERE`  
**Storage**: `/cluster/tufts/datalab/zwu09` (270GB available) + `/cluster/tufts/em212class/zwu09` (991GB available)  
**Conda Env**: `lmstudio_v3` (Python 3.11, PyTorch 2.8.0+cu128)  
**Application**: Text-Generation-WebUI (ChatGPT-like interface)

---

## 🚀 Quick Start (30 seconds to running LLM)

```bash
# 1. Login and request H100 GPU
ssh zwu09@login.pax.tufts.edu
srun -p preempt --gres=gpu:h100:1 -c 40 --mem=100G -t 04:00:00 --pty bash

# 2. Start server
cd /cluster/tufts/datalab/zwu09/text-generation-webui
source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh
conda activate lmstudio_v3
export HF_TOKEN=YOUR_HF_TOKEN_HERE
export PYTHONNOUSERSITE=1
export HF_HOME=/cluster/tufts/datalab/zwu09/caches/huggingface
export TRANSFORMERS_CACHE=/cluster/tufts/datalab/zwu09/caches/huggingface
python server.py --listen --listen-port 7860 --autosplit --no_flash_attn --trust-remote-code --verbose

# 3. In NEW local terminal, create SSH tunnel (replace s1cmp010 with your node from `hostname`)
ssh -L 7860:s1cmp010.pax.tufts.edu:7860 zwu09@login.pax.tufts.edu

# 4. Open browser: http://localhost:7860
```

**That's it!** The UI loads models and works like ChatGPT.

---

## 💾 Storage Management & Monitoring

### Storage Locations
- **Datalab**: `/cluster/tufts/datalab/zwu09` (2.3TB total, ~270GB free)
- **Class Storage**: `/cluster/tufts/em212class/zwu09` (1TB total, ~991GB free)

### Storage Performance
- **Datalab**: 931 MB/s write speed
- **Class Storage**: 828 MB/s write speed

### Monitor Storage Usage
```bash
# Real-time storage monitoring
watch -d 'df -h /cluster/tufts/datalab/zwu09/ /cluster/tufts/em212class/zwu09/'

# Check model sizes
du -sh /cluster/tufts/datalab/zwu09/text-generation-webui/user_data/models/* | sort -hr
```

### Use Class Storage for Large Models
```bash
# Create symlink to class storage for large models
rm -rf /cluster/tufts/datalab/zwu09/text-generation-webui/user_data/models
ln -sf /cluster/tufts/em212class/zwu09/text-generation-webui/user_data/models /cluster/tufts/datalab/zwu09/text-generation-webui/user_data/models
```

### Storage Monitoring Script
```bash
# Create monitoring script
cat > /cluster/tufts/datalab/zwu09/monitor_storage.sh << 'EOF'
#!/bin/bash
while true; do
    clear
    echo "=== Storage Usage Monitor - $(date) ==="
    echo ""
    echo "📊 DATALAB STORAGE:"
    df -h /cluster/tufts/datalab/zwu09/ | tail -1 | awk '{print "   Used: " $3 " / " $2 " (" $5 ")"}'
    echo ""
    echo "📊 CLASS STORAGE (em212class):"
    df -h /cluster/tufts/em212class/zwu09/ | tail -1 | awk '{print "   Used: " $3 " / " $2 " (" $5 ")"}'
    echo ""
    echo "📁 MODELS DIRECTORY:"
    ls -la /cluster/tufts/datalab/zwu09/text-generation-webui/user_data/models/ | head -5
    echo ""
    echo "Press Ctrl+C to exit"
    sleep 5
done
EOF

chmod +x /cluster/tufts/datalab/zwu09/monitor_storage.sh

# Run monitoring
bash /cluster/tufts/datalab/zwu09/monitor_storage.sh
```

---

## 📚 Full Setup (First Time Only)

### Step 1: Login & Request Compute Node

```bash
# From your local machine
ssh zwu09@login.pax.tufts.edu
# Enter password + 2FA (Duo)

# FIRST: Check available GPU hardware
sinfo -p preempt -o "%P %G %N %T" | grep idle

# Request GPU compute node (adjust based on availability)
# For H100: srun -p preempt --gres=gpu:h100:1 -c 40 --mem=100G -t 04:00:00 --pty bash
# For A100: srun -p preempt --gres=gpu:a100:1 -c 40 --mem=100G -t 04:00:00 --pty bash
# For multiple GPUs: srun -p preempt --gres=gpu:h100:3 -c 40 --mem=100G -t 04:00:00 --pty bash

# Verify you're on compute node (should show s1cmp### NOT login-prod-##)
hostname
nvidia-smi  # Should show GPU(s)
```

**Available GPU Types:**
- **H100**: Best for large models (80GB VRAM each)
- **A100**: Good for medium models (40GB VRAM each) 
- **RTX 6000**: For smaller models (24GB VRAM each)

### Step 2: Setup Environment (One-Time)

```bash
cd /cluster/tufts/datalab/zwu09

# Initialize conda
source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh

# Create conda environment (if not exists)
conda create -n lmstudio_v3 python=3.11 -y
conda activate lmstudio_v3

# Install PyTorch with CUDA 12.8 (H100 support)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Verify CUDA works
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPUs: {torch.cuda.device_count()}')"
# Output should be: CUDA: True, GPUs: 1 (or 2)

# Clone Text-Generation-WebUI (if not exists)
git clone https://github.com/oobabooga/text-generation-webui.git
cd text-generation-webui

# Install dependencies
pip install -r requirements/full/requirements.txt

# Set environment variables
export HF_TOKEN=YOUR_HF_TOKEN_HERE
export PYTHONNOUSERSITE=1
export HF_HOME=/cluster/tufts/datalab/zwu09/caches/huggingface
export TRANSFORMERS_CACHE=/cluster/tufts/datalab/zwu09/caches/huggingface
```

### Step 3: Start Server

```bash
cd /cluster/tufts/datalab/zwu09/text-generation-webui

# Start server with optimal flags
python server.py --listen --listen-port 7860 --autosplit --no_flash_attn --trust-remote-code --verbose
```

**Server will start and show:**
```
Starting Text Generation Web UI
Running on: http://0.0.0.0:7860
```

### Step 4: Access Web Interface

**On your LOCAL Windows PC**, open NEW terminal:

```bash
# Get compute node name from HPC terminal (hostname command)
# Then create SSH tunnel:
ssh -L 7860:s1cmp010.pax.tufts.edu:7860 zwu09@login.pax.tufts.edu
```

Open browser: `http://localhost:7860`

### Step 5: Load a Model

**In the Web UI:**
1. Go to **Model** tab
2. Change **Model loader** to **Transformers** (not llama.cpp!)
3. Enter model name: `Qwen/Qwen2.5-Coder-7B-Instruct`
4. Click **Download** (takes 2-5 minutes)
5. Click **Load**
6. Go to **Chat** tab and start chatting!

---

## 🎯 Recommended Models

### Single H100 (80GB VRAM):
- **Qwen/Qwen2.5-Coder-7B-Instruct** (7B) - Fast, great for coding
- **Qwen/Qwen2.5-32B-Instruct** (32B) - Balanced quality/speed
- **meta-llama/Meta-Llama-3.1-70B-Instruct** (70B) - Best quality, needs 4-bit quantization

### Multi H100 (160GB VRAM):
- **Qwen/Qwen2.5-72B-Instruct** (72B) - Top-tier
- **meta-llama/Meta-Llama-3.1-405B** (405B) - Requires 3+ H100s

---

## ⚠️ Critical Pitfalls & Solutions

### 1. Using Home Directory Instead of Datalab
**❌ Problem**: Home (`~`) is only 50GB, fills quickly  
**✅ Solution**: Always work in `/cluster/tufts/datalab/zwu09`  
**Check**: `pwd` should show `/cluster/tufts/datalab/zwu09`

### 2. Forgetting to Request Compute Node
**❌ Problem**: Running on login node = slow + gets killed  
**✅ Solution**: Always use `srun` first  
**Check**: `hostname` should show `s1cmp###`, NOT `login-prod-##`

### 3. Wrong Model Loader
**❌ Problem**: Default `llama.cpp` only works with GGUF files  
**✅ Solution**: Change to **Transformers** in Model tab  
**For**: HuggingFace models like Qwen, Llama, Mistral

### 4. GLIBC Errors (CentOS 7 Issue)
**❌ Problem**: `GLIBC_2.32 not found` when loading models  
**✅ Solution**: Use `--no_flash_attn` flag  
**Example**: `python server.py --listen --listen-port 7860 --no_flash_attn`

### 5. Server Dies on Disconnect
**❌ Problem**: Server stops when SSH disconnects  
**✅ Solution**: Use `nohup` and `disown`:
```bash
nohup python server.py --listen --listen-port 7860 --autosplit --no_flash_attn --trust-remote-code --verbose > server.log 2>&1 < /dev/null &
disown
```

### 6. SSH Tunnel to Wrong Node
**❌ Problem**: Can't connect to UI  
**✅ Solution**: Check node with `hostname`, tunnel to THAT node  
**Example**: If `hostname` shows `s1cmp010.pax.tufts.edu`, tunnel to that exact node

### 7. VRAM Always Full
**❌ Problem**: VRAM stays at 60GB+ even with no model  
**✅ Solution**: Unload model in UI (Model tab → Unload button)  
**Note**: VRAM stays high while model is loaded - this is NORMAL

### 8. Out of Memory
**❌ Problem**: Model too large for GPU  
**✅ Solution**: Enable 4-bit quantization in Model tab → load_in_4bit checkbox  
**OR**: Request multiple GPUs

### 9. Connection Refused Errors
**❌ Problem**: `channel 3: open failed: connect failed: Connection refused`  
**✅ Solution**: Server not running. Check with `ps aux | grep server.py`  
**Fix**: Restart server, ensure it's running before creating tunnel

### 10. Multiple Junk Environments
**❌ Problem**: Old broken conda envs taking up space  
**✅ Solution**: Clean up (see Cleanup section below)

### 11. Storage Space Issues
**❌ Problem**: Downloads fail due to insufficient disk space  
**Symptoms**: `No space left on device`, incomplete model downloads  
**✅ Solutions**:
- **Monitor storage**: `watch -d 'df -h /cluster/tufts/datalab/zwu09/'`
- **Use class storage**: Symlink models to `/cluster/tufts/em212class/zwu09/`
- **Clean up caches**: `rm -rf /cluster/tufts/datalab/zwu09/caches/huggingface/*`
- **Delete unused models**: Remove large models you don't need

### 12. Incomplete Model Downloads
**❌ Problem**: Models appear to download but fail to load  
**Symptoms**: Missing `modeling_*.py` files, incomplete safetensors  
**✅ Solutions**:
- **Check download progress**: `ls -la model-*.safetensors | wc -l`
- **Restart download**: Delete incomplete model and re-download
- **Use class storage**: Ensure sufficient space for complete download

---

## 🧹 Cleanup & Maintenance

### Remove Junk Environments

```bash
cd /cluster/tufts/datalab/zwu09

# List all conda environments
source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh
conda env list

# Remove duplicate/broken environments
conda env remove -n textgen_webui -y  # Duplicate
conda env remove -n OLD_ENV_NAME -y   # Any others

# Remove old environment directories
rm -rf envs/lmstudio envs/llm_diffuse_env envs/vllm envs/vllm311

# Remove temporary files
rm -rf tmp/* plotly llvmlite cursor_setup

# Check space saved
du -sh * | sort -hr | head -10
```

### Keep Only Working Environment

**KEEP**:
- `lmstudio_v3` (conda env in ~/.conda/envs/)
- `text-generation-webui/` (application)
- `caches/huggingface/` (model cache)

**DELETE**:
- Any other conda envs
- Old `envs/` directories
- Temporary files, logs, setup scripts

---

## 🔧 Advanced Configuration

### Server Persistence (Survives Disconnect)

```bash
# Start persistent server
cd /cluster/tufts/datalab/zwu09/text-generation-webui
nohup python server.py \
    --listen \
    --listen-port 7860 \
    --autosplit \
    --no_flash_attn \
    --trust-remote-code \
    --verbose \
    > server.log 2>&1 < /dev/null &

# Disconnect server from shell
disown

# Verify running
ps aux | grep server.py

# Check logs
tail -f server.log
```

### Multi-GPU Configuration

For Llama 3.1 70B or larger models:

```bash
# Request 2 H100s
srun -p preempt --gres=gpu:h100:2 -c 80 --mem=200G -t 04:00:00 --pty bash

# Start with autosplit (automatically uses both GPUs)
python server.py --listen --listen-port 7860 --autosplit --no_flash_attn --trust-remote-code --verbose

# Monitor GPU usage
watch -n 1 nvidia-smi
```

### 4-bit Quantization (Faster, Less VRAM)

**In WebUI Model tab:**
- ✅ Check **load_in_4bit**
- ✅ Check **trust_remote_code**
- ❌ Uncheck **use_flash_attention_2**

**Result**: ~4x less VRAM, 2x faster loading, minimal quality loss

---

## 📊 Storage Management

### Check Storage Usage

```bash
# Overall datalab usage
df -h /cluster/tufts/datalab/zwu09

# Breakdown by directory
cd /cluster/tufts/datalab/zwu09
du -sh * | sort -hr | head -20

# Find large files
find . -type f -size +1G 2>/dev/null | head -10
```

### Model Cache Management

```bash
# Check cached models
ls -lh caches/huggingface/hub/

# Remove specific model
rm -rf caches/huggingface/hub/models--Qwen--Qwen2.5-Coder-7B-Instruct

# Models re-download automatically when needed
```

---

## 🛠 Troubleshooting

### Server Won't Start

```bash
# Check if port is in use
ss -tulpn | grep 7860

# Use different port
python server.py --listen --listen-port 7861 --autosplit

# Check for errors
tail -100 server.log
```

### Can't Access Web UI

```bash
# 1. Verify server running
ps aux | grep server.py

# 2. Check compute node
hostname  # Copy this exact name

# 3. Recreate SSH tunnel with correct node
ssh -L 7860:EXACT_NODE_NAME:7860 zwu09@login.pax.tufts.edu

# 4. Try browser with http://localhost:7860
```

### GPU Not Detected

```bash
# Check GPU allocation
nvidia-smi

# If no GPU shown, you're on login node!
# Exit and request compute node:
exit
srun -p preempt --gres=gpu:h100:1 -c 40 --mem=100G -t 04:00:00 --pty bash
```

### Import Errors

```bash
# Reinstall dependencies
conda activate lmstudio_v3
pip install -r /cluster/tufts/datalab/zwu09/text-generation-webui/requirements/full/requirements.txt --force-reinstall
```

---

## 📁 Final Directory Structure

```
/cluster/tufts/datalab/zwu09/
├── text-generation-webui/       # Main application ✅ KEEP
│   ├── server.py
│   ├── models/
│   └── ...
├── caches/                       # Model cache ✅ KEEP
│   └── huggingface/
│       └── hub/                  # Cached models here
└── .conda_envs_backup/           # Old envs backup (can delete after verification)
```

**Conda environment**: `lmstudio_v3` in `~/.conda/envs/lmstudio_v3/`

---

## 🎯 What We Learned

### ❌ DON'T Reinvent the Wheel
- Custom Flask servers = slow, no features
- vLLM = API only, no UI for interactive use
- LM Studio Desktop = requires VNC, complex setup

### ✅ DO Use Industry Standards
- Text-Generation-WebUI = 50k+ stars, proven solution
- ChatGPT-like interface out of the box
- Multi-GPU support built-in
- Active development, great community

### ⚠️ CRITICAL Rules
1. **Always work in `/cluster/tufts/datalab/zwu09`** (not home!)
2. **Always request compute node first** (`srun` before any work)
3. **Use Transformers loader** for HuggingFace models
4. **Never load HPC modules** (use conda directly)
5. **Use `--no_flash_attn`** to avoid GLIBC issues on CentOS 7

---

## 📞 Resources

- **Text-Gen-WebUI**: https://github.com/oobabooga/text-generation-webui
- **HuggingFace Models**: https://huggingface.co/models
- **Tufts HPC Docs**: https://it.tufts.edu/high-performance-computing

---

## ✅ Success Checklist

- [ ] Logged into HPC (`ssh zwu09@login.pax.tufts.edu`)
- [ ] Requested compute node (`srun -p preempt --gres=gpu:h100:1...`)
- [ ] Verified on compute node (`hostname` shows s1cmp###)
- [ ] Activated conda environment (`conda activate lmstudio_v3`)
- [ ] Set HF_TOKEN environment variable
- [ ] Started server (`python server.py --listen...`)
- [ ] Created SSH tunnel from local PC
- [ ] Accessed http://localhost:7860
- [ ] Changed model loader to Transformers
- [ ] Downloaded and loaded a model
- [ ] Successfully chatted with the model ✨

**You now have a production-ready ChatGPT-like interface on Tufts HPC!** 🎉

---

**Last Updated**: September 30, 2025  
**Tested On**: Tufts HPC, H100 PCIe (80GB), CentOS 7  
**Status**: ✅ Production Ready

