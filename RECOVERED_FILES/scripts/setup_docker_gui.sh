#!/bin/bash
# Docker GUI Setup Script for Tufts HPC
# Usage: ./setup_docker_gui.sh

set -e

echo "🐳 Setting up Docker GUI on Tufts HPC..."

# Set up environment
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
mkdir -p $DATALAB_BASE/docker

# Check if we're on a compute node
if [[ "$SLURM_JOB_ID" == "" ]]; then
    echo "❌ Not on a compute node. Please run: srun -p gpu --gres=gpu:a100:1 -c 16 --mem=64G -t 04:00:00 --pty bash"
    exit 1
fi

echo "✅ Running on compute node: $(hostname)"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker or use a different solution."
    exit 1
fi

echo "✅ Docker is available"

# Check if NVIDIA Docker is available
if ! command -v nvidia-docker &> /dev/null; then
    echo "⚠️ nvidia-docker not found. GPU support may be limited."
fi

# Create Docker workspace
mkdir -p $DATALAB_BASE/docker/workspace

# Run GUI container
echo "🚀 Starting Docker GUI container..."

# Try different GUI containers
if docker run -it --rm \
  --gpus all \
  -p 6080:6080 \
  -v $DATALAB_BASE/docker/workspace:/workspace \
  dorowu/ubuntu-desktop-lxde-vnc; then
    echo "✅ Docker GUI container started successfully"
elif docker run -it --rm \
  -p 6080:6080 \
  -v $DATALAB_BASE/docker/workspace:/workspace \
  dorowu/ubuntu-desktop-lxde-vnc; then
    echo "✅ Docker GUI container started (without GPU support)"
else
    echo "❌ Failed to start Docker GUI container"
    exit 1
fi

echo "✅ Docker GUI is running!"
echo "🖥️ Container: $(hostname):6080"
echo "📡 Tunnel command: ssh -J zwu09@login.pax.tufts.edu -L 6080:127.0.0.1:6080 zwu09@$(hostname)"
echo "🔗 Browser: http://localhost:6080"
echo "📁 Workspace: $DATALAB_BASE/docker/workspace"

# Keep the script running
echo "Press Ctrl+C to stop the Docker container"
trap 'echo "Stopping Docker container..."; docker stop $(docker ps -q --filter ancestor=dorowu/ubuntu-desktop-lxde-vnc); exit 0' INT
while true; do sleep 1; done
