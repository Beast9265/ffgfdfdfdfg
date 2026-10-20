# Linux build/test environment for the host-side tools (shim cross-compile,
# boot images, QEMU). The XNU kernel itself still builds on GitHub's macOS runners.
#   docker build -t ios-sweet-dev tools/docker
#   docker run --rm -it -v "$PWD:/src" -w /src ios-sweet-dev
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu gcc libc6-dev make \
        qemu-system-arm python3 cpio gzip mkbootimg android-sdk-libsparse-utils \
        device-tree-compiler llvm file xxd ca-certificates \
    && rm -rf /var/lib/apt/lists/*
