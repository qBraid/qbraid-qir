# Documentation

<div>
    <h1 style="text-align: center">
        <img src="_static/logo.png" alt="qbraid logo" style="width:50px;height:50px;">
        <span> qBraid</span>
        <span style="color:#808080"> | QIR</span>
    </h1>
    <p style="text-align:center;font-style:italic;color:#808080">
        qBraid-SDK extension providing support for QIR conversions.
    </p>
</div>

Release: |release|

Python package for generating QIR programs from Cirq, OpenQASM 3, and other high-level quantum programming languages. This project aims to make QIR (Quantum Intermediate Representation) accessible via the qBraid-SDK [transpiler](https://docs.qbraid.com/en/latest/sdk/transpiler.html), and by doing so, open the door to language-specific conversions from any and all high-level quantum languages supported by `qbraid`.

"*Interoperability* opens doors to cross-fields problem-solving." - QIR Alliance: [Why do we need it?](https://www.qir-alliance.org/qir-book/concepts/why-do-we-need.html).

## Installation

```bash
pip install qbraid-qir
```

## Test container

Docker image providing an environment for testing and executing QIR programs with the [qir-runner](https://github.com/qir-alliance/qir-runner) package.

Clone to `qbraid-qir` repository:

```bash
git clone https://github.com/qBraid/qbraid-qir.git
cd qbraid-qir
```

Build the QIR runner image:

```bash
docker build -t qbraid-test/qir-runner:latest qir_runner
```

Start the container running a Jupyter Server with the JupyterLab frontend and expose
the container's internal port ``8888`` to port ``8888`` of the host machine:

```bash
docker run -p 8888:8888 qbraid-test/qir-runner:latest
```

Visiting ``http://<hostname>:8888/?token=<token>`` in a browser will launch JupyterLab, where:

- The hostname is the name of the computer running Docker (e.g. ``localhost``)
- The token is the secret token printed in the console.

Alternatively, you can open a shell inside the running container directly:

```bash
docker exec -it <container_name> /bin/bash
```

*See also:*

- [https://github.com/qBraid/qbraid-qir/tree/main/test-containers](https://github.com/qBraid/qbraid-qir/tree/main/test-containers)

## Acknowledgements

This project was conceived in cooperation with the Quantum Open Source Foundation ([QOSF](https://qosf.org/)).

<table>
  <tr>
    <td align="center" style="padding: 10px; vertical-align: middle;">
      <a href="https://www.qir-alliance.org/">
        <img src="_static/pkg-logos/qir.png" width="100px" style="vertical-align: middle;"/>
      </a>
    </td>
    <td align="center" style="padding: 10px; vertical-align: middle;">
      <a href="https://docs.qbraid.com/en/latest/">
        <img src="_static/pkg-logos/qbraid.png" width="100px" style="vertical-align: middle;"/>
      </a>
    </td>
    <td align="center" style="padding: 10px; vertical-align: middle;">
      <a href="https://quantumai.google/cirq">
        <img src="_static/pkg-logos/cirq.png" width="100px" style="vertical-align: middle;"/>
      </a>
    </td>
    <td align="center" style="padding: 10px; vertical-align: middle;">
      <a href="https://qosf.org/">
        <img src="_static/pkg-logos/qosf.png" width="100px" style="vertical-align: middle;"/>
      </a>
    </td>
  </tr>
</table>

```{toctree}
:maxdepth: 1
:caption: User Guide
:hidden:

userguide/cirq_qir.md
userguide/qasm3_qir.md
userguide/qasm3_supported.md
```

```{toctree}
:maxdepth: 1
:caption: API Reference
:hidden:

api/qbraid_qir
api/qbraid_qir.cirq
api/qbraid_qir.qasm3
api/qbraid_qir.runner
```
