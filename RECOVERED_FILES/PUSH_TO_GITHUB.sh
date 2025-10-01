#!/bin/bash
# Run these commands from your LOCAL Windows laptop
# Location: C:\Users\sdtyu\Documents\CursorRoot

echo "============================================================"
echo "Pushing HPC Setup to GitHub"
echo "============================================================"
echo ""

# Navigate to HPC folder
cd "$(dirname "$0")"
pwd

# Initialize git if not already
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    echo "✅ Git initialized"
else
    echo "✅ Git already initialized"
fi

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Logs
*.log
nohup.out

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Temporary files
tmp/
*.tmp
*.bak
*~

# HPC specific
*.slurm.out
*.slurm.err
caches/
EOF

echo "✅ Created .gitignore"

# Check git status
echo ""
echo "Current git status:"
git status

# Add all files
echo ""
echo "Adding files to git..."
git add .

# Create comprehensive commit
echo ""
echo "Creating commit..."
git commit -m "Complete HPC LM Studio setup with notes and scripts

Includes:
- Complete setup guides and documentation
- LM Studio server v3 with model caching
- Recommended models for H100
- Upload and connection scripts
- Troubleshooting guides
- vLLM and alternative solutions
- Working configuration for Qwen models

Tested and working on Tufts HPC with H100 GPU"

# Add remote
echo ""
echo "Adding GitHub remote..."
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/Fireflaker/LLM_LM_Studio_on_HPC.git

# Rename branch to main
echo ""
echo "Setting branch to main..."
git branch -M main

# Push to GitHub
echo ""
echo "Pushing to GitHub..."
git push -u origin main --force

echo ""
echo "============================================================"
echo "✅ Successfully pushed to GitHub!"
echo "============================================================"
echo ""
echo "View your repository at:"
echo "https://github.com/Fireflaker/LLM_LM_Studio_on_HPC"
echo ""

