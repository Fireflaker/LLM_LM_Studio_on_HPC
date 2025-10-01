#!/bin/bash
# Complete LM Studio Setup Commands for Tufts HPC
# Paste these commands directly into your HPC session after logging in
# Based on proven working setup from your notes

set -e  # Exit on error

echo "============================================================"
echo "🚀 Complete LM Studio Setup for Tufts HPC"
echo "============================================================"
echo ""

# Step 1: Check current allocations
echo "Step 1: Checking current job allocations..."
squeue -u $USER
echo ""
read -p "Do you want to cancel existing jobs? (y/n): " cancel_jobs
if [[ "$cancel_jobs" == "y" ]]; then
    scancel -u $USER
    echo "✅ Canceled all jobs"
    sleep 2
fi
echo ""

# Step 2: Request GPU allocation (H100 preferred, fallback to A100)
echo "Step 2: Requesting GPU allocation..."
echo "Trying H100 first (4 hour allocation)..."
echo ""
echo "Running: srun -p preempt --gres=gpu:h100:1 -c 40 --mem=100G -t 04:00:00 --pty bash"
echo ""
echo "⚠️  This will start an interactive session. After you get the compute node:"
echo "    1. Note the hostname with: hostname"
echo "    2. Continue with the setup commands below"
echo ""
echo "Press Enter to request GPU, or Ctrl+C to cancel"
read

srun -p preempt --gres=gpu:h100:1 -c 40 --mem=100G -t 04:00:00 --pty bash

