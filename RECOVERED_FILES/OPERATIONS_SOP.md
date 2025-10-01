## Tufts HPC + Cursor: Operational SOP (GPU/Jupyter)

### Storage policy
- Work in `/cluster/tufts/datalab/zwu09` (and class paths). Keep `~` minimal.
- Put envs, caches, models, and tmp under datalab (examples below).
- **Storage Management**: Clean setup scripts may accumulate junk. Monitor storage with `df -h /cluster/tufts/datalab/zwu09`
- **LLM Storage**: Reserve space for large models (7B+ models need 10-50GB each). Clean unused environments regularly.

### Network prerequisites (very important)
- On campus Wi‑Fi: use “Tufts Secure”. Avoid “Secure 6e” (tunneling/SSH may fail).
- Off campus: connect to Tufts VPN before SSH/OnDemand.

### Request interactive resources (examples)
```bash
# 2 hours, 40 CPUs, 100G RAM, 1×A100 GPU
srun -p gpu --gres=gpu:a100:1 -c 40 --mem=100G -t 02:00:00 --pty bash

# Quick test: 1 GPU, smaller CPU/mem
srun -p gpu --gres=gpu:a100:1 -c 8 --mem=16G -t 00:30:00 --pty bash
```

### Create env + kernel (one-time, under datalab)
```bash
python3 -m venv /cluster/tufts/datalab/zwu09/envs/hoc
source /cluster/tufts/datalab/zwu09/envs/hoc/bin/activate
python -m pip install --upgrade pip
python -m pip install jupyterlab ipykernel
python -m ipykernel install --user --name hoc --display-name "Tufts HPC (hoc)"
```

### Launch Jupyter on the compute node (fixed token)
```bash
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
export JUPYTER_RUNTIME_DIR=$DATALAB_BASE/tmp/jupyter
export JUPYTER_DATA_DIR=$DATALAB_BASE/jupyter/data
export JUPYTER_PATH=$DATALAB_BASE/jupyter/share
export TMPDIR=$DATALAB_BASE/tmp
mkdir -p "$JUPYTER_RUNTIME_DIR" "$JUPYTER_DATA_DIR" "$JUPYTER_PATH" "$TMPDIR"

# Prefer Python 3.11 env under datalab
/cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11 -m venv $DATALAB_BASE/envs/py311
source $DATALAB_BASE/envs/py311/bin/activate
python -m pip install --upgrade pip
python -m pip install jupyterlab ipykernel
python -m ipykernel install --prefix $DATALAB_BASE/jupyter --name py311 --display-name "Tufts HPC (py311)"

echo "NODE=$(hostname)"   # copy this EXACT hostname for the tunnel (NOT the job ID)
jupyter lab --no-browser --ip 127.0.0.1 --port 8891 \
  --ServerApp.token=allen \
  --NotebookApp.notebook_dir=/cluster/tufts/datalab/zwu09
```

### Tunnel from your laptop (NOT on the HPC shell)
- PowerShell (use call operator `&` and quotes):
```powershell
& 'C:\Windows\System32\OpenSSH\ssh.exe' -J 'zwu09@login.pax.tufts.edu' -L 8891:127.0.0.1:8891 "zwu09@NODE_FROM_ABOVE"
```
- Git Bash (or WSL):
```bash
ssh -J zwu09@login.pax.tufts.edu -L 8891:127.0.0.1:8891 zwu09@NODE_FROM_ABOVE
```
Note: The Windows path `C:\Windows\System32\OpenSSH\ssh.exe` will NOT run inside an HPC bash prompt; run tunnels on your laptop.

### Configure Cursor to use the remote server
- Command Palette → “Jupyter: Specify Jupyter server for connections”
- URL: `http://localhost:8891/?token=allen`
- Open your notebook and select the kernel (e.g., "allenML2" or "Tufts HPC (hoc)").

### Optional: set caches under datalab (reduce HOME usage)
```bash
export HF_HOME=/cluster/tufts/datalab/zwu09/caches/huggingface
export TRANSFORMERS_CACHE=/cluster/tufts/datalab/zwu09/caches/huggingface
export PIP_CACHE_DIR=/cluster/tufts/datalab/zwu09/caches/pip
export TORCH_HOME=/cluster/tufts/datalab/zwu09/caches/torch
export TMPDIR=/cluster/tufts/datalab/zwu09/tmp
mkdir -p "$HF_HOME" "$TRANSFORMERS_CACHE" "$PIP_CACHE_DIR" "$TORCH_HOME" "$TMPDIR"
```

