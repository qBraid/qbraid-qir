<img width="full" alt="qbraid-qir-header" src="https://github.com/qBraid/qbraid-qir/assets/46977852/39f921ae-c4bf-442a-b059-6b21abd2ae50">

<p align='center'>
  <a href='https://github.com/qBraid/qbraid-qir/actions/workflows/main.yml'>
      <img src='https://github.com/qBraid/qbraid-qir/actions/workflows/main.yml/badge.svg' alt='CI'>
  </a>
  <a href="https://codecov.io/gh/qBraid/qbraid-qir" >
    <img src="https://codecov.io/gh/qBraid/qbraid-qir/graph/badge.svg?token=GUQ3EN8DGI"/>
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

qBraid-SDK extension providing support for QIR conversions.

[<img src="https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png" width="150">](https://account.qbraid.com?gitHubUrl=https://github.com/qBraid/qbraid-qir.git)

## Motivation

<!DOCTYPE html>
<html>
<head>
    <title>Two Column Layout</title>
    <style>
        .container {
            display: flex;
            justify-content: space-between;
        }
        .left-column {
            width: 90%;
        }
        .right-column {
            width: 10%;
            text-align: right; /* Adjusts alignment of content in the right column */
        }
        .right-column img {
            width: 100px; /* Adjust image width as needed */
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="left-column">
            This project aims to make <a href="https://www.qir-alliance.org/">QIR</a> representations accessible via the qBraid-SDK <a href="#architecture-diagram">transpiler</a>, and by doing so, open the door to language-specific conversions from any and all high-level quantum languages <a href="https://docs.qbraid.com/en/latest/sdk/overview.html#supported-frontends">supported</a> by <code>qbraid</code>. See QIR Alliance: <a href="https://www.qir-alliance.org/qir-book/concepts/why-do-we-need.html">why do we need it?</a>.
        </div>
        <div class="right-column">
            <a href="https://www.qir-alliance.org/"><img src="docs/_static/pkg-logos/qir.png" style="vertical-align: middle;" /></a>
        </div>
    </div>
</body>
</html>

## Getting started

### Installation

qBraid-QIR requires Python 3.8 or greater, and can be installed with pip as follows:

```shell
pip install qbraid-qir
```

You can also install from source by cloning this repository and running a pip install command
in the root directory of the repository:

```shell
git clone https://github.com/qBraid/qbraid-qir.git
cd qbraid-qir
pip install .
```

### Check version

You can view the version of qbraid-qir you have installed within a Python shell as follows:

```python
In [1]: import qbraid_qir

In [2]: qbraid_qir.__version__
```

### Resources

- [User Guide](https://docs.qbraid.com/projects/qir/)
- [API Reference](https://docs.qbraid.com/projects/qir/en/latest/api/qbraid_qir.html)
- [Example Notebooks](examples)
- [Test Containers](test-containers)

### Usage Example

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

### Add QIR node to qBraid conversion graph

```python
from qbraid_qir.cirq import cirq_to_qir
from qbraid.transpiler import Conversion, ConversionGraph

graph = ConversionGraph()

conversion = Conversion("cirq", "qir", cirq_to_qir)

graph.add_conversion(conversion)

graph.plot()
```

## Architecture diagram

qBraid-SDK transpiler hub-and-spokes [architecture](https://docs.qbraid.com/en/latest/sdk/transpiler.html#architecture) with qbraid-qir integration (left) mapped to language specific conversion step in QIR abstraction [layers](https://www.qir-alliance.org/qir-book/concepts/why-do-we-need.html) (right).

<img width="full" alt="architecture" src="https://github.com/qBraid/qbraid-qir/assets/46977852/36644614-2715-4f08-8a8c-8a2e61aebf38">

## Contributing

- Interested in contributing code, or making a PR? See
  [CONTRIBUTING.md](CONTRIBUTING.md)
- For feature requests and bug reports:
  [Submit an issue](https://github.com/qBraid/qbraid-qir/issues)
- For discussions, and specific questions about the qBraid-SDK, qBraid-QIR, or
  other topics, [join our discord community](https://discord.gg/TPBU2sa8Et)
- For questions that are more suited for a forum, post to
  [Quantum Computing Stack Exchange](https://quantumcomputing.stackexchange.com/)
  with the [`qbraid`](https://quantumcomputing.stackexchange.com/questions/tagged/qbraid) tag.
- By participating, you are expected to uphold our [code of conduct](CODE_OF_CONDUCT).

## Citation

If you use qBraid-QIR in your research, we kindly request that you cite it appropriately.
The bibtex entry below is aligned with the latest stable release. For the most up-to-date
citation details, please refer to [CITATION.cff](CITATION.cff).

```tex
@software{Kushnir_qBraid-QIR_Python_package_2024,
author = {Kushnir, Samuel and Jain, Rohan and Parakh, Priyansh and Hill, Ryan James},
license = {GPL-3.0},
month = jan,
title = {{qBraid-QIR: Python package for generating QIR programs from Cirq.}},
url = {https://github.com/qBraid/qbraid-qir},
version = {0.1.0},
year = {2024}
}
```

## Acknowledgements

This project was conceived in cooperation with the Quantum Open Source Foundation ([QOSF](https://qosf.org/)).

<a href="https://qosf.org/"><img src="docs/_static/pkg-logos/qosf.png" width="100px" style="vertical-align: middle;" /></a>

## License

[GNU General Public License v3.0](LICENSE)
