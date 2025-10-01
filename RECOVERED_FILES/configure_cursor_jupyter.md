# Configure Cursor to Connect to HPC Jupyter Server

## Current Setup Model ✅
- **Jupyter Server**: Runs on compute node, port 8891, token "allen"
- **Node**: Use the actual compute node from `squeue` (e.g., `cc1gpu005`)
- **SSH Tunnel**: Open from your laptop to that node

## Steps to Configure Cursor:

### 1. Open Command Palette
- Press `Ctrl+Shift+P` (Windows) or `Cmd+Shift+P` (Mac)

### 2. Select Jupyter Server Command
- Type: `Jupyter: Specify Jupyter server for connections`
- Select it from the dropdown

### 3. Enter the Correct URL
```
http://localhost:8891/?token=allen
```

### 4. Verify Connection
- Open your notebook (`setup_and_discovery.ipynb`)
- Select kernel: "Tufts HPC (hoc)" or "allenML2"
- Run the first cell to test connection

## Troubleshooting:

### If connection still fails:
1. **Check SSH tunnel** on your laptop:
   ```bash
   # In a separate terminal on your laptop (replace NODE with actual hostname):
   ssh -J zwu09@login.pax.tufts.edu -L 8891:127.0.0.1:8891 zwu09@NODE
   ```

2. **Test tunnel** in browser:
   - Go to: `http://localhost:8891`
   - You should see Jupyter interface

3. **Check Jupyter is running** on HPC (on the compute node):
   ```bash
   ps aux | grep jupyter
   ```

4. **Start Jupyter (on compute node)** if not running:
   ```bash
   export DATALAB_BASE=/cluster/tufts/datalab/zwu09
   export JUPYTER_RUNTIME_DIR=$DATALAB_BASE/tmp/jupyter
   export JUPYTER_DATA_DIR=$DATALAB_BASE/jupyter/data
   export JUPYTER_PATH=$DATALAB_BASE/jupyter/share
   export TMPDIR=$DATALAB_BASE/tmp
   mkdir -p "$JUPYTER_RUNTIME_DIR" "$JUPYTER_DATA_DIR" "$JUPYTER_PATH" "$TMPDIR"
   source $DATALAB_BASE/envs/py311/bin/activate
   jupyter lab --no-browser --ip 127.0.0.1 --port 8891 \
     --ServerApp.token=allen \
     --NotebookApp.notebook_dir=$DATALAB_BASE
   ```

### Alternative: Use port 8890
If you prefer to use port 8890 (as Cursor was expecting), you can:
1. Stop current Jupyter (Ctrl+C in HPC terminal)
2. Start Jupyter on port 8890:
   ```bash
   jupyter lab --no-browser --ip 127.0.0.1 --port 8890 --ServerApp.token=allen --NotebookApp.notebook_dir=$DATALAB_BASE
   ```
3. Update SSH tunnel to use port 8890
4. Set Cursor URL to: `http://localhost:8890/?token=allen`

### Pitfall: Local vs HPC shell
If you see `mkdir: cannot create directory '/cluster': Permission denied`, you ran a `/cluster/...` command on your local shell. Always SSH to `login.pax.tufts.edu`, then to the compute node from `squeue`, and run there.

