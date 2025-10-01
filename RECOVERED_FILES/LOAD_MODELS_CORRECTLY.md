# How to Load Models Correctly

**Date**: September 30, 2025  
**Server Status**: ✅ Running on s1cmp010 (PID: 2534271)  
**Access**: http://localhost:8080 (with SSH tunnel)

---

## ❌ What DOESN'T Work (GGUF Models)

These models have `-gguf` or `-GGUF` in the name and **ONLY work with LM Studio desktop app**:

```
❌ Manojb/Qwen3-4B-toolcalling-gguf-codex
❌ bartowski/Qwen2.5-7B-Instruct-GGUF
❌ TheBloke/Mistral-7B-Instruct-GGUF
❌ Any model with "GGUF" or "gguf" in the name
```

**Error you'll see:**
```
does not appear to have files named (...safetensors...)
```

---

## ✅ What WORKS (Standard PyTorch Models)

These are regular HuggingFace models that work with our transformers-based server:

### 🚀 Best for Coding (7B - Recommended to try first)
```
Qwen/Qwen2.5-Coder-7B-Instruct
deepseek-ai/deepseek-coder-6.7b-instruct
```

### 💬 Best for Chat (7B)
```
Qwen/Qwen2.5-7B-Instruct
mistralai/Mistral-7B-Instruct-v0.3
```

### 🧠 Best for Reasoning (14B)
```
microsoft/Phi-3-medium-4k-instruct
Qwen/Qwen2.5-14B-Instruct
```

### 🔬 Testing (Small)
```
gpt2
distilgpt2
```

---

## 🎯 How to Load in Web Interface

1. **Open browser**: http://localhost:8080
2. **Enter model name** (copy exactly from above)
3. **Click "Load Model"**
4. **Wait 3-5 minutes** for download and loading
5. **Start chatting!**

**Example:**
```
Model name: Qwen/Qwen2.5-Coder-7B-Instruct
```

---

## 🧪 Test Script

I created `test_load_big_model.py` for you to test loading before using web interface.

**To upload and run:**

1. Upload the file:
   ```bash
   scp HPC/test_load_big_model.py zwu09@s1cmp010.pax.tufts.edu:/cluster/tufts/datalab/zwu09/
   ```

2. On HPC, run:
   ```bash
   cd /cluster/tufts/datalab/zwu09
   source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh
   conda activate lmstudio_v3
   export HF_TOKEN=YOUR_HF_TOKEN_HERE
   python test_load_big_model.py
   ```

This will test loading `Qwen/Qwen2.5-7B-Instruct` and show if it works.

---

## 🔍 How to Tell GGUF vs Standard Models

### GGUF Model (❌ Won't work):
- Has `-gguf`, `-GGUF`, `.gguf` in the name
- Usually from users: `TheBloke`, `bartowski`, `Manojb`
- Files end in `.gguf`
- Example: `Manojb/Qwen3-4B-toolcalling-gguf-codex`

### Standard Model (✅ Will work):
- Official HuggingFace model page
- No "gguf" in the name
- Files end in `.safetensors` or `.bin`
- Example: `Qwen/Qwen2.5-7B-Instruct`

---

## 📝 Quick Reference

| Want to... | Use this model | Size |
|------------|---------------|------|
| **Code in Python/JS** | `Qwen/Qwen2.5-Coder-7B-Instruct` | 7B (~14GB) |
| **General chat** | `Qwen/Qwen2.5-7B-Instruct` | 7B (~14GB) |
| **Fast testing** | `gpt2` | 117M (~0.5GB) |
| **Best reasoning** | `microsoft/Phi-3-medium-4k-instruct` | 14B (~28GB) |

---

## 🚨 Current Issue Resolution

**Problem:** You tried to load `Manojb/Qwen3-4B-toolcalling-gguf-codex` (GGUF model)

**Solution:** Load the standard version instead:
```
Qwen/Qwen2.5-Coder-7B-Instruct  ← Use this instead!
```

This is the official Qwen coding model that will work with our server.

---

## 📡 Server Info

- **Running on**: s1cmp010.pax.tufts.edu
- **PID**: 2534271
- **Port**: 8080
- **Max input**: 2048 tokens (updated!)
- **Max output**: 512 tokens (updated!)
- **HF Token**: ✅ Configured

**SSH Tunnel command:**
```bash
ssh -J zwu09@login.pax.tufts.edu -L 8080:127.0.0.1:8080 zwu09@s1cmp010.pax.tufts.edu
```

---

**Next Step:** Try loading `Qwen/Qwen2.5-Coder-7B-Instruct` in the web interface at http://localhost:8080

