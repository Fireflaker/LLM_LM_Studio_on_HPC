#!/bin/bash

# Tufts HPC LLM Server Setup Script
# This script automates the setup of LLM servers on Tufts HPC

set -e

# Default values
USER="zwu09"
PARTITION="preempt"
GPUS="h100:2"
CPUS="40"
MEM="200G"
TIME="8:00:00"
PORT="7860"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if SSH is available
check_ssh() {
    if ! command -v ssh &> /dev/null; then
        print_error "SSH client not found. Please install OpenSSH."
        exit 1
    fi
}

# Function to start LLM server
start_llm_server() {
    print_status "Starting LLM server setup..."
    
    # Create the setup script
    cat > /tmp/llm_setup.sh << 'EOF'
#!/bin/bash
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
nohup python server.py --listen --listen-port 7860 --autosplit --no_flash_attn --trust-remote-code --verbose > server.log 2>&1 < /dev/null &

echo "=== Server started, checking status ==="
sleep 3
ps aux | grep server.py | grep -v grep

echo "=== Compute node: $(hostname) ==="
echo "=== Server process: $(pgrep -f server.py) ==="
echo "=== Port: 7860 ==="
echo "=== To access: ssh -L 7860:$(hostname):7860 $USER@login.pax.tufts.edu ==="
echo "=== Then open: http://localhost:7860 ==="

# Keep the session alive
tail -f server.log
EOF

    chmod +x /tmp/llm_setup.sh
    
    print_status "Requesting GPU allocation and starting LLM server..."
    ssh $USER@login.pax.tufts.edu -tt "srun -p $PARTITION --gres=gpu:$GPUS -c $CPUS --mem=$MEM -t $TIME --pty bash < /tmp/llm_setup.sh"
}

# Function to create SSH tunnel
create_tunnel() {
    local node=$1
    if [ -z "$node" ]; then
        print_error "Please provide the compute node hostname"
        echo "Usage: $0 tunnel <node_hostname>"
        exit 1
    fi
    
    print_status "Creating SSH tunnel to $node..."
    print_status "Tunnel command: ssh -L $PORT:$node:$PORT $USER@login.pax.tufts.edu"
    print_status "Then open: http://localhost:$PORT"
    
    ssh -L $PORT:$node:$PORT $USER@login.pax.tufts.edu
}

# Function to watch GPU status
watch_gpu() {
    local node=$1
    if [ -z "$node" ]; then
        print_error "Please provide the compute node hostname"
        echo "Usage: $0 watch <node_hostname>"
        exit 1
    fi
    
    print_status "Watching GPU status on $node..."
    ssh $USER@login.pax.tufts.edu -tt "ssh $USER@$node -tt 'watch -d nvidia-smi'"
}

# Function to check resources
check_resources() {
    print_status "Checking HPC resources..."
    ssh $USER@login.pax.tufts.edu -tt << 'EOF'
set -e
echo "Node: $(hostname)  User: $USER"
echo "=== HOME ===";    df -h /cluster/home/$USER       | sed -n '1,2p'
echo "=== DATALAB ==="; df -h /cluster/tufts/datalab    | sed -n '1,2p'
echo "=== Your jobs ==="; squeue -u $USER | sed -n '1,20p'
echo "=== Partitions ==="; sinfo -o "%P %a %l %D %c %m %G" | sed -n '1,20p' || true
echo "=== Top in datalab (last 20) ==="; du -sh /cluster/tufts/datalab/$USER/* 2>/dev/null | sort -h | tail -n 20 || true
echo "=== GPU Status ==="; nvidia-smi || echo 'No GPUs found'
echo "=== Done ==="
EOF
}

# Function to show help
show_help() {
    echo "Tufts HPC LLM Server Setup Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start                 Start LLM server with GPU allocation"
    echo "  tunnel <node>         Create SSH tunnel to compute node"
    echo "  watch <node>          Watch GPU status on compute node"
    echo "  check                 Check HPC resources and status"
    echo "  help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 tunnel s1cmp010.pax.tufts.edu"
    echo "  $0 watch s1cmp010.pax.tufts.edu"
    echo "  $0 check"
}

# Main script logic
main() {
    check_ssh
    
    case "${1:-help}" in
        "start")
            start_llm_server
            ;;
        "tunnel")
            create_tunnel "$2"
            ;;
        "watch")
            watch_gpu "$2"
            ;;
        "check")
            check_resources
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"
