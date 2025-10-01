#!/bin/bash
# VNC Desktop Full Setup Script for Tufts HPC
# Usage: ./setup_vnc_desktop_full.sh

set -e

echo "🖥️ Setting up Full VNC Desktop on Tufts HPC..."

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
    yum install -y gedit nano vim emacs
    yum install -y gcc g++ make cmake
    yum install -y python3-pip python3-dev
    yum install -y xfce4-terminal xfce4-screenshooter
elif command -v apt-get &> /dev/null; then
    echo "Using apt package manager..."
    apt-get update
    apt-get install -y tigervnc-standalone-server xfce4 xfce4-goodies firefox
    apt-get install -y gedit nano vim emacs
    apt-get install -y gcc g++ make cmake
    apt-get install -y python3-pip python3-dev
    apt-get install -y xfce4-terminal xfce4-screenshooter
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
export DISPLAY=:1
exec startxfce4
EOF

chmod +x ~/.vnc/xstartup

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
1. Download RealVNC Viewer from https://www.realvnc.com/download/viewer/
2. Create SSH tunnel: ssh -J zwu09@login.pax.tufts.edu -L 5901:127.0.0.1:5901 zwu09@NODE
3. Connect VNC client to localhost:5901

Enjoy your HPC desktop experience!
EOF

# Start VNC server
echo "🚀 Starting VNC server..."
vncserver :1 -geometry 1920x1080 -depth 24

# Set display
export DISPLAY=:1

# Start desktop environment
echo "🖥️ Starting desktop environment..."
startxfce4 &

# Wait a moment for desktop to start
sleep 5

echo "✅ VNC Desktop is running!"
echo "🖥️ Desktop: $(hostname):1"
echo "📡 Tunnel command: ssh -J zwu09@login.pax.tufts.edu -L 5901:127.0.0.1:5901 zwu09@$(hostname)"
echo "🔗 VNC Client: Connect to localhost:5901"
echo "🔐 Password: Use the password you set with vncpasswd"
echo ""
echo "📋 Windows Setup:"
echo "1. Download RealVNC Viewer from: https://www.realvnc.com/en/connect/download/viewer/"
echo "2. Install and open RealVNC Viewer (no registration required)"
echo "3. Create SSH tunnel from Windows:"
echo "   ssh -J zwu09@login.pax.tufts.edu -L 5901:127.0.0.1:5901 zwu09@$(hostname)"
echo "4. In RealVNC Viewer, connect to: localhost:5901"
echo "5. Enter your VNC password"
echo ""
echo "🎯 RealVNC Viewer Benefits:"
echo "✅ Free - no registration required"
echo "✅ Windows 11 optimized"
echo "✅ Professional grade security"
echo "✅ Easy setup and connection"

# Keep the script running
echo ""
echo "Press Ctrl+C to stop the VNC server"
trap 'echo "Stopping VNC server..."; vncserver -kill :1; exit 0' INT
while true; do sleep 1; done
