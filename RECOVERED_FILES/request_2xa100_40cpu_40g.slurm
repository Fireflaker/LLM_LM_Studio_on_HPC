#!/bin/bash
#SBATCH --job-name=2xa100-40cpu-40g
#SBATCH --partition=gpu
#SBATCH --gres=gpu:a100:2
#SBATCH --cpus-per-task=40
#SBATCH --mem=40G
#SBATCH --time=02:00:00
#SBATCH --output=/cluster/tufts/datalab/zwu09/logs/%j.out
#SBATCH --error=/cluster/tufts/datalab/zwu09/logs/%j.err

# Create logs directory if it doesn't exist
mkdir -p /cluster/tufts/datalab/zwu09/logs

# Set up environment and paths
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
export JUPYTER_RUNTIME_DIR=$DATALAB_BASE/tmp/jupyter
export TMPDIR=$DATALAB_BASE/tmp
export HF_HOME=$DATALAB_BASE/caches/huggingface
export TRANSFORMERS_CACHE=$DATALAB_BASE/caches/huggingface
export PIP_CACHE_DIR=$DATALAB_BASE/caches/pip
export TORCH_HOME=$DATALAB_BASE/caches/torch

# Create necessary directories
mkdir -p "$JUPYTER_RUNTIME_DIR" "$TMPDIR" "$HF_HOME" "$TRANSFORMERS_CACHE" "$PIP_CACHE_DIR" "$TORCH_HOME"

# Activate the HPC environment
source $DATALAB_BASE/envs/hoc/bin/activate

# Display system information
echo "=== Job Information ==="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory: $SLURM_MEM_PER_NODE MB"
echo "GPUs: $CUDA_VISIBLE_DEVICES"
echo "Working Directory: $(pwd)"
echo ""

echo "=== GPU Information ==="
nvidia-smi -L || echo "nvidia-smi not available"
echo ""

echo "=== Python Environment ==="
python -c "import torch, sys; print('torch:', torch.__version__, 'cuda:', torch.version.cuda, 'is_cuda_available:', torch.cuda.is_available()); print('Python:', sys.version)"
echo ""

echo "=== Storage Information ==="
df -h /cluster/tufts/datalab
echo ""

echo "=== Starting Jupyter Lab ==="
echo "NODE=$(hostname)"
echo "To connect from your laptop, run:"
echo "ssh -J zwu09@login.pax.tufts.edu -L 8891:127.0.0.1:8891 zwu09@$(hostname)"
echo "Then set Jupyter server URL in Cursor to: http://localhost:8891/?token=allen"
echo ""

# Launch Jupyter Lab
jupyter lab --no-browser --ip 127.0.0.1 --port 8891 \
  --ServerApp.token=allen \
  --NotebookApp.notebook_dir=$DATALAB_BASE \
  --ServerApp.allow_origin='*' \
  --ServerApp.disable_check_xsrf=True

