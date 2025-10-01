#!/usr/bin/env python3
"""
Test loading a proper big model (non-GGUF)
Run this on HPC to test loading Qwen2.5-7B-Instruct
"""

import os
# Set your HuggingFace token here (get from https://huggingface.co/settings/tokens)
os.environ['HF_TOKEN'] = 'YOUR_HF_TOKEN_HERE'
os.environ['HF_HOME'] = '/cluster/tufts/datalab/zwu09/caches/huggingface'
os.environ['TRANSFORMERS_CACHE'] = '/cluster/tufts/datalab/zwu09/caches/huggingface'
os.environ['TORCH_HOME'] = '/cluster/tufts/datalab/zwu09/caches/torch'

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

print("="*60)
print("Testing Big Model Loading")
print("="*60)

# Test model - Qwen2.5-7B-Instruct (NOT GGUF!)
model_name = "Qwen/Qwen2.5-7B-Instruct"

print(f"\nModel: {model_name}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

print("\n" + "="*60)
print("Step 1: Loading tokenizer...")
print("="*60)

try:
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        token=os.environ['HF_TOKEN']
    )
    print("✅ Tokenizer loaded successfully!")
except Exception as e:
    print(f"❌ Tokenizer failed: {e}")
    exit(1)

print("\n" + "="*60)
print("Step 2: Loading model (this will take 3-5 minutes)...")
print("="*60)

try:
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        low_cpu_mem_usage=True,
        trust_remote_code=True,
        token=os.environ['HF_TOKEN']
    )
    print("✅ Model loaded successfully!")
    
    # Check memory usage
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated(0) / 1e9
        total = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"\nGPU Memory: {allocated:.1f}GB / {total:.1f}GB ({allocated/total*100:.1f}%)")
    
except Exception as e:
    print(f"❌ Model loading failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*60)
print("Step 3: Testing generation...")
print("="*60)

test_prompt = "Write a Python function to calculate fibonacci numbers:"
inputs = tokenizer(test_prompt, return_tensors="pt").to("cuda")

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=100,
        temperature=0.7,
        do_sample=True
    )

generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"\nPrompt: {test_prompt}")
print(f"\nGenerated:\n{generated_text}")

print("\n" + "="*60)
print("✅ ALL TESTS PASSED!")
print("="*60)
print("\nThe model works! You can now load it in the web interface:")
print(f"  Model name: {model_name}")
print(f"  Access: http://localhost:8080")

