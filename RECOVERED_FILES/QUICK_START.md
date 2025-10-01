# Tufts HPC Quick Start Guide

User zwu09@tufts.edu
Password Leowzd832126

## HuggingFace Tokens
Read Token: YOUR_HF_READ_TOKEN_HERE
Write Token (Basic 1): YOUR_HF_WRITE_TOKEN_1
Write Token (Basic 2): YOUR_HF_WRITE_TOKEN_2

**Note:** Get your tokens from https://huggingface.co/settings/tokens

## 📤 Upload Files from Local Computer to HPC

### Method 1: Direct to Compute Node (If you have active session)
```bash
# From your Windows laptop (Git Bash or PowerShell)
# Get the compute node name first from: squeue -u zwu09
scp HPC/test_load_big_model.py zwu09@COMPUTE_NODE.pax.tufts.edu:/cluster/tufts/datalab/zwu09/
scp HPC/lm_studio_server_v3_improved.py zwu09@COMPUTE_NODE.pax.tufts.edu:/cluster/tufts/datalab/zwu09/

# Example with actual node:
scp HPC/test_load_big_model.py zwu09@s1cmp010.pax.tufts.edu:/cluster/tufts/datalab/zwu09/
```

### Method 2: Via Login Node (Always works)
```bash
# Step 1: Upload to login node
scp HPC/test_load_big_model.py zwu09@login.pax.tufts.edu:~/

# Step 2: SSH to login node and move to datalab
ssh zwu09@login.pax.tufts.edu
mv ~/test_load_big_model.py /cluster/tufts/datalab/zwu09/
```

### Method 3: Multiple Files at Once
```bash
# Upload multiple files
scp HPC/test_load_big_model.py HPC/LOAD_MODELS_CORRECTLY.md zwu09@login.pax.tufts.edu:/cluster/tufts/datalab/zwu09/
```

### Windows PowerShell Specific
```powershell
# If using PowerShell
& 'C:\Windows\System32\OpenSSH\scp.exe' HPC\test_load_big_model.py zwu09@login.pax.tufts.edu:/cluster/tufts/datalab/zwu09/
```

## One-liners: SSH → find job → connect to node → start Jupyter

```bash
# 0) SSH (from your laptop terminal, not on HPC)
# PowerShell (Windows):
& 'C:\\Windows\\System32\\OpenSSH\\ssh.exe' zwu09@login.pax.tufts.edu
# Git Bash / macOS / Linux:
ssh zwu09@login.pax.tufts.edu

# ⚠️ CRITICAL: Never run SSH commands from within HPC sessions!
# Always work from your local machine for SSH connections.

# 1) Find active job(s) on login node
squeue -u $USER | sed -n '1,20p'
# Show details for a job if needed
scontrol show job <JOBID> | sed -n '1,40p'

# 2) Connect to the compute node (use NodeList from squeue)
NODE=$(squeue -u $USER -h -o '%N' | head -1); echo "$NODE" && ssh -o StrictHostKeyChecking=no "$NODE"

# 3) Verify GPU and resources on the node
hostname; nvidia-smi || true; nproc || true; free -h || true

# 4) Start (or reattach to) Jupyter on port 8891 (no HOME writes)
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
export JUPYTER_RUNTIME_DIR=$DATALAB_BASE/tmp/jupyter
export JUPYTER_DATA_DIR=$DATALAB_BASE/jupyter/data
export JUPYTER_PATH=$DATALAB_BASE/jupyter/share
export TMPDIR=$DATALAB_BASE/tmp
mkdir -p "$JUPYTER_RUNTIME_DIR" "$JUPYTER_DATA_DIR" "$JUPYTER_PATH" "$TMPDIR"

# Use Python 3.11 interpreter to avoid old 3.6 envs
/cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11 -m venv $DATALAB_BASE/envs/py311
source $DATALAB_BASE/envs/py311/bin/activate
python -m pip install --upgrade pip
python -m pip install jupyterlab ipykernel

# Install kernelspec under datalab (not HOME)
python -m ipykernel install --prefix $DATALAB_BASE/jupyter --name py311 --display-name "Tufts HPC (py311)"

jupyter lab --no-browser --ip 127.0.0.1 --port 8891 \
  --ServerApp.token=allen \
  --NotebookApp.notebook_dir=$DATALAB_BASE

# 5) From your laptop, open the tunnel (use the exact NODE from step 2)
# PowerShell
& 'C:\\Windows\\System32\\OpenSSH\\ssh.exe' -J 'zwu09@login.pax.tufts.edu' -L 8891:127.0.0.1:8891 "zwu09@${NODE}"
# Git Bash / macOS / Linux
ssh -J zwu09@login.pax.tufts.edu -L 8891:127.0.0.1:8891 "zwu09@${NODE}"

# 6) In Cursor, set server URL:
# http://localhost:8891/?token=allen
```

## Request 2x A100 GPUs with 40 CPUs and 40GB RAM

### Option 1: Interactive Session (Recommended)

```bash
./start_2xa100_interactive.sh
```

### Option 2: Batch Job

```bash
sbatch request_2xa100_40cpu_40g.slurm
```

### Option 3: Direct Command

```bash
srun -p gpu --gres=gpu:a100:2 -c 40 --mem=40G -t 24:00:00 --pty bash
```

## After Getting Resources

1. **Activate environment:**

   ```bash
   source /cluster/tufts/datalab/zwu09/envs/hoc/bin/activate
   ```
2. **Start Jupyter Lab:**

   ```bash

   ```

# See step 4 above; ensure env and kernelspec live under /cluster/tufts/datalab/zwu09

jupyter lab --no-browser --ip 127.0.0.1 --port 8891 --ServerApp.token=allen --NotebookApp.notebook_dir=/cluster/tufts/datalab/zwu09

```

3. **On your laptop, create tunnel:**
   ```bash
   ssh -J zwu09@login.pax.tufts.edu -L 8891:127.0.0.1:8891 zwu09@NODE_HOSTNAME
```

4. **In Cursor, set Jupyter server URL:**
   ```
   http://localhost:8891/?token=allen
   ```

## Important Notes

- **Storage**: Work in `/cluster/tufts/datalab/zwu09`, keep `~` minimal
- **Network**: Use "Tufts Secure" Wi‑Fi, not "Secure 6e"
- **GPU Etiquette**: Release resources when idle (`exit` or `scancel JOBID`)
- **Monitor**: Use `squeue -u $USER` to check your jobs

### Pitfall: Local vs HPC shell

- If you see `mkdir: cannot create directory '/cluster': Permission denied`, you ran a `/cluster/...` command on your local laptop shell. SSH to `login.pax.tufts.edu`, then `ssh NODE`, and run there.

## Files in This Directory

- `start_2xa100_interactive.sh` - Interactive session launcher
- `request_2xa100_40cpu_40g.slurm` - Batch job script
- `SLURM_NOTES.md` - Detailed SLURM commands
- `OPERATIONS_SOP.md` - Complete operational procedures
- `QUICK_START.md` - This quick reference guide
- `archive/` - Archived older files
