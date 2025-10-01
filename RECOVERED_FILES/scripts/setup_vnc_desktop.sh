#!/bin/bash
# VNC Desktop Setup Script for Tufts HPC
# Usage: ./setup_vnc_desktop.sh

set -e

echo "🖥️ Setting up VNC Desktop on Tufts HPC..."

# Set up environment
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
mkdir -p $DATALAB_BASE/vnc

# Check if we're on a compute node
if [[ "$SLURM_JOB_ID" == "" ]]; then
    echo "❌ Not on a compute node. Please run: srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash"
    exit 1
fi

echo "✅ Running on compute node: $(hostname)"

# Install VNC and desktop environment
echo "📦 Installing VNC and desktop environment..."

# Try different package managers
if command -v yum &> /dev/null; then
    echo "Using yum package manager..."
    yum install -y tigervnc-server xfce4 xfce4-goodies firefox
elif command -v apt-get &> /dev/null; then
    echo "Using apt package manager..."
    apt-get update
    apt-get install -y tigervnc-standalone-server xfce4 xfce4-goodies firefox
else
    echo "❌ No supported package manager found"
    exit 1
fi

# Set up VNC password
echo "🔐 Setting up VNC password..."
if [ ! -f ~/.vnc/passwd ]; then
    mkdir -p ~/.vnc
    echo "Please set a VNC password:"
    vncpasswd
fi

# Configure VNC
echo "⚙️ Configuring VNC server..."
cat > ~/.vnc/xstartup << 'EOF'
#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
export XKL_XMODMAP_DISABLE=1
export XDG_CURRENT_DESKTOP="XFCE"
export XDG_MENU_PREFIX="xfce-"
export XDG_SESSION_DESKTOP="xfce"
exec startxfce4
EOF

chmod +x ~/.vnc/xstartup

# Start VNC server
echo "🚀 Starting VNC server..."
vncserver :1 -geometry 1920x1080 -depth 24

# Set display
export DISPLAY=:1

echo "✅ VNC Desktop is running!"
echo "🖥️ Desktop: $(hostname):1"
echo "📡 Tunnel command: ssh -J zwu09@login.pax.tufts.edu -L 5901:127.0.0.1:5901 zwu09@$(hostname)"
echo "🔗 VNC Client: Connect to localhost:5901"
echo "🔐 Password: Use the password you set with vncpasswd"

# Keep the script running
echo "Press Ctrl+C to stop the VNC server"
trap 'echo "Stopping VNC server..."; vncserver -kill :1; exit 0' INT
while true; do sleep 1; done
