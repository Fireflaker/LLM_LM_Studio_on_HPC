#!/bin/bash
# Run these commands AFTER you get a compute node
# This sets up LM Studio completely

echo "============================================================"
echo "🖥️  Setting up LM Studio on Compute Node"
echo "============================================================"
echo ""

# Verify we're on a compute node
echo "Step 1: Verifying compute node..."
HOSTNAME=$(hostname)
echo "Current hostname: $HOSTNAME"

if [[ "$SLURM_JOB_ID" == "" ]]; then
    echo "⚠️  WARNING: Not on a compute node (no SLURM_JOB_ID)"
    echo "Please run: srun -p preempt --gres=gpu:h100:1 -c 40 --mem=100G -t 04:00:00 --pty bash"
    echo ""
    read -p "Continue anyway? (y/n): " continue_setup
    if [[ "$continue_setup" != "y" ]]; then
        exit 1
    fi
else
    echo "✅ Running on compute node: $HOSTNAME"
    echo "Job ID: $SLURM_JOB_ID"
fi
echo ""

# Step 2: Verify GPU
echo "Step 2: Verifying GPU allocation..."
nvidia-smi
if [ $? -ne 0 ]; then
    echo "❌ GPU not available!"
    exit 1
fi
echo "✅ GPU verified"
echo ""

# Step 3: Navigate to datalab
echo "Step 3: Navigating to datalab..."
cd /cluster/tufts/datalab/zwu09 || exit 1
pwd
echo "✅ In datalab directory"
echo ""

# Step 4: Initialize conda (DO NOT LOAD MODULES!)
echo "Step 4: Initializing conda..."
echo "⚠️  Using conda directly - NOT loading any modules"
source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh

if [ $? -ne 0 ]; then
    echo "❌ Failed to initialize conda"
    exit 1
fi

conda --version
echo "✅ Conda initialized"
echo ""

# Step 5: Check if environment exists
echo "Step 5: Checking for existing lmstudio_v3 environment..."
if conda env list | grep -q "lmstudio_v3"; then
    echo "Found existing lmstudio_v3 environment"
    read -p "Do you want to recreate it? (y/n): " recreate_env
    if [[ "$recreate_env" == "y" ]]; then
        echo "Removing old environment..."
        conda env remove -n lmstudio_v3 -y
        echo "✅ Old environment removed"
    fi
else
    echo "No existing environment found"
fi
echo ""

# Step 6: Create or use existing environment
if ! conda env list | grep -q "lmstudio_v3"; then
    echo "Step 6: Creating fresh conda environment..."
    conda create -n lmstudio_v3 python=3.11 -y
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create conda environment"
        exit 1
    fi
    echo "✅ Environment created"
else
    echo "Step 6: Using existing environment"
fi
echo ""

# Step 7: Activate environment
echo "Step 7: Activating environment..."
conda activate lmstudio_v3

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate environment"
    exit 1
fi

echo "✅ Environment activated"
echo "Python: $(which python)"
python --version
echo ""

# Step 8: Set environment variables (disable user site packages)
echo "Step 8: Setting environment variables..."
export PYTHONNOUSERSITE=1
export HF_HOME=/cluster/tufts/datalab/zwu09/caches/huggingface
export TRANSFORMERS_CACHE=/cluster/tufts/datalab/zwu09/caches/huggingface
export TORCH_HOME=/cluster/tufts/datalab/zwu09/caches/torch
export TMPDIR=/cluster/tufts/datalab/zwu09/tmp

# Create directories
mkdir -p "$HF_HOME" "$TRANSFORMERS_CACHE" "$TORCH_HOME" "$TMPDIR"
echo "✅ Environment variables set"
echo ""

# Step 9: Upgrade pip
echo "Step 9: Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo "✅ pip upgraded"
echo ""

# Step 10: Check if PyTorch is installed
echo "Step 10: Checking PyTorch installation..."
if python -c "import torch" 2>/dev/null; then
    echo "PyTorch already installed"
    python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
    read -p "Reinstall PyTorch? (y/n): " reinstall_pytorch
else
    reinstall_pytorch="y"
fi

if [[ "$reinstall_pytorch" == "y" ]]; then
    echo "Installing PyTorch with CUDA 12.1..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install PyTorch"
        exit 1
    fi
    echo "✅ PyTorch installed"
fi
echo ""

# Step 11: Install other packages
echo "Step 11: Installing Flask, psutil, accelerate..."
pip install flask psutil accelerate

if [ $? -ne 0 ]; then
    echo "❌ Failed to install packages"
    exit 1
fi
echo "✅ Packages installed"
echo ""

# Step 12: Install transformers (may fail on GLIBC)
echo "Step 12: Installing transformers..."
echo "⚠️  This may fail due to GLIBC issues - that's OK, server has fallback"
pip install transformers || echo "⚠️  Transformers installation failed (expected on CentOS 7)"
echo ""

# Step 13: Verify installation
echo "Step 13: Verifying installation..."
echo ""
python << 'PYEOF'
import sys
import torch

print("="*60)
print("Installation Verification")
print("="*60)
print(f"✅ Python: {sys.version}")
print(f"✅ PyTorch: {torch.__version__}")
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
    print("✅ Full mode available")
except Exception as e:
    print(f"⚠️  Transformers failed: {e}")
    print("⚠️  Server will run in demo mode")

print()
print("Testing Flask...")
try:
    import flask
    print(f"✅ Flask: {flask.__version__}")
except Exception as e:
    print(f"❌ Flask failed: {e}")

print("="*60)
PYEOF

echo ""
echo "============================================================"
echo "✅ Setup Complete!"
echo "============================================================"
echo ""
echo "Compute Node: $HOSTNAME"
echo "Job ID: $SLURM_JOB_ID"
echo ""
echo "🚀 To start LM Studio server, run:"
echo "   python lm_studio_server_v3_improved.py"
echo ""
echo "Or use the start script:"
echo "   ./start_lm_studio_v3.sh"
echo ""
echo "📡 Then create SSH tunnel from your laptop:"
echo "   ssh -J zwu09@login.pax.tufts.edu -L 8080:127.0.0.1:8080 zwu09@$HOSTNAME"
echo ""
echo "🌐 Access in browser: http://localhost:8080"
echo ""
echo "============================================================"

