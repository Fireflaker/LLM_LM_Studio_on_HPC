import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue


DEFAULT_GPU_PARTITION = "preempt"
DEFAULT_GPUS = "h100:2"
DEFAULT_CPUS = "40"
DEFAULT_MEM = "200G"
DEFAULT_TIME = "8:00:00"
DEFAULT_PORT = 7860
DEFAULT_TOKEN = "allen"


def which(cmd: str) -> bool:
    return subprocess.call(["where" if os.name == "nt" else "which", cmd],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tufts HPC LLM & Jupyter Launcher")
        self.geometry("1000x700")

        self.user_var = tk.StringVar(value="zwu09")
        self.partition_var = tk.StringVar(value=DEFAULT_GPU_PARTITION)
        self.gres_var = tk.StringVar(value=DEFAULT_GPUS)
        self.cpus_var = tk.StringVar(value=DEFAULT_CPUS)
        self.mem_var = tk.StringVar(value=DEFAULT_MEM)
        self.time_var = tk.StringVar(value=DEFAULT_TIME)
        self.port_var = tk.IntVar(value=DEFAULT_PORT)
        self.token_var = tk.StringVar(value=DEFAULT_TOKEN)
        self.node_var = tk.StringVar(value="")
        self.persistent_var = tk.BooleanVar(value=True)

        self._build()
        self._init_debug()

    def _build(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(frm, text="Tufts UTLN (username)").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(frm, textvariable=self.user_var, width=22).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Label(frm, text="Partition").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(frm, textvariable=self.partition_var, width=12).grid(row=row, column=1, sticky=tk.W)
        ttk.Label(frm, text="GRES (GPU)").grid(row=row, column=2, sticky=tk.W)
        ttk.Entry(frm, textvariable=self.gres_var, width=12).grid(row=row, column=3, sticky=tk.W)

        row += 1
        ttk.Label(frm, text="CPUs").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(frm, textvariable=self.cpus_var, width=8).grid(row=row, column=1, sticky=tk.W)
        ttk.Label(frm, text="Memory").grid(row=row, column=2, sticky=tk.W)
        ttk.Entry(frm, textvariable=self.mem_var, width=8).grid(row=row, column=3, sticky=tk.W)

        row += 1
        ttk.Label(frm, text="Time").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(frm, textvariable=self.time_var, width=10).grid(row=row, column=1, sticky=tk.W)
        ttk.Label(frm, text="Jupyter Port").grid(row=row, column=2, sticky=tk.W)
        ttk.Entry(frm, textvariable=self.port_var, width=8).grid(row=row, column=3, sticky=tk.W)

        row += 1
        ttk.Label(frm, text="Token").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(frm, textvariable=self.token_var, width=12).grid(row=row, column=1, sticky=tk.W)

        row += 1
        ttk.Separator(frm).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=6)

        row += 1
        ttk.Button(frm, text="Start LLM Server (auto)", command=self.start_llm_server).grid(row=row, column=0, sticky=tk.W)
        ttk.Button(frm, text="Start Jupyter (auto)", command=self.start_jupyter).grid(row=row, column=1, sticky=tk.W)
        ttk.Label(frm, text="Compute Node").grid(row=row, column=2, sticky=tk.E)
        ttk.Entry(frm, textvariable=self.node_var, width=16).grid(row=row, column=3, sticky=tk.W)

        row += 1
        ttk.Button(frm, text="Open Tunnel", command=self.open_tunnel).grid(row=row, column=0, sticky=tk.W)
        ttk.Button(frm, text="Copy Tunnel Cmd", command=self.copy_tunnel_cmd).grid(row=row, column=1, sticky=tk.W)
        ttk.Button(frm, text="Watch GPU", command=self.watch_gpu).grid(row=row, column=2, sticky=tk.W)
        ttk.Button(frm, text="Check Resources", command=self.check_resources).grid(row=row, column=3, sticky=tk.W)

        row += 1
        ttk.Separator(frm).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=6)

        row += 1
        ttk.Button(frm, text="Open Login Shell", command=self.open_login_shell).grid(row=row, column=0, sticky=tk.W)
        ttk.Button(frm, text="Copy Login Cmd", command=self.copy_login_cmd).grid(row=row, column=1, sticky=tk.W)
        ttk.Button(frm, text="Open Allocation Shell", command=self.open_alloc_shell).grid(row=row, column=2, sticky=tk.W)
        ttk.Button(frm, text="Copy Allocation Cmd", command=self.copy_alloc_cmd).grid(row=row, column=3, sticky=tk.W)

        row += 1
        ttk.Button(frm, text="Copy LLM Setup Cmds", command=self.copy_llm_setup_cmds).grid(row=row, column=0, sticky=tk.W)
        ttk.Button(frm, text="Copy LLM Auto Script", command=self.copy_llm_auto_start_script).grid(row=row, column=1, sticky=tk.W)
        ttk.Button(frm, text="Copy Jupyter Setup Cmds", command=self.copy_setup_cmds).grid(row=row, column=2, sticky=tk.W)
        ttk.Button(frm, text="Copy Jupyter Auto Script", command=self.copy_auto_start_script).grid(row=row, column=3, sticky=tk.W)

        row += 1
        ttk.Checkbutton(frm, text="Persistent SSH mode (use your open login shell)", variable=self.persistent_var).grid(row=row, column=0, columnspan=3, sticky=tk.W)

        row += 1
        ttk.Separator(frm).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=6)

        row += 1
        ttk.Label(frm, text="Job IDs (comma/space-separated)").grid(row=row, column=0, sticky=tk.W)
        self.jobs_entry = ttk.Entry(frm, width=28)
        self.jobs_entry.grid(row=row, column=1, sticky=tk.W)
        ttk.Button(frm, text="List My Jobs", command=self.list_jobs).grid(row=row, column=2, sticky=tk.W)
        ttk.Button(frm, text="Cancel Job(s)", command=self.cancel_jobs).grid(row=row, column=3, sticky=tk.W)

        row += 1
        ttk.Button(frm, text="Cancel ALL My Jobs", command=self.cancel_all_jobs).grid(row=row, column=2, sticky=tk.W)

        row += 1
        ttk.Separator(frm).grid(row=row, column=0, columnspan=4, sticky=tk.EW, pady=6)

        row += 1
        tips = (
            "LLM Workflow: Start LLM Server → copy NODE → Open Tunnel → http://localhost:7860\n"
            "Jupyter Workflow: Start Jupyter → copy NODE → Open Tunnel → http://localhost:<port>/?token=<token>\n"
            "Pitfall: /cluster commands must run on HPC node, not locally.\n"
            "GPU Monitoring: Use 'Watch GPU' button to monitor nvidia-smi in real-time"
        )
        ttk.Label(frm, text=tips, foreground="#333").grid(row=row, column=0, columnspan=4, sticky=tk.W)

        # Embedded shell / logs at bottom
        shell_frame = ttk.LabelFrame(self, text="Interactive Shell & Logs", padding=6)
        shell_frame.pack(fill=tk.BOTH, expand=True)
        self.shell_text = tk.Text(shell_frame, height=14, wrap=tk.NONE, bg="#0d1117", fg="#d0d7de")
        self.shell_text.pack(fill=tk.BOTH, expand=True)
        self.cmd_entry = ttk.Entry(shell_frame)
        self.cmd_entry.pack(fill=tk.X)
        self.cmd_entry.bind("<Return>", self._on_cmd_enter)
        btns = ttk.Frame(shell_frame)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="Run Local Cmd", command=self._run_local_cmd).pack(side=tk.LEFT)
        ttk.Button(btns, text="Clear", command=lambda: self.shell_text.delete("1.0", tk.END)).pack(side=tk.LEFT)

    def _powershell(self) -> str:
        return os.path.join(os.environ.get("SystemRoot", r"C:\\Windows"), "System32", "WindowsPowerShell", "v1.0", "powershell.exe")

    def start_llm_server(self):
        self._log_debug("start_llm_server invoked")
        if not which("ssh"):
            messagebox.showerror("Missing SSH", "OpenSSH client (ssh) is not on PATH")
            return
        user = self.user_var.get().strip()
        part = self.partition_var.get().strip()
        gres = self.gres_var.get().strip()
        cpus = self.cpus_var.get().strip()
        mem = self.mem_var.get().strip()
        time = self.time_var.get().strip()
        port = int(self.port_var.get())

        # LLM Server setup script
        script = f"""
        $ErrorActionPreference = 'Stop'
        $user = '{user}'
        $port = {port}
        ssh $user@login.pax.tufts.edu -tt @'
          set -e
          echo "Requesting GPU allocation for LLM server..."
          srun -p {part} --gres=gpu:{gres} -c {cpus} --mem={mem} -t {time} --pty bash <<'EOF'
            set -e
            echo "=== Activating conda environment ==="
            source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh
            conda activate lmstudio_v3
            
            echo "=== Setting environment variables ==="
            export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            export PYTHONNOUSERSITE=1
            export HF_HOME=/cluster/tufts/datalab/$USER/caches/huggingface
            export TRANSFORMERS_CACHE=/cluster/tufts/datalab/$USER/caches/huggingface
            
            echo "=== Navigating to text-generation-webui ==="
            cd /cluster/tufts/datalab/$USER/text-generation-webui
            
            echo "=== Starting LLM server with 2x H100 GPUs ==="
            nohup python server.py --listen --listen-port $port --autosplit --no_flash_attn --trust-remote-code --verbose > server.log 2>&1 < /dev/null &
            
            echo "=== Server started, checking status ==="
            sleep 3
            ps aux | grep server.py | grep -v grep
            
            echo "=== Compute node: $(hostname) ==="
            echo "=== Server process: $(pgrep -f server.py) ==="
            echo "=== Port: $port ==="
            echo "=== To access: ssh -L $port:$(hostname):$port $user@login.pax.tufts.edu ==="
            echo "=== Then open: http://localhost:$port ==="
            
            # Keep the session alive
            tail -f server.log
          EOF
        '@
        """

        if self.persistent_var.get():
            self._log_debug("persistent mode: copying LLM auto start script")
            self.copy_llm_auto_start_script()
        else:
            if os.name == "nt":
                self._run_powershell_file(script)
            else:
                self._spawn_terminal(script)

    def start_jupyter(self):
        self._log_debug("start_jupyter invoked")
        if not which("ssh"):
            messagebox.showerror("Missing SSH", "OpenSSH client (ssh) is not on PATH")
            return
        user = self.user_var.get().strip()
        part = self.partition_var.get().strip()
        gres = self.gres_var.get().strip()
        cpus = self.cpus_var.get().strip()
        mem = self.mem_var.get().strip()
        time = self.time_var.get().strip()
        port = int(self.port_var.get())
        token = self.token_var.get().strip()

        # Interactive SSH → allocate → guarded env setup → start Jupyter on compute node
        script = f"""
        $ErrorActionPreference = 'Stop'
        $user = '{user}'
        $port = {port}
        $token = '{token}'
        ssh $user@login.pax.tufts.edu -tt @'
          set -e
          echo "Requesting GPU allocation..."
          srun -p {part} --gres=gpu:{gres} -c {cpus} --mem={mem} -t {time} --pty bash <<'EOF'
            set -e
            export DATALAB_BASE=/cluster/tufts/datalab/$USER
            export JUPYTER_RUNTIME_DIR=$DATALAB_BASE/tmp/jupyter
            export JUPYTER_DATA_DIR=$DATALAB_BASE/jupyter/data
            export JUPYTER_PATH=$DATALAB_BASE/jupyter/share
            export TMPDIR=$DATALAB_BASE/tmp
            mkdir -p "$JUPYTER_RUNTIME_DIR" "$JUPYTER_DATA_DIR" "$JUPYTER_PATH" "$TMPDIR"

            # venv (create once)
            if [ -x /cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11 ] && [ ! -d "$DATALAB_BASE/envs/py311" ]; then
              /cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11 -m venv "$DATALAB_BASE/envs/py311"
            fi
            # activate
            source "$DATALAB_BASE/envs/py311/bin/activate" || true
            python -m pip install -U pip setuptools wheel >/dev/null 2>&1 || true

            # Install only if missing; prefer binary wheels to avoid builds
            python -m pip show jupyterlab >/dev/null 2>&1 || python -m pip install --only-binary=:all: jupyterlab
            python -m pip show ipykernel  >/dev/null 2>&1 || python -m pip install --only-binary=:all: ipykernel
            python -m pip show pyzmq      >/dev/null 2>&1 || python -m pip install --only-binary=:all: "pyzmq<26" || (export CFLAGS='-std=c99' && python -m pip install "pyzmq==25.1.2")

            # kernelspec (install once under datalab)
            if [ ! -d "$DATALAB_BASE/jupyter/share/jupyter/kernels/py311" ]; then
              python -m ipykernel install --prefix "$DATALAB_BASE/jupyter" --name py311 --display-name "Tufts HPC (py311)" || true
            fi

            echo NODE=$(hostname)
            jupyter lab --no-browser --ip 127.0.0.1 --port $port \
              --ServerApp.token=$token \
              --NotebookApp.notebook_dir=$DATALAB_BASE
          EOF
        '@
        """

        # In persistent mode, copy the auto-start script so user pastes it in the existing login shell
        if self.persistent_var.get():
            self._log_debug("persistent mode: copying auto start script instead of spawning new SSH")
            self.clipboard_clear()
            # Reuse the copy_auto_start_script content
            self.copy_auto_start_script()
        else:
            # Use temp PowerShell script on Windows to avoid quoting errors
            if os.name == "nt":
                self._run_powershell_file(script)
            else:
                self._spawn_terminal(script)

    def open_tunnel(self):
        self._log_debug("open_tunnel invoked")
        if not which("ssh"):
            messagebox.showerror("Missing SSH", "OpenSSH client (ssh) is not on PATH")
            return
        user = self.user_var.get().strip()
        node = self.node_var.get().strip()
        port = int(self.port_var.get())
        if not node:
            messagebox.showwarning("Missing node", "Enter the compute node hostname (e.g., cc1gpu005)")
            return

        cmd = f"ssh -J {user}@login.pax.tufts.edu -L {port}:127.0.0.1:{port} {user}@{node}"
        self._spawn_terminal(cmd)

    def copy_tunnel_cmd(self):
        self._log_debug("copy_tunnel_cmd invoked")
        user = self.user_var.get().strip()
        node = self.node_var.get().strip()
        port = int(self.port_var.get())
        cmd = f"ssh -J {user}@login.pax.tufts.edu -L {port}:127.0.0.1:{port} {user}@{node}"
        self.clipboard_clear()
        self.clipboard_append(cmd)
        messagebox.showinfo("Copied", "SSH tunnel command copied to clipboard")

    def check_resources(self):
        self._log_debug("check_resources invoked")
        if not which("ssh"):
            messagebox.showerror("Missing SSH", "OpenSSH client (ssh) is not on PATH")
            return
        user = self.user_var.get().strip()
        # Open a terminal and run a concise cluster status script on the login node
        script = f"""
        $ErrorActionPreference = 'Stop'
        $user = '{user}'
        $cmd = @'
set -e
echo "Node: $(hostname)  User: $USER"
echo "=== HOME ===";    df -h /cluster/home/$USER       | sed -n '1,2p'
echo "=== DATALAB ==="; df -h /cluster/tufts/datalab    | sed -n '1,2p'
echo "=== Your jobs ==="; squeue -u $USER | sed -n '1,20p'
echo "=== Partitions ==="; sinfo -o "%P %a %l %D %c %m %G" | sed -n '1,20p' || true
echo "=== Top in datalab (last 20) ==="; du -sh /cluster/tufts/datalab/$USER/* 2>/dev/null | sort -h | tail -n 20 || true
echo "=== Done ==="
'@
        ssh $user@login.pax.tufts.edu -tt bash -lc $cmd
        """
        if self.persistent_var.get():
            self._log_debug("persistent mode: copying resources commands for manual paste")
            self.copy_resources_cmds()
        else:
            if os.name == "nt":
                self._run_powershell_file(script)
            else:
                self._spawn_terminal(script)

    def watch_gpu(self):
        self._log_debug("watch_gpu invoked")
        if not which("ssh"):
            messagebox.showerror("Missing SSH", "OpenSSH client (ssh) is not on PATH")
            return
        user = self.user_var.get().strip()
        node = self.node_var.get().strip()
        if not node:
            messagebox.showwarning("Missing node", "Enter the compute node hostname first")
            return
        
        cmd = f"watch -d nvidia-smi"
        if self.persistent_var.get():
            self._log_debug("persistent mode: copying watch_gpu cmd")
            self.clipboard_clear()
            self.clipboard_append(cmd)
            self.shell_text.insert(tk.END, f"[copy] {cmd}\n"); self.shell_text.see(tk.END)
        else:
            script = f"""
$ErrorActionPreference = 'Stop'
$user = '{user}'
$node = '{node}'
ssh $user@login.pax.tufts.edu -tt ssh $user@$node -tt "{cmd}"
"""
            if os.name == "nt":
                self._run_powershell_file(script)
            else:
                self._spawn_terminal(script)

    def copy_resources_cmds(self):
        self._log_debug("copy_resources_cmds invoked")
        cmds = (
            "set -e\n"
            "echo \"Node: $(hostname)  User: $USER\"\n"
            "echo \"=== HOME ===\";    df -h /cluster/home/$USER       | sed -n '1,2p'\n"
            "echo \"=== DATALAB ===\"; df -h /cluster/tufts/datalab    | sed -n '1,2p'\n"
            "echo \"=== Your jobs ===\"; squeue -u $USER | sed -n '1,20p'\n"
            "echo \"=== Partitions ===\"; sinfo -o \"%P %a %l %D %c %m %G\" | sed -n '1,20p' || true\n"
            "echo \"=== Top in datalab (last 20) ===\"; du -sh /cluster/tufts/datalab/$USER/* 2>/dev/null | sort -h | tail -n 20 || true\n"
            "echo \"=== GPU Status ===\"; nvidia-smi || echo 'No GPUs found'\n"
            "echo \"=== Done ===\"\n"
        )
        self.clipboard_clear()
        self.clipboard_append(cmds)
        messagebox.showinfo("Copied", "Resource check commands copied to clipboard")

    def open_login_shell(self):
        self._log_debug("open_login_shell invoked")
        user = self.user_var.get().strip()
        cmd = f"ssh {user}@login.pax.tufts.edu"
        self._spawn_terminal(cmd)

    def open_alloc_shell(self):
        self._log_debug("open_alloc_shell invoked")
        user = self.user_var.get().strip()
        part = self.partition_var.get().strip()
        gres = self.gres_var.get().strip()
        cpus = self.cpus_var.get().strip()
        mem = self.mem_var.get().strip()
        time = self.time_var.get().strip()
        # Open an allocation and drop into an interactive shell on the compute node
        cmd = f"ssh {user}@login.pax.tufts.edu -tt srun -p {part} --gres=gpu:{gres} -c {cpus} --mem={mem} -t {time} --pty bash"
        self._spawn_terminal(cmd)

    def copy_llm_setup_cmds(self):
        self._log_debug("copy_llm_setup_cmds invoked")
        port = int(self.port_var.get())
        cmds = f"""
# LLM Server Setup Commands
echo "=== Activating conda environment ==="
source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh
conda activate lmstudio_v3

echo "=== Setting environment variables ==="
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export PYTHONNOUSERSITE=1
export HF_HOME=/cluster/tufts/datalab/$USER/caches/huggingface
export TRANSFORMERS_CACHE=/cluster/tufts/datalab/$USER/caches/huggingface

echo "=== Navigating to text-generation-webui ==="
cd /cluster/tufts/datalab/$USER/text-generation-webui

echo "=== Starting LLM server with 2x H100 GPUs ==="
nohup python server.py --listen --listen-port {port} --autosplit --no_flash_attn --trust-remote-code --verbose > server.log 2>&1 < /dev/null &

echo "=== Server started, checking status ==="
sleep 3
ps aux | grep server.py | grep -v grep

echo "=== Compute node: $(hostname) ==="
echo "=== Server process: $(pgrep -f server.py) ==="
echo "=== Port: {port} ==="
echo "=== To access: ssh -L {port}:$(hostname):{port} $USER@login.pax.tufts.edu ==="
echo "=== Then open: http://localhost:{port} ==="

# Keep the session alive
tail -f server.log
""".strip()
        self.clipboard_clear()
        self.clipboard_append(cmds)
        messagebox.showinfo("Copied", "LLM setup commands copied to clipboard")

    def copy_setup_cmds(self):
        self._log_debug("copy_setup_cmds invoked")
        port = int(self.port_var.get())
        token = self.token_var.get().strip()
        cmds = f"""
export DATALAB_BASE=/cluster/tufts/datalab/$USER
export JUPYTER_RUNTIME_DIR=$DATALAB_BASE/tmp/jupyter
export JUPYTER_DATA_DIR=$DATALAB_BASE/jupyter/data
export JUPYTER_PATH=$DATALAB_BASE/jupyter/share
export TMPDIR=$DATALAB_BASE/tmp
mkdir -p "$JUPYTER_RUNTIME_DIR" "$JUPYTER_DATA_DIR" "$JUPYTER_PATH" "$TMPDIR"

# venv create once
if [ -x /cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11 ] && [ ! -d "$DATALAB_BASE/envs/py311" ]; then
  /cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11 -m venv "$DATALAB_BASE/envs/py311"
fi
source "$DATALAB_BASE/envs/py311/bin/activate" || true
python -m pip install -U pip setuptools wheel >/dev/null 2>&1 || true

# Install only if missing, prefer wheels
python -m pip show jupyterlab >/dev/null 2>&1 || python -m pip install --only-binary=:all: jupyterlab
python -m pip show ipykernel  >/dev/null 2>&1 || python -m pip install --only-binary=:all: ipykernel
python -m pip show pyzmq      >/dev/null 2>&1 || python -m pip install --only-binary=:all: "pyzmq<26" || (export CFLAGS='-std=c99' && python -m pip install "pyzmq==25.1.2")

# kernelspec once under datalab
[ -d "$DATALAB_BASE/jupyter/share/jupyter/kernels/py311" ] || \
  python -m ipykernel install --prefix "$DATALAB_BASE/jupyter" --name py311 --display-name "Tufts HPC (py311)"

echo NODE=$(hostname)
jupyter lab --no-browser --ip 127.0.0.1 --port {port} --ServerApp.token={token} --NotebookApp.notebook_dir=$DATALAB_BASE
""".strip()
        self.clipboard_clear()
        self.clipboard_append(cmds)
        messagebox.showinfo("Copied", "Jupyter setup commands copied to clipboard")

    def copy_llm_auto_start_script(self):
        self._log_debug("copy_llm_auto_start_script invoked")
        part = self.partition_var.get().strip()
        gres = self.gres_var.get().strip()
        cpus = self.cpus_var.get().strip()
        mem = self.mem_var.get().strip()
        time = self.time_var.get().strip()
        port = int(self.port_var.get())
        script = f"""
srun -p {part} --gres=gpu:{gres} -c {cpus} --mem={mem} -t {time} --pty bash <<'EOF'
set -e
echo "=== Activating conda environment ==="
source /cluster/tufts/hpc/tools/anaconda/202307/etc/profile.d/conda.sh
conda activate lmstudio_v3

echo "=== Setting environment variables ==="
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export PYTHONNOUSERSITE=1
export HF_HOME=/cluster/tufts/datalab/$USER/caches/huggingface
export TRANSFORMERS_CACHE=/cluster/tufts/datalab/$USER/caches/huggingface

echo "=== Navigating to text-generation-webui ==="
cd /cluster/tufts/datalab/$USER/text-generation-webui

echo "=== Starting LLM server with 2x H100 GPUs ==="
nohup python server.py --listen --listen-port {port} --autosplit --no_flash_attn --trust-remote-code --verbose > server.log 2>&1 < /dev/null &

echo "=== Server started, checking status ==="
sleep 3
ps aux | grep server.py | grep -v grep

echo "=== Compute node: $(hostname) ==="
echo "=== Server process: $(pgrep -f server.py) ==="
echo "=== Port: {port} ==="
echo "=== To access: ssh -L {port}:$(hostname):{port} $USER@login.pax.tufts.edu ==="
echo "=== Then open: http://localhost:{port} ==="

# Keep the session alive
tail -f server.log
EOF
""".strip()
        self.clipboard_clear()
        self.clipboard_append(script)
        messagebox.showinfo("Copied", "LLM auto start script copied to clipboard")

    def copy_auto_start_script(self):
        self._log_debug("copy_auto_start_script invoked")
        part = self.partition_var.get().strip()
        gres = self.gres_var.get().strip()
        cpus = self.cpus_var.get().strip()
        mem = self.mem_var.get().strip()
        time = self.time_var.get().strip()
        port = int(self.port_var.get())
        token = self.token_var.get().strip()
        script = f"""
srun -p {part} --gres=gpu:{gres} -c {cpus} --mem={mem} -t {time} --pty bash <<'EOF'
set -e
export DATALAB_BASE=/cluster/tufts/datalab/$USER
export JUPYTER_RUNTIME_DIR=$DATALAB_BASE/tmp/jupyter
export JUPYTER_DATA_DIR=$DATALAB_BASE/jupyter/data
export JUPYTER_PATH=$DATALAB_BASE/jupyter/share
export TMPDIR=$DATALAB_BASE/tmp
mkdir -p "$JUPYTER_RUNTIME_DIR" "$JUPYTER_DATA_DIR" "$JUPYTER_PATH" "$TMPDIR"
if [ -x /cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11 ] && [ ! -d "$DATALAB_BASE/envs/py311" ]; then
  /cluster/tufts/hpc/tools/anaconda/202307/bin/python3.11 -m venv "$DATALAB_BASE/envs/py311"
fi
source "$DATALAB_BASE/envs/py311/bin/activate" || true
python -m pip install -U pip setuptools wheel >/dev/null 2>&1 || true
python -m pip show jupyterlab >/dev/null 2>&1 || python -m pip install --only-binary=:all: jupyterlab
python -m pip show ipykernel  >/dev/null 2>&1 || python -m pip install --only-binary=:all: ipykernel
python -m pip show pyzmq      >/dev/null 2>&1 || python -m pip install --only-binary=:all: "pyzmq<26" || (export CFLAGS='-std=c99' && python -m pip install "pyzmq==25.1.2")
[ -d "$DATALAB_BASE/jupyter/share/jupyter/kernels/py311" ] || \
  python -m ipykernel install --prefix "$DATALAB_BASE/jupyter" --name py311 --display-name "Tufts HPC (py311)"
echo NODE=$(hostname)
jupyter lab --no-browser --ip 127.0.0.1 --port {port} --ServerApp.token={token} --NotebookApp.notebook_dir=$DATALAB_BASE
EOF
""".strip()
        self.clipboard_clear()
        self.clipboard_append(script)
        messagebox.showinfo("Copied", "Auto start script copied to clipboard")

    def copy_login_cmd(self):
        self._log_debug("copy_login_cmd invoked")
        user = self.user_var.get().strip()
        cmd = f"ssh {user}@login.pax.tufts.edu"
        self.clipboard_clear()
        self.clipboard_append(cmd)
        messagebox.showinfo("Copied", "Login SSH command copied to clipboard")

    def copy_alloc_cmd(self):
        self._log_debug("copy_alloc_cmd invoked")
        part = self.partition_var.get().strip()
        gres = self.gres_var.get().strip()
        cpus = self.cpus_var.get().strip()
        mem = self.mem_var.get().strip()
        time = self.time_var.get().strip()
        cmd = f"srun -p {part} --gres=gpu:{gres} -c {cpus} --mem={mem} -t {time} --pty bash"
        self.clipboard_clear()
        self.clipboard_append(cmd)
        messagebox.showinfo("Copied", "Allocation srun command copied to clipboard")

    # ---- helpers ----
    def _powershell(self) -> str:
        return os.path.join(os.environ.get("SystemRoot", r"C:\\Windows"), "System32", "WindowsPowerShell", "v1.0", "powershell.exe")

    def _cmd_exe(self) -> str:
        return os.path.join(os.environ.get("SystemRoot", r"C:\\Windows"), "System32", "cmd.exe")

    def _spawn_terminal(self, command: str):
        """Open a new terminal window with command, fallback to running locally if terminal unavailable."""
        self._log_debug(f"spawn_terminal: {command}")
        try:
            if os.name == "nt":
                # For complex multi-line commands, prefer writing a temp PowerShell script
                if "\n" in command or "@'" in command or "'@" in command:
                    self._run_powershell_file(command)
                else:
                    if which("wt"):
                        subprocess.Popen(["wt", "-w", "0", "nt", "powershell", "-NoExit", "-Command", command])
                    else:
                        subprocess.Popen([self._cmd_exe(), "/c", "start", "", self._cmd_exe(), "/k", command])
            else:
                # Try common terminals on *nix
                if which("xterm"):
                    subprocess.Popen(["xterm", "-hold", "-e", "bash", "-lc", command])
                elif which("gnome-terminal"):
                    subprocess.Popen(["gnome-terminal", "--", "bash", "-lc", command])
                else:
                    subprocess.Popen(["bash", "-lc", command])
        except Exception as e:
            self._log_debug(f"terminal spawn failed: {e}; running locally")
            self._run_local_async(command)

    def _run_powershell_file(self, script_content: str):
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ps1", mode="w", encoding="utf-8") as f:
                f.write(script_content)
                path = f.name
            # Use -ExecutionPolicy Bypass to avoid local policy blocks (does not persist)
            subprocess.Popen([self._powershell(), "-NoExit", "-ExecutionPolicy", "Bypass", "-File", path])
            self._log_debug(f"spawned ps1: {path}")
        except Exception as e:
            self._log_debug(f"ps1 spawn failed: {e}; running locally")
            self._run_local_async(script_content)

    # Job control helpers
    def list_jobs(self):
        self._log_debug("list_jobs invoked")
        if not which("ssh"):
            messagebox.showerror("Missing SSH", "OpenSSH client (ssh) is not on PATH")
            return
        user = self.user_var.get().strip()
        cmd = "squeue -u $USER | sed -n '1,50p'"
        if self.persistent_var.get():
            self._log_debug("persistent mode: copying list_jobs cmd")
            self.clipboard_clear()
            self.clipboard_append(cmd)
            self.shell_text.insert(tk.END, f"[copy] {cmd}\n"); self.shell_text.see(tk.END)
        else:
            script = f"""
$ErrorActionPreference = 'Stop'
$user = '{user}'
ssh $user@login.pax.tufts.edu -tt bash -lc "{cmd}"
"""
            if os.name == "nt":
                self._run_powershell_file(script)
            else:
                self._spawn_terminal(script)

    def cancel_jobs(self):
        self._log_debug("cancel_jobs invoked")
        if not which("ssh"):
            messagebox.showerror("Missing SSH", "OpenSSH client (ssh) is not on PATH")
            return
        user = self.user_var.get().strip()
        jobs_raw = self.jobs_entry.get().strip() if hasattr(self, 'jobs_entry') else ''
        if not jobs_raw:
            messagebox.showwarning("Jobs", "Enter one or more Job IDs")
            return
        jobs = ' '.join([j for j in jobs_raw.replace(',', ' ').split() if j.isdigit()])
        if not jobs:
            messagebox.showwarning("Jobs", "No valid numeric Job IDs found")
            return
        cmd = f"echo Cancelling: {jobs}; scancel {jobs}; squeue -u $USER | sed -n '1,30p'"
        if self.persistent_var.get():
            self._log_debug("persistent mode: copying cancel_jobs cmd")
            self.clipboard_clear()
            self.clipboard_append(cmd)
            self.shell_text.insert(tk.END, f"[copy] {cmd}\n"); self.shell_text.see(tk.END)
        else:
            script = f"""
$ErrorActionPreference = 'Stop'
$user = '{user}'
ssh $user@login.pax.tufts.edu -tt bash -lc "{cmd}"
"""
            if os.name == "nt":
                self._run_powershell_file(script)
            else:
                self._spawn_terminal(script)

    def cancel_all_jobs(self):
        self._log_debug("cancel_all_jobs invoked")
        if not which("ssh"):
            messagebox.showerror("Missing SSH", "OpenSSH client (ssh) is not on PATH")
            return
        user = self.user_var.get().strip()
        cmd = "echo Cancelling ALL jobs for $USER; scancel -u $USER; squeue -u $USER | sed -n '1,20p'"
        if self.persistent_var.get():
            self._log_debug("persistent mode: copying cancel_all_jobs cmd")
            self.clipboard_clear()
            self.clipboard_append(cmd)
            self.shell_text.insert(tk.END, f"[copy] {cmd}\n"); self.shell_text.see(tk.END)
        else:
            script = f"""
$ErrorActionPreference = 'Stop'
$user = '{user}'
ssh $user@login.pax.tufts.edu -tt bash -lc "{cmd}"
"""
            if os.name == "nt":
                self._run_powershell_file(script)
            else:
                self._spawn_terminal(script)

    def _init_debug(self):
        self._log_q: "queue.Queue[str]" = queue.Queue()
        def pump():
            try:
                while True:
                    line = self._log_q.get_nowait()
                    self.shell_text.insert(tk.END, line + "\n")
                    self.shell_text.see(tk.END)
            except queue.Empty:
                pass
            self.after(120, pump)
        pump()

    def _log_debug(self, msg: str):
        self._log_q.put(f"[DEBUG] {msg}")

    def _on_cmd_enter(self, _event=None):
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return
        self.cmd_entry.delete(0, tk.END)
        self._run_local_async(cmd)

    def _run_local_cmd(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            messagebox.showinfo("Run", "Enter a command in the box above")
            return
        self._run_local_async(cmd)

    def _run_local_async(self, cmd: str):
        self._log_debug(f"run_local: {cmd}")
        def worker():
            try:
                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in proc.stdout:  # type: ignore
                    self._log_q.put(line.rstrip())
                rc = proc.wait()
                self._log_q.put(f"[exit {rc}]")
            except Exception as e:
                self._log_q.put(f"[error] {e}")
        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    App().mainloop()


