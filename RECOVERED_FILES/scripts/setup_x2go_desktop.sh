#!/bin/bash
# X2Go Desktop Setup Script for Tufts HPC
# Usage: ./setup_x2go_desktop.sh

set -e

echo "🖥️ Setting up X2Go Desktop on Tufts HPC..."

# Set up environment
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
mkdir -p $DATALAB_BASE/x2go

# Check if we're on a compute node
if [[ "$SLURM_JOB_ID" == "" ]]; then
    echo "❌ Not on a compute node. Please run: srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash"
    exit 1
fi

echo "✅ Running on compute node: $(hostname)"

# Install X2Go and desktop environment
echo "📦 Installing X2Go and desktop environment..."

# Try different package managers
if command -v yum &> /dev/null; then
    echo "Using yum package manager..."
    yum install -y x2goserver x2goserver-xsession xfce4 xfce4-goodies
elif command -v apt-get &> /dev/null; then
    echo "Using apt package manager..."
    apt-get update
    apt-get install -y x2goserver x2goserver-xsession xfce4 xfce4-goodies
else
    echo "❌ No supported package manager found"
    exit 1
fi

# Configure X2Go
echo "⚙️ Configuring X2Go server..."

# Create X2Go session
x2goserver-add-session zwu09

# Set up desktop environment
echo "🖥️ Setting up desktop environment..."
export DISPLAY=:1
startxfce4 &

echo "✅ X2Go Desktop is running!"
echo "🖥️ Server: login.pax.tufts.edu"
echo "👤 Username: zwu09"
echo "🔗 Download X2Go client from: https://wiki.x2go.org/"
echo "📡 Connection: login.pax.tufts.edu:22"

# Keep the script running
echo "Press Ctrl+C to stop the X2Go server"
trap 'echo "Stopping X2Go server..."; exit 0' INT
while true; do sleep 1; done
