#!/bin/bash
# vLLM Setup Script for A100 GPUs
# Requirements: Python 3.11/3.12, CUDA 12.2, PyTorch with CUDA 12.2

echo "=== vLLM Setup for A100 GPUs ==="

# Set up RAM disk for temporary operations
export TMPDIR=/tmp/vllm_setup
export PIP_CACHE_DIR=/tmp/vllm_setup/pip_cache
mkdir -p $TMPDIR $PIP_CACHE_DIR

echo "RAM disk set up at: $TMPDIR"

# Check system status
echo "=== System Check ==="
echo "Node: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"
echo "GPUs: $CUDA_VISIBLE_DEVICES"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader,nounits

# Check available Python versions
echo "=== Python Versions ==="
python3.11 --version 2>/dev/null && echo "Python 3.11 available" || echo "Python 3.11 not available"
python3.12 --version 2>/dev/null && echo "Python 3.12 available" || echo "Python 3.12 not available"

# Create new environment with Python 3.11 or 3.12
PYTHON_CMD=""
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo "Using Python 3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    echo "Using Python 3.11"
else
    echo "ERROR: Neither Python 3.11 nor 3.12 available"
    exit 1
fi

# Create virtual environment
VENV_PATH="/cluster/tufts/datalab/zwu09/envs/vllm"
echo "Creating virtual environment at: $VENV_PATH"
$PYTHON_CMD -m venv $VENV_PATH

# Activate environment
source $VENV_PATH/bin/activate
echo "Environment activated"

# Upgrade pip
pip install --upgrade pip

# Install PyTorch with CUDA 12.2 support
echo "=== Installing PyTorch with CUDA 12.2 ==="
pip install --cache-dir $PIP_CACHE_DIR torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Verify PyTorch installation
echo "=== Verifying PyTorch ==="
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda}'); print(f'GPU Count: {torch.cuda.device_count()}')"

# Install vLLM
echo "=== Installing vLLM ==="
pip install --cache-dir $PIP_CACHE_DIR vllm

# Install additional dependencies
echo "=== Installing Additional Dependencies ==="
pip install --cache-dir $PIP_CACHE_DIR transformers accelerate

# Test vLLM installation
echo "=== Testing vLLM ==="
python -c "import vllm; print('vLLM imported successfully')"

# Create Jupyter kernel
echo "=== Creating Jupyter Kernel ==="
python -m ipykernel install --user --name vllm --display-name "vLLM (Python $($PYTHON_CMD --version | cut -d' ' -f2))"

echo "=== Setup Complete ==="
echo "Environment: $VENV_PATH"
echo "To activate: source $VENV_PATH/bin/activate"
echo "Jupyter kernel: vLLM"

