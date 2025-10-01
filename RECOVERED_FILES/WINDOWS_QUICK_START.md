# Windows 11 Quick Start Guide - Full Linux GUI on HPC

## 🚀 **Easiest Setup (VNC Desktop)**

### **Step 1: Download Software on Windows 11**
1. **Download RealVNC Viewer**: https://www.realvnc.com/download/viewer/
2. **Install RealVNC Viewer** (no registration required)
3. **Download PuTTY** (for SSH tunneling): https://www.putty.org/

### **Step 2: Setup HPC Server**
```bash
# SSH to your HPC
ssh zwu09@login.pax.tufts.edu

# Get compute node with GPU
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash

# Run the setup script
./HPC/scripts/setup_vnc_desktop_full.sh
```

### **Step 3: Connect from Windows 11**
1. **Open PuTTY** on Windows
2. **Configure SSH tunnel**:
   - Host: `login.pax.tufts.edu`
   - Port: `22`
   - Username: `zwu09`
   - Go to Connection → SSH → Tunnels
   - Source port: `5901`
   - Destination: `127.0.0.1:5901`
   - Click "Add"
3. **Connect to HPC** (enter password)
4. **Open RealVNC Viewer**
5. **Connect to**: `localhost:5901`
6. **Enter VNC password** (set during setup)

---

## 🎯 **Alternative Setup (X2Go Desktop)**

### **Step 1: Download Software on Windows 11**
1. **Download X2Go Client**: https://wiki.x2go.org/doku.php/doc:installation:x2goclient
2. **Install X2Go Client**

### **Step 2: Setup HPC Server**
```bash
# SSH to your HPC
ssh zwu09@login.pax.tufts.edu

# Get compute node with GPU
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash

# Run the setup script
./HPC/scripts/setup_x2go_desktop_full.sh
```

### **Step 3: Connect from Windows 11**
1. **Open X2Go Client**
2. **Create new session**:
   - Session name: `HPC Desktop`
   - Host: `login.pax.tufts.edu`
   - Login: `zwu09`
   - SSH Port: `22`
   - Session Type: `XFCE`
3. **Connect** (enter password)

---

## 📋 **What You Get**

### **Full Linux Desktop Environment**
- **Desktop**: XFCE (lightweight and fast)
- **Web Browser**: Firefox
- **Text Editors**: Gedit, Nano, Vim, Emacs
- **Development Tools**: GCC, G++, Make, CMake
- **Python**: Python3 with pip
- **File Manager**: Full file system access
- **Terminal**: Multiple terminal windows
- **And more!**

### **Perfect for Development**
- **Code editing** with syntax highlighting
- **File management** with drag-and-drop
- **Web browsing** for documentation
- **Terminal access** for command-line tools
- **GPU development** with CUDA support
- **Python development** with full IDE experience

---

## 🔧 **Troubleshooting**

### **Common Issues**
1. **"Connection refused"** → Check SSH tunnel is working
2. **"Authentication failed"** → Check VNC password
3. **"Desktop not starting"** → Check VNC server is running
4. **"Permission denied"** → Run on compute node, not login node

### **Quick Fixes**
```bash
# Check if on compute node
echo $SLURM_JOB_ID

# Check VNC server
ps aux | grep vnc

# Restart VNC server
vncserver -kill :1
vncserver :1 -geometry 1920x1080 -depth 24
```

---

## 🎯 **My Recommendation**

**Start with VNC Desktop** - it's the most reliable and gives you the best experience:

1. **Download RealVNC Viewer** (free, no registration)
2. **Download PuTTY** (for SSH tunneling)
3. **Run the VNC setup script** on your HPC
4. **Create SSH tunnel** with PuTTY
5. **Connect with RealVNC Viewer**

This gives you a complete Linux desktop environment that you can use for development, with full access to all GUI applications and tools.

---

## 📞 **Support**

If you encounter issues:
1. Check the troubleshooting section above
2. Verify you're on a compute node (not login node)
3. Ensure sufficient resources are allocated
4. Check network connectivity and tunneling

Remember: Always work in `/cluster/tufts/datalab/zwu09` to avoid HOME directory issues!
