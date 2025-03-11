# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM ubuntu:24.04

LABEL maintainer="qBraid Development Team <contact@qbraid.com>" \
      licenses="Apache-2.0" \
      title="qBraid-QIR x QIR bytecode runner" \
      description="Flexible environment with qBraid-QIR and the QIR-Runner (built from source)." \
      version="2.0"

ENV USER=qbraid

ENV HOME=/home/$USER

RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends \
    # Basic utilities
    sudo vim git curl jq pkg-config lsb-release wget software-properties-common gnupg \
    # SSL related dependencies
    openssl libssl-dev \
    # Build dependencies
    g++ ninja-build cmake gfortran build-essential \
    # Mathematical libraries
    libblas-dev libopenblas-dev liblapack-dev \
    # Compression library
    libz-dev \
    # LLVM dependencies
    clang-format clang-tidy clang-tools clang clangd libc++-dev libc++1 libc++abi-dev \
    libc++abi1 libclang-dev libclang1 liblldb-dev libllvm-ocaml-dev libomp-dev \
    libomp5 lld lldb llvm-dev llvm-runtime llvm python3-clang \
    libpolly-18-dev libzstd-dev \
    # Python interpreter and package managers 
    python3 python3-pip python3-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash $USER && \
    echo "$USER ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER $USER

# Install Rustup: https://www.rust-lang.org/tools/install
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

ENV PATH="$HOME/.cargo/bin:${PATH}"

USER root

# Ensure we have the latest stable toolchain (≥ 1.81)
RUN rustup update stable && rustup default stable

RUN git clone https://github.com/qir-alliance/qir-runner.git /opt/qir-runner && \
    chown -R $USER:$USER /opt/qir-runner

USER $USER

WORKDIR /opt/qir-runner

RUN cargo install llvmenv && \
    cargo build --release

ENV PATH="/opt/qir-runner/target/release:${PATH}"

WORKDIR /work

RUN python3 -m venv venv && \
    venv/bin/python3 -m pip install --upgrade pip && \
    venv/bin/python3 -m pip install qbraid qbraid-qir[cirq,qasm3] qbraid-core[runner] && \
    rm -rf $(venv/bin/python3 -m pip cache dir)

COPY --chown=USER:USER ./examples examples