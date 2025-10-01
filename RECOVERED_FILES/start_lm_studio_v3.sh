#!/bin/bash
# Start LM Studio v3 with improved error handling

echo "============================================================"
echo "Starting LM Studio v3 - Improved"
echo "============================================================"
echo ""

cd /cluster/tufts/datalab/zwu09 || exit 1

# Initialize conda
echo "🔌 Initializing conda..."
if [ -f "/cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh" ]; then
    source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source $HOME/miniconda3/etc/profile.d/conda.sh
fi

# Activate the environment
echo "🔌 Activating conda environment: lmstudio_v3"
conda activate lmstudio_v3

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate environment"
    echo ""
    echo "Please run setup first:"
    echo "  ./setup_lm_studio_v3.sh"
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

# Check if transformers works
echo "🔍 Checking transformers..."
python -c "
try:
    import transformers
    print(f'✅ Transformers: {transformers.__version__}')
    print('✅ Full mode available')
except Exception as e:
    print(f'⚠️  Transformers failed: {e}')
    print('⚠️  Will run in demo mode')
"
echo ""

echo "============================================================"
echo "🚀 Starting LM Studio Server v3..."
echo "============================================================"
echo ""

# Try the improved server first
python lm_studio_server_v3_improved.py
