# Custom Bazzite build commands

# Build handheld variant (ROG Ally X)
build-handheld:
    docker build --target handheld -t bazzite:handheld .

# Build desktop variant (NVIDIA)
build-desktop:
    docker build --target desktop -t bazzite:desktop .

# Build both variants
build-all: build-handheld build-desktop

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
