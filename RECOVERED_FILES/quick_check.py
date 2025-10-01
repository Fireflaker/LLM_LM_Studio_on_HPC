#!/usr/bin/env python3
import subprocess
import time

def run_cmd(cmd, desc):
    print(f"[{time.strftime('%H:%M:%S')}] {desc}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
    except Exception as e:
        print(f"Error: {e}")
    print()

# System checks using proper HPC commands
run_cmd("df -h /cluster/tufts/datalab", "Disk space")
run_cmd("squeue -u $USER", "My jobs")
run_cmd("sinfo -o '%P %a %l %D %c %m %G' | head -20", "Partitions")
run_cmd("nvidia-smi", "GPU status")
run_cmd("pip list | grep -E '(torch|diffusers|transformers)'", "Key packages")
run_cmd("jupyter kernelspec list", "Jupyter kernels")

