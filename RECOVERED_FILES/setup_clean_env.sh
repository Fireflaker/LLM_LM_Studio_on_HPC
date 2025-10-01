#!/bin/bash
# Professional LM Studio Environment Setup for Tufts HPC
# Properly loads CUDA modules and creates clean environment

echo "============================================================"
echo "LM Studio Clean Environment Setup - Professional Edition"
echo "============================================================"
echo ""

cd /cluster/tufts/datalab/zwu09 || exit 1

VENV_PATH="/cluster/tufts/datalab/zwu09/envs/lmstudio_clean"

echo "This will create a fresh Python environment at:"
echo "  $VENV_PATH"
echo ""
echo "This avoids GLIBC conflicts from ~/.local packages"
echo ""

# ============================================================
# Step 1: Load Required Modules
# ============================================================
echo "📦 Loading HPC modules..."
echo ""

# List available CUDA modules
echo "Available CUDA modules:"
module avail cuda 2>&1 | grep -i cuda | head -10
echo ""

# Load CUDA 12.2
echo "Loading CUDA 12.2..."
module load cuda/12.2 2>&1 || {
    echo "⚠️  cuda/12.2 not found, trying alternatives..."
    module load cuda/12 2>&1 || module load cuda 2>&1 || {
        echo "❌ Could not load CUDA module"
        echo "Available modules:"
        module avail 2>&1 | grep -i cuda
        exit 1
    }
}

# Verify CUDA loaded
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | sed -n 's/.*release \([0-9]*\.[0-9]*\).*/\1/p')
    echo "✅ CUDA $CUDA_VERSION loaded successfully"
    echo "  nvcc: $(which nvcc)"
    echo "  CUDA_HOME: $CUDA_HOME"
else
    echo "❌ nvcc not found after loading module"
    exit 1
fi

echo ""

# ============================================================
# Step 2: Setup Python Environment
# ============================================================
PYTHON_BIN="/cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "❌ Anaconda Python not found at $PYTHON_BIN"
    echo "Trying system python3..."
    PYTHON_BIN="/usr/bin/python3"
fi

echo "Using Python: $PYTHON_BIN"
$PYTHON_BIN --version
echo ""

# Remove old environment if it exists
if [ -d "$VENV_PATH" ]; then
    echo "🗑️  Removing old environment..."
    rm -rf "$VENV_PATH"
fi

# Create new virtual environment
echo "📦 Creating virtual environment..."
$PYTHON_BIN -m venv "$VENV_PATH"

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

# Activate environment
echo "🔌 Activating environment..."
source "$VENV_PATH/bin/activate"

# Upgrade pip
echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip --quiet

echo ""

# ============================================================
# Step 3: Install PyTorch with correct CUDA version
# ============================================================
echo "📥 Installing PyTorch with CUDA $CUDA_VERSION support..."
echo ""

# Determine PyTorch index URL
if [[ "$CUDA_VERSION" == 12.2* ]] || [[ "$CUDA_VERSION" == 12.1* ]] || [[ "$CUDA_VERSION" == 12.* ]]; then
    TORCH_INDEX="https://download.pytorch.org/whl/cu121"
    echo "  Using PyTorch for CUDA 12.1 (compatible with 12.2)"
elif [[ "$CUDA_VERSION" == 11.8* ]] || [[ "$CUDA_VERSION" == 11.* ]]; then
    TORCH_INDEX="https://download.pytorch.org/whl/cu118"
    echo "  Using PyTorch for CUDA 11.8"
else
    TORCH_INDEX="https://download.pytorch.org/whl/cu121"
    echo "  Defaulting to PyTorch for CUDA 12.1"
fi

# Install PyTorch (this will take a few minutes)
python -m pip install torch torchvision torchaudio --index-url $TORCH_INDEX

if [ $? -ne 0 ]; then
    echo "❌ PyTorch installation failed"
    exit 1
fi

echo "✅ PyTorch installed"
echo ""

# ============================================================
# Step 4: Install Other Required Packages
# ============================================================
echo "📥 Installing transformers, flask, psutil..."
python -m pip install transformers flask psutil --quiet

if [ $? -ne 0 ]; then
    echo "❌ Package installation failed"
    exit 1
fi

echo "✅ All packages installed"
echo ""

# ============================================================
# Step 5: Verify Installation
# ============================================================
echo "🔍 Verifying installation..."
echo ""

python << 'PYEOF'
import sys
import torch
import transformers
import flask

print(f"✅ Python: {sys.version}")
print(f"✅ PyTorch: {torch.__version__}")
print(f"✅ Transformers: {transformers.__version__}")
print(f"✅ Flask: {flask.__version__}")
print()
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA Version: {torch.version.cuda}")
    print(f"GPU Count: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
        props = torch.cuda.get_device_properties(i)
        print(f"    Memory: {props.total_memory / 1e9:.1f} GB")
else:
    print("⚠️  WARNING: CUDA not detected!")
PYEOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Verification failed"
    exit 1
fi

echo ""
echo "============================================================"
echo "✅ Environment setup complete!"
echo "============================================================"
echo ""
echo "Loaded modules:"
module list 2>&1 | grep -v "^$"
echo ""
echo "To use this environment, run:"
echo "  ./start_lm_studio_clean.sh"
echo ""
echo "Or manually:"
echo "  module load cuda/12.2"
echo "  source $VENV_PATH/bin/activate"
echo "  export PYTHONNOUSERSITE=1"
echo "  python lm_studio_server_robust_v2.py"
echo ""