# Copyright (C) 2024 qBraid Development Team.
# Distributed under terms of the GNU General Public License v3.
FROM jupyter/minimal-notebook:latest

USER root

RUN apt-get update --yes && apt-get install --yes --no-install-recommends \
    # Basic utilities
    vim \
    git \
    curl \
    jq \
    pkg-config \
    lsb-release \
    wget \
    software-properties-common \
    gnupg \
    # SSL related dependencies
    openssl \
    libssl-dev \
    # Build dependencies
    g++ \
    ninja-build \
    cmake \
    gfortran \
    build-essential \
    # Mathematical libraries
    libblas-dev \
    libopenblas-dev \
    liblapack-dev \
    # Compression library
    libz-dev \
    # LLVM dependencies
    clang-format \
    clang-tidy \
    clang-tools \
    clang \
    clangd \
    libc++-dev \
    libc++1 \
    libc++abi-dev \
    libc++abi1 \
    libclang-dev \
    libclang1 \
    liblldb-dev \
    libllvm-ocaml-dev \
    libomp-dev \
    libomp5 \
    lld \
    lldb \
    llvm-dev \
    llvm-runtime \
    llvm \
    python3-clang

USER $NB_UID

# Install Rustup: https://www.rust-lang.org/tools/install
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Set PATH to include Cargo's bin directory
ENV PATH="$HOME/.cargo/bin:${PATH}"

USER root

# Install LLVM
RUN bash -c "$(wget -O - https://apt.llvm.org/llvm.sh)"

# Clone and build qir-runner
RUN git clone https://github.com/qir-alliance/qir-runner.git /opt/qir-runner && \
    chown -R $NB_UID:$NB_GID /opt/qir-runner

USER $NB_UID

WORKDIR /opt/qir-runner

# Install llvmenv and build qir-runner
RUN cargo install llvmenv && \
    cargo build --release

ENV PATH="/opt/qir-runner/target/release:${PATH}"

WORKDIR $HOME