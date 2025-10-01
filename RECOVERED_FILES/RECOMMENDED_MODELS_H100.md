# Recommended Models for H100 (80GB) with Transformers Library

**Date**: September 30, 2025  
**Setup**: Transformers + PyTorch + CUDA 12.1  
**HF Token**: YOUR_HF_TOKEN_HERE (get from https://huggingface.co/settings/tokens)

## ⚠️ CRITICAL: GGUF vs Standard Models

- ❌ **GGUF models** = Only for LM Studio Desktop App (e.g., `*-gguf`, `*-GGUF`)
- ✅ **Standard models** = For our transformers-based server

## 🎯 Best Models for H100 (80GB VRAM)

### Tier 1: Recommended (Tested & Working)
| Model | Size | VRAM | Best For | HuggingFace Link |
|-------|------|------|----------|------------------|
| **gpt2** | 117M | ~0.5GB | Testing | `gpt2` |
| **distilgpt2** | 82M | ~0.3GB | Fast testing | `distilgpt2` |
| **microsoft/DialoGPT-small** | 117M | ~0.5GB | Chat | `microsoft/DialoGPT-small` |

### Tier 2: Medium Models (7-14B - Good for H100)
| Model | Size | VRAM | Best For | HuggingFace Link |
|-------|------|------|----------|------------------|
| **meta-llama/Llama-3.2-7B-Instruct** | 7B | ~14GB | General chat/code | `meta-llama/Llama-3.2-7B-Instruct` ⚠️ Gated |
| **Qwen/Qwen2.5-7B-Instruct** | 7B | ~14GB | Multilingual | `Qwen/Qwen2.5-7B-Instruct` ✅ No gate |
| **Qwen/Qwen2.5-Coder-7B-Instruct** | 7B | ~14GB | Coding | `Qwen/Qwen2.5-Coder-7B-Instruct` ✅ No gate |
| **mistralai/Mistral-7B-Instruct-v0.3** | 7B | ~14GB | Efficient chat | `mistralai/Mistral-7B-Instruct-v0.3` ✅ No gate |
| **microsoft/Phi-3-medium-4k-instruct** | 14B | ~28GB | Efficient reasoning | `microsoft/Phi-3-medium-4k-instruct` ✅ No gate |

### Tier 3: Large Models (32-70B - Excellent for H100)
| Model | Size | VRAM | Best For | HuggingFace Link |
|-------|------|------|----------|------------------|
| **Qwen/Qwen2.5-32B-Instruct** | 32B | ~64GB | Advanced chat | `Qwen/Qwen2.5-32B-Instruct` ✅ No gate |
| **Qwen/Qwen2.5-Coder-32B-Instruct** | 32B | ~64GB | Professional coding | `Qwen/Qwen2.5-Coder-32B-Instruct` ✅ No gate |
| **meta-llama/Llama-3.1-70B-Instruct** | 70B | ~140GB | State-of-art | ⚠️ Too big for 80GB (needs quantization) |

### Tier 4: Specialized Models
| Model | Size | VRAM | Best For | HuggingFace Link |
|-------|------|------|----------|------------------|
| **codellama/CodeLlama-13b-Instruct-hf** | 13B | ~26GB | Code generation | `codellama/CodeLlama-13b-Instruct-hf` ⚠️ Gated |
| **codellama/CodeLlama-34b-Instruct-hf** | 34B | ~68GB | Advanced coding | `codellama/CodeLlama-34b-Instruct-hf` ⚠️ Gated |
| **deepseek-ai/deepseek-coder-33b-instruct** | 33B | ~66GB | Code understanding | `deepseek-ai/deepseek-coder-33b-instruct` ✅ No gate |

## 🚀 Top 3 Recommendations for Your Setup

### 1. **Qwen/Qwen2.5-Coder-32B-Instruct** (BEST CHOICE)
```
Model: Qwen/Qwen2.5-Coder-32B-Instruct
Size: 32B parameters (~64GB VRAM)
Pros: Excellent coding, no gate, fits H100 perfectly
```

### 2. **Qwen/Qwen2.5-7B-Instruct** (BALANCED)
```
Model: Qwen/Qwen2.5-7B-Instruct
Size: 7B parameters (~14GB VRAM)
Pros: Fast, multilingual, reliable, room for multitasking
```

### 3. **microsoft/Phi-3-medium-4k-instruct** (EFFICIENT)
```
Model: microsoft/Phi-3-medium-4k-instruct
Size: 14B parameters (~28GB VRAM)
Pros: Excellent reasoning, efficient, Microsoft quality
```

## 📝 How to Load in LM Studio Server

**In the web interface:**
1. Enter model name exactly as shown (without quotes)
2. Click "Load Model"
3. Wait 2-5 minutes for download and loading

**Examples:**
```
Qwen/Qwen2.5-7B-Instruct
Qwen/Qwen2.5-Coder-32B-Instruct
microsoft/Phi-3-medium-4k-instruct
mistralai/Mistral-7B-Instruct-v0.3
```

## ⚠️ Models to AVOID

### ❌ GGUF Models (Won't Work)
- Anything with `-gguf` or `-GGUF` in the name
- `Manojb/Qwen3-4B-toolcalling-gguf-codex`
- `bartowski/*-GGUF`
- `TheBloke/*-GGUF`

### ❌ Gated Models (Need Request Access)
- `meta-llama/*` models (need Meta approval)
- `codellama/*` models (need Meta approval)
- Solution: Request access on HuggingFace, then use your token

### ❌ Too Large for H100 80GB
- Models >70B parameters without quantization
- Mixtral-8x22B (requires 140GB+)

## 🔧 Troubleshooting

### Issue: "Rate limit" error
**Solution**: Already fixed - HF_TOKEN is set in environment

### Issue: "GLIBC" error
**Solution**: Avoid models requiring sentencepiece on CentOS 7
- Use: Qwen, Phi-3, Mistral (no issues)
- Avoid: Some Llama variants

### Issue: "Out of memory"
**Solution**: 
1. Use smaller model (7B instead of 32B)
2. Enable 8-bit loading (add to server)
3. Clear GPU cache first

## 🎯 Quick Start Command

Load a recommended model in the browser:
1. Open http://localhost:8080
2. Type: `Qwen/Qwen2.5-7B-Instruct`
3. Click "Load Model"
4. Wait ~3 minutes
5. Start chatting!

---

**Last Updated**: September 30, 2025  
**Status**: HF Token configured, server running on s1cmp010  
**Next**: Try loading a Qwen model!

