## Slurm Notes (Tufts HPC)

- Reference: [Slurm Job Scheduler @ Tufts RT Guides](https://rtguides.it.tufts.edu/hpc/slurm/index.html)

### Quick reference
- `squeue` — list your active jobs (R/PD/CG)
- `sinfo` — list partitions and node states
- `sbatch` — submit batch scripts
- `salloc` — allocate interactive resources
- `srun` — run a command/interactive shell on allocated resources
- `scancel` — cancel jobs
- `sprio` — see priorities of pending jobs
- `sacct` — historical accounting (finished jobs)
- `seff` — CPU/memory efficiency of a finished job

### Interactive sessions
```bash
# General interactive shell (choose partition/resources)
srun -p batch -c 4 --mem=8G -t 02:00:00 --pty bash

# GPU interactive examples
srun -p gpu --gres=gpu:a100:1 -c 8  --mem=32G  -t 02:00:00 --pty bash
srun -p gpu --gres=gpu:a100:2 -c 16 --mem=64G  -t 02:00:00 --pty bash

# Your typical request (2h, 40 CPU, 100G RAM, 1×A100)
srun -p gpu --gres=gpu:a100:1 -c 40 --mem=100G -t 02:00:00 --pty bash
```

### Monitor active jobs
```bash
# show your jobs
squeue --me
squeue -u $USER

# show details for a job (running or pending)
scontrol show jobid -dd JOBID
```

Example (from RT Guides):
```bash
squeue --me
squeue -u your_utln
scontrol show jobid -dd 296794
```
Source: [Job Monitoring and Management](https://rtguides.it.tufts.edu/hpc/slurm/monitor.html)

### Cancel jobs
```bash
# specific job
scancel JOBID

# all your jobs
scancel -u $USER
```
Source: [Job Monitoring and Management](https://rtguides.it.tufts.edu/hpc/slurm/monitor.html)

### Finished jobs: utilization and accounting
```bash
# efficiency summary (CPU & memory) for a finished job
seff JOBID

# detailed accounting view (customize --format fields as needed)
sacct --format=partition,state,time,start,end,elapsed,MaxRss,ReqMem,MaxVMSize,nnodes,ncpus,nodelist -j JOBID
```
Source: [Job Resource Utilization](https://rtguides.it.tufts.edu/hpc/slurm/utilization.html)

### Partitions and cluster view
```bash
# partitions with key resources
sinfo -o "%P %a %l %D %c %m %G" | sed -n '1,60p'
```
See: [Slurm Job Scheduler](https://rtguides.it.tufts.edu/hpc/slurm/index.html)

### Helper tool
```bash
module load hpctools 2>/dev/null || true
hpctools    # interactive menu to inspect resources, storage, and jobs
```

### Etiquette / best practice
- Request a right-sized interactive allocation (e.g., 1–4 GPUs for 1–3 hours) and iterate inside it; avoid rapid-fire short GPU `srun`s.
- Release resources when idle (`exit` compute shell, or `scancel JOBID`).
- Keep `~` minimal; put envs, models, caches, and tmp under `/cluster/tufts/datalab/zwu09`.

### Tunneling pattern for Jupyter (summary)
```bash
# 1) On compute node (after srun --pty bash). Ensure Jupyter uses datalab paths.
export DATALAB_BASE=/cluster/tufts/datalab/zwu09
export JUPYTER_RUNTIME_DIR=$DATALAB_BASE/tmp/jupyter
export JUPYTER_DATA_DIR=$DATALAB_BASE/jupyter/data
export JUPYTER_PATH=$DATALAB_BASE/jupyter/share
mkdir -p "$JUPYTER_RUNTIME_DIR" "$JUPYTER_DATA_DIR" "$JUPYTER_PATH"
jupyter lab --no-browser --ip 127.0.0.1 --port 8891 --ServerApp.token=allen

# 2) On laptop (NEW terminal) – replace NODE with actual hostname
# PowerShell:
& 'C:\Windows\System32\OpenSSH\ssh.exe' -J 'zwu09@login.pax.tufts.edu' -L 8891:127.0.0.1:8891 "zwu09@NODE"
# Git Bash:
ssh -J zwu09@login.pax.tufts.edu -L 8891:127.0.0.1:8891 zwu09@NODE

# 3) Cursor Jupyter server URL: http://localhost:8891/?token=allen
```

### Common pitfalls and warnings
- **CRITICAL**: Use actual compute node hostname (from `hostname` command), NOT the job ID
- **CRITICAL**: Run tunnel command in a NEW terminal on your laptop, NOT in the HPC shell
- **CRITICAL**: Jupyter must run on a compute node (after `srun`), NOT on login node
- **LOCAL VS HPC**: `/cluster/...` paths do not exist on your laptop. If you see `mkdir: cannot create directory '/cluster'`, you ran the command locally. SSH to `login.pax.tufts.edu`, then `ssh NODE` and run it there.
- **Network**: Use "Tufts Secure" Wi-Fi, not "Secure 6e" (tunneling may fail)
- **Two terminals needed**: Keep both HPC terminal (running Jupyter) and laptop terminal (running tunnel) open
- **Authentication**: You'll be prompted for password twice (login node + compute node)
