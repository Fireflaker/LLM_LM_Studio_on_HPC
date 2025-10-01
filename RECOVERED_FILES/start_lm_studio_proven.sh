#!/bin/bash
# Start LM Studio using proven working conda environment

echo "============================================================"
echo "Starting LM Studio with Proven Method"
echo "============================================================"
echo ""

cd /cluster/tufts/datalab/zwu09 || exit 1

# Initialize conda first
echo "🔌 Initializing conda..."
if [ -f "/cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh" ]; then
    source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source $HOME/miniconda3/etc/profile.d/conda.sh
fi

# Activate the working conda environment
echo "🔌 Activating conda environment: lmstudio"
conda activate lmstudio

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate environment"
    echo ""
    echo "Please run setup first:"
    echo "  ./setup_lm_studio_proven_method.sh"
    exit 1
fi

# Disable user site packages to avoid conflicts
export PYTHONNOUSERSITE=1
echo "🔒 Disabled ~/.local packages"

echo "🐍 Python: $(which python)"
python --version
echo ""

# Quick CUDA check
echo "🔍 Checking CUDA..."
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPUs: {torch.cuda.device_count()}')"
echo ""

echo "============================================================"
echo "🚀 Starting LM Studio Server..."
echo "============================================================"
echo ""

python lm_studio_server_robust_v2.py
