#!/bin/bash
set -euo pipefail

# Install and configure RamaLama with GPU support for desktop systems
echo "Setting up RamaLama with GPU support..."

# Check if RamaLama is already installed
if command -v ramalama >/dev/null 2>&1; then
    echo "RamaLama already installed, checking version..."
    ramalama version
    echo "RamaLama setup already completed, skipping..."
    exit 0
fi

# Check for NVIDIA GPU support
if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "WARNING: nvidia-smi not found. RamaLama will run in CPU mode."
    echo "For GPU acceleration, ensure NVIDIA drivers are installed."
else
    echo "NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader,nounits
fi

# Check if Homebrew is available
if ! command -v brew >/dev/null 2>&1; then
    echo "ERROR: Homebrew not found. Please install Homebrew first."
    exit 1
fi

# Install RamaLama via Homebrew
echo "Installing RamaLama via Homebrew..."
brew install ramalama

# Verify installation
echo "Verifying RamaLama installation..."
if ! command -v ramalama >/dev/null 2>&1; then
    echo "ERROR: RamaLama installation failed"
    exit 1
fi

echo "RamaLama installed successfully!"
ramalama version

echo ""
echo "=== System GPU Information ==="
if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=name,driver_version,memory.total,driver_version --format=csv,noheader,nounits
    echo ""
    echo "GPU support detected. RamaLama should automatically use GPU acceleration when available."
else
    echo "No NVIDIA GPU detected. RamaLama will use CPU."
fi

echo ""
echo "RamaLama setup completed successfully!"
echo ""
echo "=== Getting Started with RamaLama ==="
echo "To download and run a model:"
echo "  ramalama serve llama3.2:3b"
echo "  ramalama run llama3.2:3b"
echo ""
echo "To list available models:"
echo "  ramalama list"
echo ""
echo "Monitor GPU usage while running models:"
echo "  watch -n 1 nvidia-smi"
echo ""
echo "For more information:"
echo "  ramalama --help"
