#!/bin/bash
# LM Studio v3 Setup - Using Proven Conda Method
# Based on successful approaches from your notes

echo "============================================================"
echo "LM Studio v3 Setup - Proven Conda Method"
echo "============================================================"
echo ""
echo "This setup uses conda directly (no modules) to avoid GLIBC issues"
echo ""

# Step 1: Navigate to datalab
echo "Step 1: Navigate to datalab storage"
cd /cluster/tufts/datalab/zwu09 || exit 1
pwd
echo ""

# Step 2: Initialize conda
echo "Step 2: Initializing conda"
if [ -f "/cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh" ]; then
    echo "Found Anaconda 2023.07"
    source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    echo "Found Miniconda in home"
    source $HOME/miniconda3/etc/profile.d/conda.sh
elif command -v conda &> /dev/null; then
    echo "Conda already available"
else
    echo "❌ Conda not found!"
    echo ""
    echo "Please run one of these first:"
    echo "  source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh"
    exit 1
fi

conda --version
echo "✅ Conda initialized"
echo ""

# Step 3: Create environment
echo "Step 3: Creating conda environment 'lmstudio_v3' with Python 3.11"
echo "This will create a fresh environment to avoid conflicts"
echo ""

# Remove old environment if it exists
if [ -d "envs/lmstudio_v3" ]; then
    echo "🗑️  Removing old environment..."
    rm -rf envs/lmstudio_v3
fi

# Create new environment
conda create -n lmstudio_v3 python=3.11 -y

if [ $? -ne 0 ]; then
    echo "❌ Failed to create conda environment"
    exit 1
fi

echo "✅ Conda environment created"
echo ""

# Step 4: Activate environment
echo "Step 4: Activating environment"
conda activate lmstudio_v3

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate environment"
    exit 1
fi

echo "✅ Environment activated"
echo "Current Python: $(which python)"
python --version
echo ""

# Step 5: Upgrade pip and install basic packages
echo "Step 5: Upgrading pip and installing basic packages"
pip install --upgrade pip setuptools wheel

echo "✅ pip upgraded"
echo ""

# Step 6: Install PyTorch with CUDA 12.1
echo "Step 6: Installing PyTorch with CUDA 12.1 support"
echo "This will take a few minutes..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

if [ $? -ne 0 ]; then
    echo "❌ Failed to install PyTorch"
    exit 1
fi

echo "✅ PyTorch installed"
echo ""

# Step 7: Install other packages
echo "Step 7: Installing transformers, flask, psutil"
pip install transformers flask psutil

if [ $? -ne 0 ]; then
    echo "❌ Failed to install packages"
    exit 1
fi

echo "✅ Packages installed"
echo ""

# Step 8: Test installation
echo "Step 8: Testing installation"
echo ""

python << 'PYEOF'
import sys
import torch
import flask
import psutil

print(f"✅ Python: {sys.version}")
print(f"✅ PyTorch: {torch.__version__}")
print(f"✅ Flask: {flask.__version__}")
print(f"✅ psutil: {psutil.__version__}")
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

print()
print("Testing transformers import...")
try:
    import transformers
    print(f"✅ Transformers: {transformers.__version__}")
    print("✅ Transformers import successful!")
except Exception as e:
    print(f"❌ Transformers import failed: {e}")
    print("   This is likely due to GLIBC issues")
    print("   Server will run in demo mode")
PYEOF

echo ""
echo "============================================================"
echo "✅ Setup complete!"
echo "============================================================"
echo ""
echo "To use this environment:"
echo "  conda activate lmstudio_v3"
echo "  python lm_studio_server_v3_improved.py"
echo ""
echo "Or use the start script:"
echo "  ./start_lm_studio_v3.sh"
echo ""
echo "If transformers failed, you can still use:"
echo "  python simple_lm_studio.py"
echo ""
