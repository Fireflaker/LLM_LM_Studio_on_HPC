# GUI Solutions for Tufts HPC - Complete Setup Guide

## Overview
This guide provides multiple GUI solutions for your Tufts HPC environment with A100/H100 GPUs and 400GB storage. All solutions are designed to work from scratch with minimal dependencies.

## 🎯 Recommended Solutions (Easiest to Hardest)

### 1. **JupyterLab with GUI Extensions** ⭐ **RECOMMENDED**
**Difficulty**: Easy | **Setup Time**: 15 minutes | **Resource Usage**: Low

#### What you get:
- Full web-based GUI through browser
- File manager, terminal, code editor
- GPU-accelerated applications
- Persistent sessions

#### Setup:
```bash
# 1. Get compute node with GPU
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash

# 2. Install GUI extensions in your environment
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
source $DATALAB_BASE/envs/py311/bin/activate

# Install GUI extensions
pip install jupyterlab-git jupyterlab-lsp jupyterlab-system-monitor
pip install jupyterlab-drawio jupyterlab-variableinspector
pip install ipywidgets ipycanvas ipyvolume

# 3. Start enhanced JupyterLab
jupyter lab --no-browser --ip 127.0.0.1 --port 8891 \
  --ServerApp.token=allen \
  --NotebookApp.notebook_dir=$DATALAB_BASE \
  --ServerApp.allow_origin='*' \
  --ServerApp.disable_check_xsrf=True
```

#### Access:
- Tunnel: `ssh -J zwu09@login.pax.tufts.edu -L 8891:127.0.0.1:8891 zwu09@NODE`
- Browser: `http://localhost:8891/?token=allen`

---

### 2. **VNC Server with Lightweight Desktop** ⭐ **BEST FOR FULL DESKTOP**
**Difficulty**: Medium | **Setup Time**: 30 minutes | **Resource Usage**: Medium

#### What you get:
- Full Linux desktop environment
- Run any GUI application
- Persistent desktop sessions
- Multiple desktop environments

#### Setup:
```bash
# 1. Get compute node
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash

# 2. Install VNC and lightweight desktop
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
mkdir -p $DATALAB_BASE/vnc

# Install TigerVNC and XFCE (lightweight)
yum install -y tigervnc-server xfce4 xfce4-goodies || \
apt-get update && apt-get install -y tigervnc-standalone-server xfce4 xfce4-goodies

# 3. Configure VNC
vncpasswd  # Set password when prompted
vncserver :1 -geometry 1920x1080 -depth 24

# 4. Start desktop environment
export DISPLAY=:1
startxfce4 &
```

#### Access:
- Tunnel: `ssh -J zwu09@login.pax.tufts.edu -L 5901:127.0.0.1:5901 zwu09@NODE`
- VNC Client: Connect to `localhost:5901`

---

### 3. **X2Go Remote Desktop** ⭐ **BEST PERFORMANCE**
**Difficulty**: Medium | **Setup Time**: 45 minutes | **Resource Usage**: Medium

#### What you get:
- High-performance remote desktop
- Optimized for low bandwidth
- Session persistence
- Multiple desktop environments

#### Setup:
```bash
# 1. Get compute node
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash

# 2. Install X2Go server
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
mkdir -p $DATALAB_BASE/x2go

# Install X2Go server and desktop
yum install -y x2goserver x2goserver-xsession || \
apt-get update && apt-get install -y x2goserver x2goserver-xsession

# Install lightweight desktop
yum install -y xfce4 || apt-get install -y xfce4

# 3. Start X2Go server
x2goserver-add-session zwu09
```

#### Access:
- Download X2Go client from https://wiki.x2go.org/
- Connect to: `login.pax.tufts.edu` (port 22)
- Session: `zwu09`

---

### 4. **Docker Desktop with GUI** ⭐ **MOST FLEXIBLE**
**Difficulty**: Hard | **Setup Time**: 60 minutes | **Resource Usage**: High

#### What you get:
- Full containerized desktop
- Isolated environment
- Easy software installation
- Windows-like experience

#### Setup:
```bash
# 1. Get compute node with more resources
srun -p gpu --gres=gpu:a100:1 -c 16 --mem=64G -t 04:00:00 --pty bash

# 2. Install Docker (if available)
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
mkdir -p $DATALAB_BASE/docker

# 3. Run GUI container
docker run -it --rm \
  --gpus all \
  -p 6080:6080 \
  -v $DATALAB_BASE:/workspace \
  dorowu/ubuntu-desktop-lxde-vnc
```

#### Access:
- Tunnel: `ssh -J zwu09@login.pax.tufts.edu -L 6080:127.0.0.1:6080 zwu09@NODE`
- Browser: `http://localhost:6080`

---

## 🚀 Quick Start Commands

### For JupyterLab GUI (Recommended):
```bash
# One-liner setup
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash && \
export DATALAB_BASE=/cluster/tufts/datalab/zwu09 && \
source $DATALAB_BASE/envs/py311/bin/activate && \
pip install jupyterlab-git jupyterlab-lsp ipywidgets && \
jupyter lab --no-browser --ip 127.0.0.1 --port 8891 --ServerApp.token=allen
```

### For VNC Desktop:
```bash
# One-liner setup
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash && \
vncserver :1 -geometry 1920x1080 -depth 24 && \
export DISPLAY=:1 && startxfce4 &
```

## 🔧 Troubleshooting

### Common Issues:
1. **Permission denied**: Run commands on compute node, not login node
2. **Port conflicts**: Change port numbers (8892, 5902, etc.)
3. **Memory issues**: Increase `--mem` parameter
4. **GPU not detected**: Check with `nvidia-smi`

### Resource Monitoring:
```bash
# Check GPU usage
nvidia-smi

# Check memory usage
free -h

# Check disk space
df -h /cluster/tufts/datalab
```

## 📋 Requirements Summary

| Solution | CPU | RAM | GPU | Setup Time | Difficulty |
|----------|-----|-----|-----|------------|------------|
| JupyterLab GUI | 8 cores | 32GB | 1x A100 | 15 min | Easy |
| VNC Desktop | 8 cores | 32GB | 1x A100 | 30 min | Medium |
| X2Go | 8 cores | 32GB | 1x A100 | 45 min | Medium |
| Docker GUI | 16 cores | 64GB | 1x A100 | 60 min | Hard |

## 🎯 Recommendations

1. **Start with JupyterLab GUI** - easiest to set up, most reliable
2. **Use VNC for full desktop** - if you need traditional desktop experience
3. **Try X2Go for performance** - if you have bandwidth issues
4. **Docker for isolation** - if you need specific software environments

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify you're on a compute node (not login node)
3. Ensure sufficient resources are allocated
4. Check network connectivity and tunneling

Remember: Always work in `/cluster/tufts/datalab/zwu09` to avoid HOME directory issues!
