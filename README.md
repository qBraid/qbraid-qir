<img width="full" alt="qbraid-qir-header" src="https://github.com/qBraid/qbraid-qir/assets/46977852/39f921ae-c4bf-442a-b059-6b21abd2ae50">

<p align='center'>
  <a href='https://github.com/qBraid/qbraid-qir/actions/workflows/main.yml'>
      <img src='https://github.com/qBraid/qbraid-qir/actions/workflows/main.yml/badge.svg' alt='CI'>
  </a>
  <a href='https://docs.qbraid.com/projects/qir/en/latest/?badge=latest'>
    <img src='https://readthedocs.com/projects/qbraid-qbraid-qir/badge/?version=latest&token=7656ee72b7a66dec6d78dda911ce808676dca55c3e86702d5e97191badfdf19c' alt='Documentation Status'/>
  </a>
  <a href="https://pypi.org/project/qbraid-qir/">
    <img src="https://img.shields.io/pypi/v/qbraid-qir.svg?color=blue" alt="PyPI version"/>
  </a>
  <a href="https://pypi.org/project/qbraid-qir/">
    <img src="https://img.shields.io/pypi/pyversions/qbraid-qir.svg?color=blue" alt="PyPI version"/>
  </a>
  <a href='https://www.gnu.org/licenses/gpl-3.0.html'>
    <img src='https://img.shields.io/github/license/qBraid/qbraid.svg' alt='License'/>
  </a>
  <a href='https://discord.gg/TPBU2sa8Et'>
    <img src='https://img.shields.io/discord/771898982564626445.svg?color=pink' alt='Discord'/>
  </a>
</p>

*Work in progress*

qBraid-SDK extension providing support for QIR conversions.

This project aims to make [QIR](https://www.qir-alliance.org/) representations accessible via the qBraid-SDK [transpiler](#architecture-diagram), and by doing so, open the door to language-specific conversions from any and all high-level quantum languages [supported](https://docs.qbraid.com/en/latest/sdk/overview.html#supported-frontends) by `qbraid`. See QIR Alliance: [why do we need it?](https://www.qir-alliance.org/qir-book/concepts/why-do-we-need.html).

## Getting started

### Installation

```bash
pip install qbraid-qir
```

### Example

```python
import cirq
from qbraid_qir import cirq_to_qir

q0, q1 = cirq.LineQubit.range(2)

circuit = cirq.Circuit(
  cirq.H(q0),
  cirq.CNOT(q0, q1),
  cirq.measure(q0, q1)
)

module = cirq_to_qir(circuit, name="my-circuit")

ir = str(module)
```

## Development

### Install from source

```bash
git clone https://github.com/qBraid/qbraid-qir.git
cd qbraid-qir
pip install -e .
```

### Run tests

```bash
pip install -r requirements-dev.txt
pytest tests
```

with coverage report

```bash
pytest --cov=qbraid_qir --cov-report=term tests/
```

### Build docs

```bash
cd docs
pip install -r requirements.txt
make html
```

## Architecture diagram

![architecture](https://github.com/qBraid/qbraid-qir/assets/46977852/64da00e3-ca11-443d-b9d0-66a2a71dca0f)
