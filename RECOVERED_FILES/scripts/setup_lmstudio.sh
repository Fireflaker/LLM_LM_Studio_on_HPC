#!/bin/bash
# LM Studio Setup Script for Tufts HPC
# Usage: ./setup_lmstudio.sh

set -e

echo "🤖 Setting up LM Studio on Tufts HPC..."

# Set up environment
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
mkdir -p $DATALAB_BASE/lmstudio
cd $DATALAB_BASE/lmstudio

# Check if we're on a compute node
if [[ "$SLURM_JOB_ID" == "" ]]; then
    echo "❌ Not on a compute node. Please run: srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash"
    exit 1
fi

echo "✅ Running on compute node: $(hostname)"

# Download LM Studio
echo "📥 Downloading LM Studio..."
wget https://github.com/lmstudio-ai/lms/releases/download/v0.2.20/lms-0.2.20-linux-x64.tar.gz
tar -xzf lms-0.2.20-linux-x64.tar.gz
cd lms-0.2.20-linux-x64

# Make executable
chmod +x lms

# Start LM Studio web interface
echo "🚀 Starting LM Studio web interface..."
echo "🌐 Web interface will be available at: http://localhost:8080"
echo "📡 To access from your computer, run:"
echo "   ssh -J zwu09@login.pax.tufts.edu -L 8080:127.0.0.1:8080 zwu09@$(hostname)"
echo ""
echo "✅ LM Studio is starting..."

# Start LM Studio
./lms server --host 0.0.0.0 --port 8080

echo "✅ LM Studio setup complete!"
echo "🔗 Access via: http://localhost:8080"
echo "📁 Workspace: $DATALAB_BASE/lmstudio"






