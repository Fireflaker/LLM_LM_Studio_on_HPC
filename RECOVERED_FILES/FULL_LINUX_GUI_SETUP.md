# Full Linux GUI Setup for Tufts HPC - Complete Guide

## 🎯 **Best Solutions for Full Linux Desktop Experience**

### **Option 1: VNC Desktop (Recommended)** ⭐
- **What you get**: Complete Linux desktop environment
- **Performance**: Excellent for development work
- **Setup time**: 30 minutes
- **Windows client**: RealVNC Viewer (free)

### **Option 2: X2Go Desktop** ⭐
- **What you get**: High-performance remote desktop
- **Performance**: Optimized for low bandwidth
- **Setup time**: 45 minutes
- **Windows client**: X2Go Client (free)

### **Option 3: NoMachine** ⭐
- **What you get**: Professional remote desktop
- **Performance**: Best for multimedia
- **Setup time**: 60 minutes
- **Windows client**: NoMachine Client (free)

---

## 🖥️ **Windows 11 Client Setup**

### **For VNC Desktop (Recommended)**

#### **Step 1: Download RealVNC Viewer**
1. Go to: https://www.realvnc.com/download/viewer/
2. Download "VNC Viewer" for Windows
3. Install the software (no registration required)

#### **Step 2: Alternative VNC Clients**
- **TightVNC Viewer**: https://www.tightvnc.com/download.php
- **UltraVNC Viewer**: https://www.uvnc.com/downloads/ultravnc.html
- **TigerVNC Viewer**: https://github.com/TigerVNC/tigervnc/releases

### **For X2Go Desktop**

#### **Step 1: Download X2Go Client**
1. Go to: https://wiki.x2go.org/doku.php/doc:installation:x2goclient
2. Download "X2Go Client for Windows"
3. Install the software

### **For NoMachine**

#### **Step 1: Download NoMachine Client**
1. Go to: https://www.nomachine.com/download
2. Download "NoMachine for Windows"
3. Install the software

---

## 🚀 **HPC Server Setup Scripts**

### **VNC Desktop Setup (Recommended)**

```bash
#!/bin/bash
# VNC Desktop Setup for Tufts HPC
# Run this on a compute node

echo "🖥️ Setting up VNC Desktop on Tufts HPC..."

# Get compute node
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash

# Install VNC and desktop environment
yum install -y tigervnc-server xfce4 xfce4-goodies firefox || \
apt-get update && apt-get install -y tigervnc-standalone-server xfce4 xfce4-goodies firefox

# Set up VNC password
mkdir -p ~/.vnc
vncpasswd  # Set your password

# Configure VNC
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
vncserver :1 -geometry 1920x1080 -depth 24

echo "✅ VNC Desktop is running!"
echo "🖥️ Desktop: $(hostname):1"
echo "📡 Tunnel: ssh -J zwu09@login.pax.tufts.edu -L 5901:127.0.0.1:5901 zwu09@$(hostname)"
echo "🔗 VNC Client: Connect to localhost:5901"
```

### **X2Go Desktop Setup**

```bash
#!/bin/bash
# X2Go Desktop Setup for Tufts HPC
# Run this on a compute node

echo "🖥️ Setting up X2Go Desktop on Tufts HPC..."

# Get compute node
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash

# Install X2Go and desktop environment
yum install -y x2goserver x2goserver-xsession xfce4 xfce4-goodies || \
apt-get update && apt-get install -y x2goserver x2goserver-xsession xfce4 xfce4-goodies

# Configure X2Go
x2goserver-add-session zwu09

echo "✅ X2Go Desktop is running!"
echo "🖥️ Server: login.pax.tufts.edu"
echo "👤 Username: zwu09"
echo "🔗 Download X2Go client from: https://wiki.x2go.org/"
```

### **NoMachine Setup**

```bash
#!/bin/bash
# NoMachine Setup for Tufts HPC
# Run this on a compute node

echo "🖥️ Setting up NoMachine on Tufts HPC..."

# Get compute node
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash

# Download and install NoMachine
wget https://download.nomachine.com/download/8.11/Linux/nomachine_8.11.3_4_x86_64.rpm
rpm -i nomachine_8.11.3_4_x86_64.rpm || \
wget https://download.nomachine.com/download/8.11/Linux/nomachine_8.11.3_4_x86_64.deb && \
dpkg -i nomachine_8.11.3_4_x86_64.deb

# Install desktop environment
yum install -y xfce4 xfce4-goodies || \
apt-get update && apt-get install -y xfce4 xfce4-goodies

echo "✅ NoMachine is running!"
echo "🖥️ Server: $(hostname):4000"
echo "🔗 Download NoMachine client from: https://www.nomachine.com/download"
```

---

## 🔧 **Quick Setup Commands**

### **VNC Desktop (Recommended)**
```bash
# 1. Get compute node
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash

# 2. Install VNC and desktop
yum install -y tigervnc-server xfce4 xfce4-goodies firefox

# 3. Set up VNC
vncpasswd  # Set password
vncserver :1 -geometry 1920x1080 -depth 24

# 4. From Windows: Tunnel and connect
ssh -J zwu09@login.pax.tufts.edu -L 5901:127.0.0.1:5901 zwu09@NODE
# Then connect VNC client to localhost:5901
```

### **X2Go Desktop**
```bash
# 1. Get compute node
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash

# 2. Install X2Go and desktop
yum install -y x2goserver x2goserver-xsession xfce4 xfce4-goodies

# 3. Configure X2Go
x2goserver-add-session zwu09

# 4. From Windows: Connect with X2Go client to login.pax.tufts.edu:22
```

---

## 📋 **Windows 11 Download Links**

### **VNC Clients**
- **RealVNC Viewer**: https://www.realvnc.com/download/viewer/
- **TightVNC Viewer**: https://www.tightvnc.com/download.php
- **UltraVNC Viewer**: https://www.uvnc.com/downloads/ultravnc.html
- **TigerVNC Viewer**: https://github.com/TigerVNC/tigervnc/releases

### **X2Go Client**
- **X2Go Client**: https://wiki.x2go.org/doku.php/doc:installation:x2goclient

### **NoMachine Client**
- **NoMachine Client**: https://www.nomachine.com/download

---

## 🎯 **My Recommendation**

**Start with VNC Desktop** - it's the most reliable and easiest to set up:

1. **Download RealVNC Viewer** on your Windows 11 computer
2. **Run the VNC setup script** on your HPC compute node
3. **Create SSH tunnel** from your Windows computer
4. **Connect with VNC client** to localhost:5901

This gives you a complete Linux desktop environment that you can use for development, with full access to all GUI applications.

---

## 🔧 **Troubleshooting**

### **Common Issues**
1. **"Permission denied"** → Run on compute node, not login node
2. **"Port already in use"** → Change port numbers (5902, 5903, etc.)
3. **"Connection refused"** → Check SSH tunnel is working
4. **"Desktop not starting"** → Check VNC server is running

### **Quick Fixes**
```bash
# Check if on compute node
echo $SLURM_JOB_ID

# Check VNC server
ps aux | grep vnc

# Kill existing VNC sessions
vncserver -kill :1

# Restart VNC server
vncserver :1 -geometry 1920x1080 -depth 24
```

---

## 📞 **Support**

If you encounter issues:
1. Check the troubleshooting section above
2. Verify you're on a compute node (not login node)
3. Ensure sufficient resources are allocated
4. Check network connectivity and tunneling

Remember: Always work in `/cluster/tufts/datalab/zwu09` to avoid HOME directory issues!
