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
