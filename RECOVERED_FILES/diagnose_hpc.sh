#!/bin/bash
# HPC Environment Diagnostic Tool

echo "============================================================"
echo "HPC Environment Diagnostics"
echo "============================================================"
echo ""

echo "📍 Current Location:"
echo "  PWD: $(pwd)"
echo "  User: $USER"
echo "  Hostname: $(hostname)"
echo ""

echo "📦 Available Modules:"
echo "  Searching for CUDA modules..."
module avail cuda 2>&1 | grep -i cuda || echo "  No CUDA modules found"
echo ""

echo "🔍 Loaded Modules:"
module list 2>&1 || echo "  No modules currently loaded"
echo ""

echo "🐍 Python Environments:"
echo "  System Python:"
which python3 && python3 --version
echo ""
echo "  Anaconda Python:"
/cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11 --version 2>/dev/null && \
    echo "  Location: /cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11" || \
    echo "  Not found"
echo ""

echo "🎮 GPU Status:"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free --format=csv
else
    echo "  nvidia-smi not found"
fi
echo ""

echo "💾 Storage:"
echo "  Datalab:"
df -h /cluster/tufts/datalab/zwu09 2>/dev/null | tail -1 || echo "  Not accessible"
echo "  Home:"
df -h ~ | tail -1
echo ""

echo "📚 Environment Variables:"
echo "  CUDA_HOME: ${CUDA_HOME:-<not set>}"
echo "  LD_LIBRARY_PATH: ${LD_LIBRARY_PATH:-<not set>}"
echo "  PYTHONNOUSERSITE: ${PYTHONNOUSERSITE:-<not set>}"
echo ""

echo "🔧 LM Studio Files:"
cd /cluster/tufts/datalab/zwu09 2>/dev/null && {
    echo "  Server files:"
    ls -lh lm_studio_server*.py 2>/dev/null || echo "    No server files found"
    echo ""
    echo "  Scripts:"
    ls -lh *.sh 2>/dev/null || echo "    No scripts found"
    echo ""
    echo "  Environment:"
    if [ -d "envs/lmstudio_clean" ]; then
        echo "    ✅ Clean environment exists"
        du -sh envs/lmstudio_clean
    else
        echo "    ❌ Clean environment not found"
    fi
} || echo "  Cannot access /cluster/tufts/datalab/zwu09"

echo ""
echo "============================================================"
echo "Diagnostic Complete"
echo "============================================================"
