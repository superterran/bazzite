# Custom Bazzite build commands

# Build handheld variant (ROG Ally X)
build-handheld:
    docker build --target handheld -t bazzite:handheld .

# Build desktop variant (NVIDIA)
build-desktop:
    docker build --target desktop -t bazzite:desktop .

# Build both variants
build-all: build-handheld build-desktop

# Run handheld variant interactively
run-handheld: build-handheld
    docker run -it --rm bazzite:handheld /bin/bash

# Run desktop variant interactively  
run-desktop: build-desktop
    docker run -it --rm bazzite:desktop /bin/bash

# Build and tag for registry push
build-handheld-release:
    docker build --target handheld -t ghcr.io/superterran/bazzite:handheld .

build-desktop-release:
    docker build --target desktop -t ghcr.io/superterran/bazzite:desktop .

# Push to registry (requires login)
push-handheld: build-handheld-release
    docker push ghcr.io/superterran/bazzite:handheld

push-desktop: build-desktop-release
    docker push ghcr.io/superterran/bazzite:desktop

push-all: push-handheld push-desktop

# Clean up local images
clean:
    docker rmi bazzite:handheld bazzite:desktop || true
    docker rmi ghcr.io/superterran/bazzite:handheld ghcr.io/superterran/bazzite:desktop || true

# User setup commands
user-setup:
    ./user-setup.sh

# Smart setup (detects system type)
setup:
    ./setup.sh

# Desktop-specific setup (OpenRGB, etc.)
desktop-setup:
    ./desktop-setup.sh desktop

# Backup current system configuration
backup-config:
    ./backup-config.sh

# Rebase to desktop variant (local testing)
rebase-desktop-local:
    sudo rpm-ostree rebase ostree-unverified-registry:localhost/bazzite:desktop

# Rebase to handheld variant (local testing)
rebase-handheld-local:
    sudo rpm-ostree rebase ostree-unverified-registry:localhost/bazzite:handheld

# Test what packages are in the built image
test-desktop-packages:
    docker run --rm bazzite:desktop rpm -qa | grep -E "(docker-compose|gnome-boxes|podman-docker|warp-terminal|code|1password)" | sort

# Test handheld packages
test-handheld-packages:
    docker run --rm bazzite:handheld rpm -qa | grep -E "(docker-compose|gnome-boxes|podman-docker|warp-terminal|code|1password)" | sort
