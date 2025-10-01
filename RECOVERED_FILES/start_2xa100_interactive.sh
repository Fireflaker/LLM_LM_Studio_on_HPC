#!/bin/bash
# Interactive session request for 2x A100, 40 CPU, 40GB RAM
# Usage: ./start_2xa100_interactive.sh

echo "Requesting interactive session with 2x A100 GPUs, 40 CPUs, 40GB RAM..."
echo "This will start an interactive shell on a compute node."
echo ""

# Request interactive resources
srun -p gpu --gres=gpu:a100:2 -c 40 --mem=40G -t 02:00:00 --pty bash -c "
echo '=== Interactive Session Started ==='
echo 'Job ID: $SLURM_JOB_ID'
echo 'Node: $(hostname)'
echo 'CPUs: $SLURM_CPUS_PER_TASK'
echo 'Memory: $SLURM_MEM_PER_NODE MB'
echo 'GPUs: $CUDA_VISIBLE_DEVICES'
echo ''

# Set up environment
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
export JUPYTER_RUNTIME_DIR=\$DATALAB_BASE/tmp/jupyter
export TMPDIR=\$DATALAB_BASE/tmp
export HF_HOME=\$DATALAB_BASE/caches/huggingface
export TRANSFORMERS_CACHE=\$DATALAB_BASE/caches/huggingface
export PIP_CACHE_DIR=\$DATALAB_BASE/caches/pip
export TORCH_HOME=\$DATALAB_BASE/caches/torch

# Create directories
mkdir -p \"\$JUPYTER_RUNTIME_DIR\" \"\$TMPDIR\" \"\$HF_HOME\" \"\$TRANSFORMERS_CACHE\" \"\$PIP_CACHE_DIR\" \"\$TORCH_HOME\"

# Activate environment
source \$DATALAB_BASE/envs/hoc/bin/activate

echo '=== GPU Information ==='
nvidia-smi -L || echo 'nvidia-smi not available'
echo ''

echo '=== Python Environment ==='
python -c \"import torch, sys; print('torch:', torch.__version__, 'cuda:', torch.version.cuda, 'is_cuda_available:', torch.cuda.is_available()); print('Python:', sys.version)\"
echo ''

echo '=== To start Jupyter Lab, run: ==='
echo 'jupyter lab --no-browser --ip 127.0.0.1 --port 8891 --ServerApp.token=allen --NotebookApp.notebook_dir=\$DATALAB_BASE'
echo ''
echo '=== Then on your laptop, run: ==='
echo \"ssh -J zwu09@login.pax.tufts.edu -L 8891:127.0.0.1:8891 zwu09@\$(hostname)\"
echo ''
echo '=== Set Jupyter server URL in Cursor to: ==='
echo 'http://localhost:8891/?token=allen'
echo ''

# Start interactive bash
exec bash
"

