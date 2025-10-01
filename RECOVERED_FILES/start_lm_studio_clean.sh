#!/bin/bash
# Start LM Studio with clean environment and proper CUDA loading

VENV_PATH="/cluster/tufts/datalab/zwu09/envs/lmstudio_clean"

if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Clean environment not found at: $VENV_PATH"
    echo ""
    echo "Please run setup first:"
    echo "  ./setup_clean_env.sh"
    exit 1
fi

cd /cluster/tufts/datalab/zwu09 || exit 1

echo "============================================================"
echo "Starting LM Studio with Clean Environment"
echo "============================================================"
echo ""

# Load CUDA module
echo "📦 Loading CUDA 12.2 module..."
module load cuda/12.2 2>&1 || {
    echo "⚠️  cuda/12.2 not found, trying alternatives..."
    module load cuda/12 2>&1 || module load cuda 2>&1
}

if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | sed -n 's/.*release \([0-9]*\.[0-9]*\).*/\1/p')
    echo "✅ CUDA $CUDA_VERSION loaded"
else
    echo "⚠️  Could not verify CUDA, but continuing..."
fi

echo ""

# Activate environment
echo "🔌 Activating environment: $VENV_PATH"
source "$VENV_PATH/bin/activate"

# Disable user site packages to avoid GLIBC conflicts
export PYTHONNOUSERSITE=1
echo "🔒 Disabled ~/.local packages (PYTHONNOUSERSITE=1)"

# Set LD_LIBRARY_PATH to include CUDA libraries
if [ -n "$CUDA_HOME" ]; then
    export LD_LIBRARY_PATH="$CUDA_HOME/lib64:$LD_LIBRARY_PATH"
    echo "📚 Added CUDA libraries to LD_LIBRARY_PATH"
fi

echo "📁 Working directory: $(pwd)"
echo ""

# Check CUDA availability
echo "🔍 Checking CUDA availability..."
python << 'PYEOF'
import torch
cuda_available = torch.cuda.is_available()
print(f"CUDA Available: {cuda_available}")
if cuda_available:
    print(f"CUDA Version: {torch.version.cuda}")
    print(f"GPU Count: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
else:
    print("⚠️  WARNING: CUDA not detected!")
    print("Server will run in CPU mode (very slow)")
PYEOF

echo ""
echo "============================================================"
echo "🚀 Starting LM Studio Server..."
echo "============================================================"
echo ""

python lm_studio_server_robust_v2.py