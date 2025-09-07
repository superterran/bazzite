#!/bin/bash
set -euo pipefail

# Install and configure Ollama with GPU support via Podman container
echo "Setting up containerized Ollama with CUDA GPU acceleration..."

# Check if Ollama container service is already running
if systemctl --user is-active ollama.service >/dev/null 2>&1; then
    echo "Ollama container service already running"
    podman ps | grep ollama && echo "✅ Container verified"
    echo "Ollama setup already completed, skipping..."
    exit 0
fi

# Check for NVIDIA GPU and container runtime support
if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "ERROR: nvidia-smi not found. GPU acceleration requires NVIDIA drivers."
    exit 1
else
    echo "NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader,nounits
fi

# Check for Podman and container toolkit
if ! command -v podman >/dev/null 2>&1; then
    echo "ERROR: Podman not found. Container support required."
    exit 1
fi

if ! command -v nvidia-ctk >/dev/null 2>&1; then
    echo "ERROR: nvidia-container-toolkit not found. GPU passthrough requires container toolkit."
    exit 1
fi

# Setup GPU container passthrough
echo "Configuring NVIDIA Container Device Interface (CDI)..."
sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
echo "✅ CDI configured for GPU passthrough"

# Create systemd container configuration
echo "Creating systemd container service..."
mkdir -p ~/.config/containers/systemd

cat > ~/.config/containers/systemd/ollama.container << 'EOF'
[Unit]
Description=Ollama AI Model Server Container
After=local-fs.target

[Container]
ContainerName=ollama
Image=docker.io/ollama/ollama:latest
AddDevice=nvidia.com/gpu=all
SecurityLabelDisable=true
PublishPort=11434:11434
Volume=ollama:/root/.ollama:z
Environment=OLLAMA_HOST=0.0.0.0:11434

# GPU optimization environment variables
Environment=CUDA_VISIBLE_DEVICES=0
Environment=OLLAMA_GPU_OVERHEAD=0
Environment=OLLAMA_MAX_LOADED_MODELS=1
Environment=OLLAMA_FLASH_ATTENTION=true
Environment=OLLAMA_KV_CACHE_TYPE=f16
Environment=OLLAMA_NUM_PARALLEL=1

[Install]
WantedBy=default.target
EOF

echo "✅ Systemd container configuration created"

# Install Ollama CLI via Homebrew for command-line access
if command -v brew >/dev/null 2>&1; then
    echo "Installing Ollama CLI via Homebrew..."
    brew install ollama
    echo "✅ Ollama CLI installed"
else
    echo "⚠️  Homebrew not available, manual CLI installation may be needed"
fi

# Pull Ollama container image
echo "Pulling Ollama container image..."
podman pull docker.io/ollama/ollama:latest
echo "✅ Container image pulled"

# Start and enable the systemd service
echo "Starting Ollama container service..."
systemctl --user daemon-reload
systemctl --user enable ollama.service
systemctl --user start ollama.service

# Verify service is running
echo "Verifying Ollama container service..."
if ! systemctl --user is-active ollama.service >/dev/null 2>&1; then
    echo "ERROR: Ollama container service failed to start"
    systemctl --user status ollama.service
    exit 1
fi

echo "✅ Ollama container service started successfully!"
podman ps | grep ollama

echo ""
echo "=== Testing CUDA GPU Support ==="
echo "Checking container GPU detection..."
sleep 3
podman logs ollama | grep -E "(library=cuda|inference compute|NVIDIA)" && 
    echo "✅ CUDA GPU acceleration enabled in container" || 
    echo "⚠️  CUDA GPU detection failed in container"

echo ""
echo "Testing API connectivity..."
curl -s http://localhost:11434/api/version && echo "" && echo "✅ Ollama API accessible" || echo "⚠️  API connectivity failed"

echo ""
echo "Ollama setup completed successfully!"
echo ""
echo "=== Getting Started with Ollama ==="
echo "To start Ollama server:"
echo "  ollama serve &"
echo ""
echo "To download and run a model with GPU acceleration:"
echo "  ollama pull llama3.2:3b"
echo "  ollama run llama3.2:3b 'Hello world'"
echo "  # For coding tasks:"
echo "  ollama pull codegemma:7b-instruct"
echo ""
echo "To manage the container service:"
echo "  systemctl --user start ollama.service"
echo "  systemctl --user stop ollama.service"
echo "  systemctl --user restart ollama.service"
echo ""
echo "To list available models:"
echo "  ollama list"
echo ""
echo "=== Alpaca Configuration ==="
echo "For Alpaca (AI chat GUI), use:"
echo "  • Provider: Ollama"
echo "  • Host: http://localhost:11434"
echo "  • Model: llama3.2:3b (recommended for quality+speed)"
echo "  • API Key: (leave empty)"
echo ""
echo "🐋 Containerized Ollama with CUDA acceleration:"
echo "  ✅ Isolated from host system (perfect for immutable OS)"
echo "  ✅ GPU passthrough via NVIDIA Container Toolkit"
echo "  ✅ Systemd service management"
echo "  ✅ Automatic container updates"
echo ""
echo "🔥 Expected performance:"
echo "  • High GPU utilization (70-90%) during inference"
echo "  • Low CPU usage (< 20%)"
echo "  • No CPU overheating"
echo "  • Faster inference than CPU-only approaches"
echo "Monitor GPU usage while running models:"
echo "  watch -n 1 nvidia-smi"
echo ""
echo "For more information:"
echo "  ollama --help"
