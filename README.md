# qbraid-qir

<p align="left">
  <a href="https://github.com/qBraid/qbraid-qir/actions/workflows/main.yml">
      <img src="https://github.com/qBraid/qbraid-qir/actions/workflows/main.yml/badge.svg" alt="CI">
  </a>
  <a href="https://www.gnu.org/licenses/gpl-3.0.html">
    <img src="https://img.shields.io/github/license/qBraid/qbraid.svg" alt="License"/>
  </a>
  <a href="https://discord.gg/TPBU2sa8Et">
    <img src="https://img.shields.io/discord/771898982564626445.svg?color=pink" alt="Discord"/>
  </a>
</p>

*Work in progress*

qBraid-SDK extension providing support for QIR conversions

## Planned features

This project aims to make [QIR](https://www.qir-alliance.org/) representations accessible via the qBraid-SDK hub and spokes [model](#architecture-diagram), and by doing so, open the door to language-specific conversions from any and all high-level quantum languages [supported](https://docs.qbraid.com/en/latest/sdk/overview.html#supported-frontends) by `qbraid`.

- [ ] Cirq $\rightarrow$ QIR
  - [ ] Quantum operations
  - [ ] Classical operations
- [ ] OpenQASM 3 $\rightarrow$ QIR

See: https://www.qir-alliance.org/qir-book/concepts/why-do-we-need.html

## Local install

```bash
git clone https://github.com/qBraid/qbraid-qir.git
cd qbraid-qir
pip install -e .
```

## Run tests

```bash
pip install -r requirements-dev.txt
pytest tests
```

with coverage report

```bash
pytest --cov=qbraid_qir --cov-report=term tests/
```

## Build docs

```bash
cd docs
pip install -r requirements.txt
make html
```

## Architecture diagram

![architecture](https://github.com/qBraid/qbraid-qir/assets/46977852/64da00e3-ca11-443d-b9d0-66a2a71dca0f)

## Running a Minimal Working Example