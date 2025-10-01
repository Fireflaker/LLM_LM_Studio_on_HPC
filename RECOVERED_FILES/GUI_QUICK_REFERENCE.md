# GUI Solutions Quick Reference - Tufts HPC

## 🚀 Quick Start (Choose One)

### Option 1: JupyterLab GUI (Easiest) ⭐
```bash
# 1. Get compute node
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash

# 2. Run setup script
./HPC/scripts/setup_jupyterlab_gui.sh

# 3. Tunnel from laptop
ssh -J zwu09@login.pax.tufts.edu -L 8891:127.0.0.1:8891 zwu09@NODE

# 4. Open browser: http://localhost:8891/?token=allen
```

### Option 2: VNC Desktop (Full Desktop)
```bash
# 1. Get compute node
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash

# 2. Run setup script
./HPC/scripts/setup_vnc_desktop.sh

# 3. Tunnel from laptop
ssh -J zwu09@login.pax.tufts.edu -L 5901:127.0.0.1:5901 zwu09@NODE

# 4. Connect with VNC client to localhost:5901
```

### Option 3: X2Go Desktop (High Performance)
```bash
# 1. Get compute node
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=32G -t 04:00:00 --pty bash

# 2. Run setup script
./HPC/scripts/setup_x2go_desktop.sh

# 3. Download X2Go client from https://wiki.x2go.org/
# 4. Connect to: login.pax.tufts.edu:22, username: zwu09
```

### Option 4: Docker GUI (Most Flexible)
```bash
# 1. Get compute node with more resources
srun -p gpu --gres=gpu:a100:1 -c 16 --mem=64G -t 04:00:00 --pty bash

# 2. Run setup script
./HPC/scripts/setup_docker_gui.sh

# 3. Tunnel from laptop
ssh -J zwu09@login.pax.tufts.edu -L 6080:127.0.0.1:6080 zwu09@NODE

# 4. Open browser: http://localhost:6080
```

## 📋 Resource Requirements

| Solution | CPU | RAM | GPU | Port | Difficulty |
|----------|-----|-----|-----|------|------------|
| JupyterLab GUI | 8 cores | 32GB | 1x A100 | 8891 | Easy |
| VNC Desktop | 8 cores | 32GB | 1x A100 | 5901 | Medium |
| X2Go Desktop | 8 cores | 32GB | 1x A100 | 22 | Medium |
| Docker GUI | 16 cores | 64GB | 1x A100 | 6080 | Hard |

## 🔧 Troubleshooting

### Common Issues:
1. **"Permission denied"** → Run on compute node, not login node
2. **"Port already in use"** → Change port numbers
3. **"No space left"** → Use `/cluster/tufts/datalab/zwu09` instead of `~`
4. **"GPU not found"** → Check with `nvidia-smi`

### Quick Fixes:
```bash
# Check if on compute node
echo $SLURM_JOB_ID

# Check GPU
nvidia-smi

# Check disk space
df -h /cluster/tufts/datalab

# Kill existing processes
pkill -f jupyter
pkill -f vncserver
```

## 🎯 Recommendations

- **Start with JupyterLab GUI** - easiest to set up
- **Use VNC for full desktop** - if you need traditional desktop
- **Try X2Go for performance** - if you have bandwidth issues
- **Docker for isolation** - if you need specific software

## 📞 Support Commands

```bash
# Check job status
squeue -u $USER

# Check GPU usage
nvidia-smi

# Check memory usage
free -h

# Check disk space
df -h /cluster/tufts/datalab

# Kill all GUI processes
pkill -f jupyter
pkill -f vncserver
pkill -f x2go
pkill -f docker
```

## 🔗 Access URLs

- **JupyterLab GUI**: http://localhost:8891/?token=allen
- **VNC Desktop**: localhost:5901 (VNC client)
- **X2Go Desktop**: login.pax.tufts.edu:22 (X2Go client)
- **Docker GUI**: http://localhost:6080

## 📁 File Locations

- **Scripts**: `HPC/scripts/setup_*.sh`
- **Guide**: `HPC/GUI_SOLUTIONS_GUIDE.md`
- **Workspace**: `/cluster/tufts/datalab/zwu09`
- **Logs**: `/cluster/tufts/datalab/zwu09/tmp/`

Remember: Always work in `/cluster/tufts/datalab/zwu09` to avoid HOME directory issues!
