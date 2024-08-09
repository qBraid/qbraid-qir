<img width="full" alt="qbraid-qir-header" src="https://github.com/qBraid/qbraid-qir/assets/46977852/39f921ae-c4bf-442a-b059-6b21abd2ae50">

<p align='center'>
  <a href='https://github.com/qBraid/qbraid-qir/actions/workflows/main.yml'>
      <img src='https://github.com/qBraid/qbraid-qir/actions/workflows/main.yml/badge.svg' alt='CI'>
  </a>
  <a href='https://sdk.qbraid.com/projects/qir/en/latest/?badge=latest'>
    <img src='https://readthedocs.com/projects/qbraid-qbraid-qir/badge/?version=latest&token=7656ee72b7a66dec6d78dda911ce808676dca55c3e86702d5e97191badfdf19c' alt='Documentation Status'/>
  </a>
  <a href="https://codecov.io/gh/qBraid/qbraid-qir">
    <img src="https://codecov.io/gh/qBraid/qbraid-qir/graph/badge.svg?token=GUQ3EN8DGI"/>
  </a>
  <a href="https://pypi.org/project/qbraid-qir/">
    <img src="https://img.shields.io/pypi/v/qbraid-qir.svg?color=blue" alt="PyPI version"/>
  </a>
  <a href="https://pypi.org/project/qbraid-qir/">
    <img src="https://img.shields.io/pypi/pyversions/qbraid-qir.svg?color=blue" alt="PyPI version"/>
  </a>
<!--   <a href="https://pepy.tech/project/qbraid-qir">
    <img src="https://static.pepy.tech/badge/qbraid-qir" alt="Downloads"/>
  </a> -->
  <a href='https://www.gnu.org/licenses/gpl-3.0.html'>
    <img src='https://img.shields.io/github/license/qBraid/qbraid.svg' alt='License'/>
  </a>
  <a href='https://discord.gg/TPBU2sa8Et'>
    <img src="https://img.shields.io/badge/Discord-%235865F2.svg?logo=discord&logoColor=white" alt="Discord"/>
  </a>
</p>

qBraid-SDK extension providing support for QIR conversions.

[<img src="https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png" width="150">](https://account.qbraid.com?gitHubUrl=https://github.com/qBraid/qbraid-qir.git)

## Motivation

<img align="right" width="100" alt="qir" src="https://qbraid-static.s3.amazonaws.com/logos/qir.png">

This project aims to make [QIR](https://www.qir-alliance.org/) representations accessible via the qBraid-SDK [transpiler](#architecture-diagram), and by doing so, open the door to language-specific conversions from any and all high-level quantum languages [supported](https://docs.qbraid.com/sdk/user-guide/overview#supported-frontends) by `qbraid`. See QIR Alliance: [why do we need it?](https://www.qir-alliance.org/qir-book/concepts/why-do-we-need.html).

## Installation

qBraid-QIR requires Python 3.9 or greater, and can be installed with pip as follows:

```shell
pip install qbraid-qir
```

### Optional dependencies

qBraid-QIR offers integrations that require extra (optional) dependencies, which can be installed as follows:

For OpenQASM 3 to QIR conversions, install the `qasm3` extra:

```shell
pip install 'qbraid-qir[qasm3]'
```

For Cirq to QIR conversions, install the `cirq` extra:

```shell
pip install 'qbraid-qir[cirq]'
```

### Install from source

You can also install from source by cloning this repository and running a pip install command
in the root directory of the repository:

```shell
git clone https://github.com/qBraid/qbraid-qir.git
cd qbraid-qir
pip install .
```

To include optional dependencies when installing from source, use the same "extras_require" format, e.g.

```shell
pip install '.[qasm3,cirq]'
```

## Check version

You can view the version of qbraid-qir you have installed within a Python shell as follows:

```python
In [1]: import qbraid_qir

In [2]: qbraid_qir.__version__
```

## Resources

- [User Guide](https://docs.qbraid.com/qir/user-guide)
- [API Reference](https://sdk.qbraid.com/projects/qir/en/stable/api/qbraid_qir.html)
- [Example Notebooks](examples)
- [Test Containers](test-containers)

## Usage examples

### OpenQASM 3 conversions

```python
from qbraid_qir.qasm3 import qasm3_to_qir

program = """
OPENQASM 3;
include "stdgates.inc";

qubit[2] q;
bit[2] c;

h q[0];
cx q[0], q[1];

measure q[0] -> c[0];
measure q[1] -> c[1];
"""

module = qasm3_to_qir(program, name="my-program")

ir = str(module)
```

### Cirq conversions

```python
import cirq
from qbraid_qir.cirq import cirq_to_qir

q0, q1 = cirq.LineQubit.range(2)

circuit = cirq.Circuit(
  cirq.H(q0),
  cirq.CNOT(q0, q1),
  cirq.measure(q0, q1)
)

module = cirq_to_qir(circuit, name="my-circuit")

ir = str(module)
```

## Architecture diagram

qBraid-SDK transpiler hub-and-spokes [architecture](https://docs.qbraid.com/qir/user-guide/overview#architecture-diagram) with qbraid-qir integration (left) mapped to language specific conversion step in QIR abstraction [layers](https://www.qir-alliance.org/qir-book/concepts/why-do-we-need.html) (right).

<img width="full" alt="architecture" src="https://github.com/qBraid/qbraid-qir/assets/46977852/36644614-2715-4f08-8a8c-8a2e61aebf38">

## Contributing

- Interested in contributing code, or making a PR? See
  [CONTRIBUTING.md](CONTRIBUTING.md)
- For feature requests and bug reports:
  [Submit an issue](https://github.com/qBraid/qbraid-qir/issues)
- For discussions, and specific questions about qBraid-QIR, or
  other topics, [join our discord community](https://discord.gg/TPBU2sa8Et)
- For questions that are more suited for a forum, post to
  [QCSE](https://quantumcomputing.stackexchange.com/)
  with the [`qbraid`](https://quantumcomputing.stackexchange.com/questions/tagged/qbraid) tag.
- By participating, you are expected to uphold our [code of conduct](CODE_OF_CONDUCT).

## Citation

If you use qBraid-QIR in your research, we kindly request that you cite it appropriately.
The BibTeX entry below is aligned with the latest stable release. For the most up-to-date
citation details, please refer to [CITATION.cff](CITATION.cff).

```bibtex
@software{Gupta_qBraid-QIR_Python_package_2024,
  author = {Gupta, Harshit and Jain, Rohan and Kushnir, Samuel and Parakh, Priyansh and Hill, Ryan James},
  license = {GPL-3.0},
  month = aug,
  title = {{qBraid-QIR: Python package for QIR conversions, integrations, and utilities.}},
  url = {https://github.com/qBraid/qbraid-qir},
  version = {0.2.2},
  year = {2024}
}
```

## Acknowledgements

This project was conceived in cooperation with the Quantum Open Source Foundation ([QOSF](https://qosf.org/)).

<a href="https://qosf.org/"><img src="https://qbraid-static.s3.amazonaws.com/logos/qosf.png" width="100px" style="vertical-align: middle;" /></a>

## License

[GNU General Public License v3.0](LICENSE)