### Resource & queue checks
```bash
df -h /cluster/tufts/datalab
df -h /cluster/tufts/em212class
sinfo -o "%P %a %l %D %c %m %G" | sed -n '1,40p'
squeue -u $USER | sed -n '1,30p'

module load hpctools 2>/dev/null || true
hpctools  # interactive menu if available
```

### GPU etiquette
- Request a right-sized interactive allocation (1–4 GPUs) for 1–3 hours.
- Iterate inside that allocation; avoid rapid-fire short `srun` GPU jobs.
- Release GPUs when idle: `exit` shell and/or `scancel <JOBID>`.

### Troubleshooting
- Cursor "connection failed":
  - Verify Wi‑Fi (Tufts Secure) or VPN, and that the tunnel is open to the correct `NODE`.
  - If port 8891 is busy, choose another port for both Jupyter and the tunnel (e.g., 8892).
- Notebook on login node: always start Jupyter after `srun --pty ...` puts you on a compute node.
- Pitfall: If you see `mkdir: cannot create directory '/cluster': Permission denied`, you are in your local shell. Run `/cluster/...` commands only on HPC login/compute nodes.
- **CRITICAL: Avoid Nested SSH**: Never run `ssh` commands from within HPC sessions. This creates dangerous nested connections. Always work from your local machine or single HPC session.
- **Python Version Issues**: Default Python 3.6.8 is too old for modern ML libraries. Use Python 3.11:
  ```bash
  /cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11 -m venv $DATALAB_BASE/envs/py311
  source $DATALAB_BASE/envs/py311/bin/activate
  ```
- PyTorch/CUDA issues:
  ```bash
  python -m pip install --upgrade pip
  python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
  ```

### Cancel/replace an allocation
```bash
squeue -u $USER
scancel <JOBID>
```

### Quick one-liner recap
```bash
# 1) Get a node
srun -p gpu --gres=gpu:a100:1 -c 40 --mem=100G -t 02:00:00 --pty bash

# 2) Launch Jupyter on the node
source /cluster/tufts/datalab/zwu09/envs/hoc/bin/activate
export JUPYTER_RUNTIME_DIR=/cluster/tufts/datalab/zwu09/tmp/jupyter
export TMPDIR=/cluster/tufts/datalab/zwu09/tmp
mkdir -p "$JUPYTER_RUNTIME_DIR" "$TMPDIR"
echo "NODE=$(hostname)"
jupyter lab --no-browser --ip 127.0.0.1 --port 8891 --ServerApp.token=allen \
  --NotebookApp.notebook_dir=/cluster/tufts/datalab/zwu09

# 3) On laptop: tunnel (PowerShell)
& 'C:\\Windows\\System32\\OpenSSH\\ssh.exe' -J 'zwu09@login.pax.tufts.edu' -L 8891:127.0.0.1:8891 "zwu09@NODE"
# or Git Bash
ssh -J zwu09@login.pax.tufts.edu -L 8891:127.0.0.1:8891 zwu09@NODE

# 4) In Cursor: set Jupyter server to http://localhost:8891/?token=allen

# IMPORTANT: Use the actual compute node hostname (from hostname command), NOT the job ID!
```

## ⚠️ **CRITICAL SSH RULES**

### **NEVER DO THIS:**
- ❌ Running `ssh` commands from within HPC sessions
- ❌ Nested SSH connections (ssh within ssh within ssh)
- ❌ Multiple layers of terminal sessions

### **ALWAYS DO THIS:**
- ✅ Work from your local machine for SSH connections
- ✅ Use single HPC session for compute work
- ✅ Exit properly with `exit` command
- ✅ Check your location with `hostname` command

### **Session Management:**
```bash
# Check where you are
hostname
whoami

# If you're in nested sessions, exit properly
exit  # Repeat until back to local machine

# Then connect properly
ssh zwu09@login.pax.tufts.edu
srun -p gpu --gres=gpu:h100:1 -c 40 --mem=100G -t 03:00:00 --pty bash
```
