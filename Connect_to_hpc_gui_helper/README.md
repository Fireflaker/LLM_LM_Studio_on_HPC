HPC Jupyter Launcher (GUI)

Purpose: A small Tkinter app to help you:
- SSH to Tufts HPC (with DUO handled by your normal SSH client window)
- Request a 24h GPU allocation (40 CPU, 1×A100, configurable)
- Launch Jupyter on the compute node using datalab-only paths (no HOME writes)
- Open the SSH tunnel from your laptop

Requirements
- Windows/macOS/Linux with a working OpenSSH client (`ssh` on PATH)
- Python 3.8+ locally (Tkinter included)

Quick Start
1) Run the GUI locally:
   - Windows PowerShell: `python HPC/gui_helper/hpc_gui.py`
2) In the GUI, set your username (e.g., `zwu09`) and verify settings
3) Click "Start Jupyter on HPC" → a new console opens, prompts for password + DUO
   - This console will allocate a node and start Jupyter on it
   - It prints `NODE=<hostname>` (e.g., `cc1gpu005`)
4) Copy the printed node name into the GUI "Compute Node" box
5) Click "Open Tunnel" → another console opens for the tunnel
6) In Cursor, set: `http://localhost:<port>/?token=<token>` (defaults: 8891, `allen`)

Notes
- All virtualenv, kernelspec, tmp, caches live under `/cluster/tufts/datalab/<USER>`
- If you see "mkdir: cannot create directory '/cluster'", you ran HPC commands locally. Use the GUI buttons that open SSH consoles.


