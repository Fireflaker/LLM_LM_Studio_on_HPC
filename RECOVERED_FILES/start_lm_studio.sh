#!/bin/bash
# Professional LM Studio Server Startup Script
# Tries multiple Python environments to avoid GLIBC issues

echo "============================================================"
echo "LM Studio Server Startup Script - Enhanced Debug Version"
echo "============================================================"
echo ""

# CRITICAL: Disable user-installed packages that may have GLIBC issues
export PYTHONNOUSERSITE=1
echo "🔒 Disabled ~/.local packages (PYTHONNOUSERSITE=1)"

# Navigate to datalab
cd /cluster/tufts/datalab/zwu09 || exit 1

SERVER_SCRIPT="lm_studio_server_robust_v2.py"

if [ ! -f "$SERVER_SCRIPT" ]; then
    echo "❌ Error: $SERVER_SCRIPT not found in $(pwd)"
    exit 1
fi

echo "📁 Working directory: $(pwd)"
echo "🔍 Found server script: $SERVER_SCRIPT"
echo ""

# Function to try running with a Python interpreter
try_python() {
    local python_bin=$1
    local python_name=$2
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Testing: $python_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ ! -f "$python_bin" ]; then
        echo "  ❌ Binary not found: $python_bin"
        return 1
    fi
    
    # Check version
    echo "  🐍 Binary: $python_bin"
    local version=$($python_bin --version 2>&1)
    echo "  📦 Version: $version"
    
    # Check CUDA support
    echo "  🔍 Testing CUDA detection..."
    local cuda_test=$($python_bin -c "import torch; print('CUDA:', torch.cuda.is_available(), 'GPUs:', torch.cuda.device_count() if torch.cuda.is_available() else 0)" 2>&1)
    echo "  $cuda_test"
    
    # Try to import required modules
    echo "  🔍 Testing imports (torch, transformers, flask)..."
    $python_bin -c "import torch; import transformers; import flask; print('  ✅ All imports successful')" 2>&1
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "╔════════════════════════════════════════════════════════════╗"
        echo "║  ✅ Compatible Python Found: $python_name"
        echo "╚════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Starting server..."
        echo ""
        exec $python_bin $SERVER_SCRIPT
    else
        echo "  ❌ Import test failed"
        return 1
    fi
}

# Try different Python interpreters in order of preference
echo "🔍 Searching for compatible Python interpreter..."
echo ""

# Check if nvidia-smi shows GPUs
echo "🔍 GPU Detection Check:"
if command -v nvidia-smi &> /dev/null; then
    echo "  nvidia-smi found, checking GPUs..."
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | nl -v 0 | sed 's/^/  GPU /'
else
    echo "  ⚠️  nvidia-smi not found"
fi
echo ""

# 1. Try Anaconda Python 3.11 (usually has better CUDA support)
try_python "/cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11" "Anaconda Python 3.11"

# 2. Try system Python 3.11
try_python "/usr/bin/python3.11" "System Python 3.11"

# 3. Try system Python 3.9 (often more compatible)
try_python "/usr/bin/python3.9" "System Python 3.9"

# 4. Try system Python 3
try_python "/usr/bin/python3" "System Python 3"

# 5. Try Python from PATH
if command -v python3 &> /dev/null; then
    try_python "$(command -v python3)" "PATH Python 3"
fi

# If we get here, nothing worked
echo ""
echo "============================================================"
echo "❌ CRITICAL: No compatible Python environment found!"
echo "============================================================"
echo ""
echo "The GLIBC version issue prevents transformers from loading."
echo ""
echo "📋 Recommended solutions:"
echo ""
echo "1. Create a fresh virtual environment:"
echo "   python3 -m venv /cluster/tufts/datalab/zwu09/envs/lmstudio"
echo "   source /cluster/tufts/datalab/zwu09/envs/lmstudio/bin/activate"
echo "   pip install torch transformers flask psutil"
echo "   python lm_studio_server_robust_v2.py"
echo ""
echo "2. Use conda environment:"
echo "   module load anaconda/2023.07-1"
echo "   conda create -n lmstudio python=3.10 -y"
echo "   conda activate lmstudio"
echo "   pip install torch transformers flask psutil"
echo "   python lm_studio_server_robust_v2.py"
echo ""
echo "3. Try system Python directly:"
echo "   /usr/bin/python3 -m pip install --user torch transformers flask psutil"
echo "   /usr/bin/python3 lm_studio_server_robust_v2.py"
echo ""
exit 1
