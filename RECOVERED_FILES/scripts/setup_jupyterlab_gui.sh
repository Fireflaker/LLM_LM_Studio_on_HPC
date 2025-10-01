#!/bin/bash
# JupyterLab GUI Setup Script for Tufts HPC
# Usage: ./setup_jupyterlab_gui.sh

set -e

echo "🚀 Setting up JupyterLab GUI on Tufts HPC..."

# Set up environment
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
export JUPYTER_RUNTIME_DIR=$DATALAB_BASE/tmp/jupyter
export JUPYTER_DATA_DIR=$DATALAB_BASE/jupyter/data
export JUPYTER_PATH=$DATALAB_BASE/jupyter/share
export TMPDIR=$DATALAB_BASE/tmp

# Create directories
mkdir -p "$JUPYTER_RUNTIME_DIR" "$JUPYTER_DATA_DIR" "$JUPYTER_PATH" "$TMPDIR"

# Activate Python environment
if [ -f "$DATALAB_BASE/envs/py311/bin/activate" ]; then
    source $DATALAB_BASE/envs/py311/bin/activate
    echo "✅ Activated Python 3.11 environment"
else
    echo "❌ Python environment not found. Please run the environment setup first."
    exit 1
fi

# Install GUI extensions
echo "📦 Installing JupyterLab GUI extensions..."
pip install --upgrade pip
pip install jupyterlab-git jupyterlab-lsp jupyterlab-system-monitor
pip install jupyterlab-drawio jupyterlab-variableinspector
pip install ipywidgets ipycanvas ipyvolume
pip install jupyterlab-code-formatter jupyterlab-github

echo "✅ GUI extensions installed"

# Start JupyterLab
echo "🌐 Starting JupyterLab GUI..."
echo "NODE=$(hostname)"
echo "📝 Copy this hostname for tunneling: $(hostname)"

jupyter lab --no-browser --ip 127.0.0.1 --port 8891 \
  --ServerApp.token=allen \
  --NotebookApp.notebook_dir=$DATALAB_BASE \
  --ServerApp.allow_origin='*' \
  --ServerApp.disable_check_xsrf=True \
  --ServerApp.allow_remote_access=True

echo "✅ JupyterLab GUI is running!"
echo "🔗 Access via: http://localhost:8891/?token=allen"
echo "📡 Tunnel command: ssh -J zwu09@login.pax.tufts.edu -L 8891:127.0.0.1:8891 zwu09@$(hostname)"
