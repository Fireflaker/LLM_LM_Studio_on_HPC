#!/bin/bash
# ONE COMMAND to start everything on compute node
# Run this after you have a compute node allocated

cd /cluster/tufts/datalab/zwu09 && \
source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh && \
conda activate lmstudio_v3 && \
export PYTHONNOUSERSITE=1 && \
export HF_HOME=/cluster/tufts/datalab/zwu09/caches/huggingface && \
export TRANSFORMERS_CACHE=/cluster/tufts/datalab/zwu09/caches/huggingface && \
export TORCH_HOME=/cluster/tufts/datalab/zwu09/caches/torch && \
export TMPDIR=/cluster/tufts/datalab/zwu09/tmp && \
echo "============================================================" && \
echo "Starting LM Studio Server v3" && \
echo "============================================================" && \
echo "Compute Node: $(hostname)" && \
echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)" && \
echo "" && \
echo "📡 Create tunnel from laptop:" && \
echo "   ssh -J zwu09@login.pax.tufts.edu -L 8080:127.0.0.1:8080 zwu09@$(hostname)" && \
echo "" && \
echo "🌐 Access: http://localhost:8080" && \
echo "============================================================" && \
echo "" && \
python lm_studio_server_v3_improved.py

