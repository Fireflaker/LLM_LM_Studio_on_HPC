# LLM & LM Studio on HPC

Complete setup guide for running Large Language Models on HPC systems using H100/A100 GPUs.

**Tested on:** Tufts HPC (CentOS 7, H100 80GB)  
**Working Models:** Qwen2.5-Coder-7B, Qwen2.5-32B, and more

---

## 🚀 Quick Start

### 1. Connect to HPC
```bash
ssh your_username@login.pax.tufts.edu
```

### 2. Request GPU
```bash
srun -p preempt --gres=gpu:h100:1 -c 40 --mem=100G -t 04:00:00 --pty bash
```

### 3. Setup Environment
```bash
cd /cluster/tufts/datalab/your_username
source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh
conda create -n lmstudio python=3.11 -y
conda activate lmstudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers accelerate flask psutil
```

### 4. Start Server
```bash
export HF_TOKEN=your_huggingface_token_here
python lm_studio_server_v3_improved.py
```

### 5. Access from Your Laptop
```bash
# Create SSH tunnel
ssh -J your_username@login.pax.tufts.edu -L 8080:127.0.0.1:8080 your_username@compute_node_name

# Open browser
http://localhost:8080
```

---

## 📚 Documentation

### Essential Guides
- **[QUICK_START.md](QUICK_START.md)** - Fast setup instructions
- **[LM_STUDIO_COMPLETE_SETUP_GUIDE.md](LM_STUDIO_COMPLETE_SETUP_GUIDE.md)** - Comprehensive setup
- **[LOAD_MODELS_CORRECTLY.md](LOAD_MODELS_CORRECTLY.md)** - Understanding GGUF vs standard models
- **[RECOMMENDED_MODELS_H100.md](RECOMMENDED_MODELS_H100.md)** - Best models for H100

### Setup Guides
- **[OPERATIONS_SOP.md](OPERATIONS_SOP.md)** - Standard operating procedures
- **[HPC_SETUP_NOTES.md](HPC_SETUP_NOTES.md)** - Detailed HPC configuration
- **[WINDOWS_QUICK_START.md](WINDOWS_QUICK_START.md)** - Windows-specific instructions

### Advanced Topics
- **[BETTER_SOLUTIONS.md](BETTER_SOLUTIONS.md)** - vLLM and production alternatives
- **[UPDATES_SUMMARY.md](UPDATES_SUMMARY.md)** - Latest features and changes
- **[GUI_SOLUTIONS_GUIDE.md](GUI_SOLUTIONS_GUIDE.md)** - VNC and desktop options

---

## 🎯 Recommended Models

### Large (32B - Best Quality)
- **Qwen/Qwen2.5-Coder-32B-Instruct** - Best for coding (~64GB VRAM)
- **Qwen/Qwen2.5-32B-Instruct** - Best for chat (~64GB VRAM)
- **deepseek-ai/deepseek-coder-33b-instruct** - Advanced code understanding

### Medium (7B-14B - Fast & Good)
- **Qwen/Qwen2.5-Coder-7B-Instruct** - ✅ Tested & Working (~14GB VRAM)
- **Qwen/Qwen2.5-14B-Instruct** - Balanced performance (~28GB VRAM)
- **microsoft/Phi-3-medium-4k-instruct** - Excellent reasoning (~28GB VRAM)

All recommended models are **ungated** (no approval needed) and work with standard transformers library.

---

## ⚠️ Important Notes

### GGUF vs Standard Models
- ❌ **GGUF models** (with `-gguf` in name) only work with LM Studio desktop app
- ✅ **Standard models** (from HuggingFace) work with our transformers-based server
- Example: Use `Qwen/Qwen2.5-7B-Instruct` NOT `bartowski/Qwen2.5-7B-GGUF`

### Storage Policy
- ⚠️ **HOME directory is SMALL** - do NOT store models there
- ✅ Use `/cluster/tufts/datalab/your_username` for everything
- ✅ Models cache in `caches/huggingface/` (automatically)

### Module Loading
- ❌ **DO NOT** run `module load` commands (Python modules are corrupted)
- ✅ Use conda directly: `source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh`

---

## 🔧 Troubleshooting

### Rate Limit Errors
**Solution:** Set HuggingFace token:
```bash
export HF_TOKEN=your_token_here
```

### CUDA Not Detected
**Solution:** Verify GPU allocation:
```bash
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
```

### Model Won't Load
**Check:**
1. Is it a GGUF model? (Use standard models instead)
2. Do you have enough VRAM? (Check with `nvidia-smi`)
3. Is HF_TOKEN set? (For rate limits)

---

## 🚀 Alternative Solutions

For production use, consider these instead of custom server:

### vLLM (Recommended for Performance)
- 2-5x faster inference
- Conversational context built-in
- OpenAI-compatible API
- Industry standard

```bash
pip install vllm
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-Coder-7B-Instruct \
    --port 8080 --host 0.0.0.0
```

### Text Generation WebUI (Best UI)
- ChatGPT-like interface
- Conversation history
- Most popular open-source solution

See [BETTER_SOLUTIONS.md](BETTER_SOLUTIONS.md) for details.

---

## 📁 Repository Structure

```
HPC/
├── README.md                          # This file
├── QUICK_START.md                     # Fast setup guide
├── LM_STUDIO_COMPLETE_SETUP_GUIDE.md # Comprehensive guide
├── OPERATIONS_SOP.md                  # Standard procedures
├── BETTER_SOLUTIONS.md                # Production alternatives
├── lm_studio_server_v3_improved.py   # Main server
├── test_load_big_model.py            # Model testing script
├── scripts/                           # Setup scripts
│   ├── setup_vnc_desktop_full.sh
│   └── setup_lm_studio_v3.sh
└── archive/                           # Older versions
```

---

## 🎯 Features

- ✅ Model caching (no re-downloads)
- ✅ Force re-download option
- ✅ HuggingFace token support
- ✅ H100/A100 GPU support
- ✅ Web interface
- ✅ Multiple model support
- ✅ 2048 token input, 512 token output
- ✅ GPU memory monitoring

---

## 📊 Tested Configuration

- **HPC**: Tufts University HPC
- **OS**: CentOS 7
- **GPU**: NVIDIA H100 PCIe 80GB
- **CUDA**: 12.1
- **Python**: 3.11.13
- **PyTorch**: 2.5.1+cu121
- **Transformers**: 4.56.2

---

## 🤝 Contributing

This repository documents a working HPC LLM setup. Feel free to:
- Report issues
- Suggest improvements
- Share your configuration
- Add support for other HPC systems

---

## 📝 License

Educational and research use. Adapt for your HPC environment.

---

## 🔗 Useful Links

- [HuggingFace Models](https://huggingface.co/models)
- [vLLM Documentation](https://docs.vllm.ai/)
- [Text Generation WebUI](https://github.com/oobabooga/text-generation-webui)
- [LM Studio](https://lmstudio.ai/)

---

**Last Updated:** September 30, 2025  
**Status:** ✅ Working and tested  
**Recommended Model:** Qwen/Qwen2.5-Coder-7B-Instruct (tested & working)

