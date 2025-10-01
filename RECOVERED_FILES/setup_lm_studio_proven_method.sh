#!/bin/bash
# LM Studio Setup - Using Proven Working Method from Your Notes
# Based on successful llm-dfuse-env approach
# DO NOT LOAD ANY MODULES - they are broken

echo "============================================================"
echo "LM Studio Setup - Proven Working Method"
echo "============================================================"
echo ""
echo "Following your successful approach from llm-dfuse-env"
echo "This will work because:"
echo "  1. Uses conda (not modules)"
echo "  2. No module loading"
echo "  3. Fresh environment in datalab"
echo ""

# Step 1: Navigate to datalab
echo "Step 1: Navigate to datalab storage"
cd /cluster/tufts/datalab/zwu09 || exit 1
pwd
echo ""

# Step 2: Initialize conda
echo "Step 2: Initializing conda"
echo "Checking for conda..."

# Try different conda locations
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
    echo ""
    echo "Or if using miniconda:"
    echo "  source ~/miniconda3/etc/profile.d/conda.sh"
    exit 1
fi

conda --version
echo "✅ Conda initialized"
echo ""

# Step 3: Create envs directory if needed
echo "Step 3: Ensure envs directory exists"
mkdir -p envs
cd envs
pwd
echo ""

# Step 4: Create conda environment
echo "Step 4: Creating conda environment 'lmstudio' with Python 3.11"
echo "Command: conda create -n lmstudio python=3.11 -y"
echo ""
read -p "Press Enter to run this command..."
conda create -n lmstudio python=3.11 -y

if [ $? -ne 0 ]; then
    echo "❌ Failed to create conda environment"
    exit 1
fi

echo ""
echo "✅ Conda environment created"
echo ""

# Step 5: Activate environment
echo "Step 5: Activating environment"
echo "Command: conda activate lmstudio"
echo ""
read -p "Press Enter to continue..."
conda activate lmstudio

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate environment"
    exit 1
fi

echo "✅ Environment activated"
echo "Current Python: $(which python)"
python --version
echo ""

# Step 6: Upgrade pip
echo "Step 6: Upgrading pip, setuptools, wheel"
echo "Command: pip install --upgrade pip setuptools wheel"
echo ""
read -p "Press Enter to continue..."
pip install --upgrade pip setuptools wheel

echo "✅ pip upgraded"
echo ""

# Step 7: Install PyTorch with CUDA 12.1
echo "Step 7: Installing PyTorch with CUDA 12.1 support"
echo "Command: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
echo ""
echo "This will take a few minutes..."
read -p "Press Enter to continue..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

if [ $? -ne 0 ]; then
    echo "❌ Failed to install PyTorch"
    exit 1
fi

echo "✅ PyTorch installed"
echo ""

# Step 8: Install transformers, flask, psutil
echo "Step 8: Installing transformers, flask, psutil"
echo "Command: pip install transformers flask psutil"
echo ""
read -p "Press Enter to continue..."
pip install transformers flask psutil

if [ $? -ne 0 ]; then
    echo "❌ Failed to install packages"
    exit 1
fi

echo "✅ Packages installed"
echo ""

# Step 9: Test CUDA detection
echo "Step 9: Testing CUDA detection"
echo ""
python << 'PYEOF'
import torch
print(f"✅ PyTorch version: {torch.__version__}")
print(f"✅ CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"✅ CUDA version: {torch.version.cuda}")
    print(f"✅ GPU count: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
else:
    print("⚠️  CUDA not detected")
PYEOF

echo ""
echo "============================================================"
echo "✅ Setup complete!"
echo "============================================================"
echo ""
echo "To use this environment:"
echo "  conda activate lmstudio"
echo "  python lm_studio_server_robust_v2.py"
echo ""
echo "Or use the start script:"
echo "  ./start_lm_studio_proven.sh"
echo ""
