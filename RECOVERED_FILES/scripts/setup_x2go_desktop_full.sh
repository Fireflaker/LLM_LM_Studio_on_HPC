#!/bin/bash
# X2Go Desktop Full Setup Script for Tufts HPC
# Usage: ./setup_x2go_desktop_full.sh

set -e

echo "🖥️ Setting up Full X2Go Desktop on Tufts HPC..."

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
    yum install -y x2goserver x2goserver-xsession xfce4 xfce4-goodies firefox
    yum install -y gedit nano vim emacs
    yum install -y gcc g++ make cmake
    yum install -y python3-pip python3-dev
elif command -v apt-get &> /dev/null; then
    echo "Using apt package manager..."
    apt-get update
    apt-get install -y x2goserver x2goserver-xsession xfce4 xfce4-goodies firefox
    apt-get install -y gedit nano vim emacs
    apt-get install -y gcc g++ make cmake
    apt-get install -y python3-pip python3-dev
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

# Create desktop shortcuts
mkdir -p ~/Desktop
cat > ~/Desktop/README.txt << 'EOF'
Welcome to your HPC Desktop!

This is a full Linux desktop environment running on your HPC compute node.
You can use this for development, running GUI applications, and more.

Available applications:
- Firefox (web browser)
- Gedit (text editor)
- Terminal
- File manager
- And more!

To connect from Windows:
1. Download X2Go Client from https://wiki.x2go.org/doku.php/doc:installation:x2goclient
2. Install and open X2Go Client
3. Create new session:
   - Host: login.pax.tufts.edu
   - Login: zwu09
   - SSH Port: 22
   - Session Type: XFCE
4. Connect to the session

Enjoy your HPC desktop experience!
EOF

# Wait a moment for desktop to start
sleep 5

echo "✅ X2Go Desktop is running!"
echo "🖥️ Server: login.pax.tufts.edu"
echo "👤 Username: zwu09"
echo "🔗 Download X2Go client from: https://wiki.x2go.org/doku.php/doc:installation:x2goclient"
echo ""
echo "📋 Windows Setup:"
echo "1. Download X2Go Client from: https://wiki.x2go.org/doku.php/doc:installation:x2goclient"
echo "2. Install and open X2Go Client"
echo "3. Create new session:"
echo "   - Host: login.pax.tufts.edu"
echo "   - Login: zwu09"
echo "   - SSH Port: 22"
echo "   - Session Type: XFCE"
echo "4. Connect to the session"

# Keep the script running
echo ""
echo "Press Ctrl+C to stop the X2Go server"
trap 'echo "Stopping X2Go server..."; exit 0' INT
while true; do sleep 1; done
