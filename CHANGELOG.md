# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Types of changes:
- `New Features`: for new features.
- `Improvements`: for improvements to existing functionality.
- `Documentation`: for any additions to documentation.
- `Bug Fixes`: for any bug fixes.
- `Dependency updates`: for any dependency changes
- `Deprecations` (optional): for soon-to-be removed features.

## [Unreleased]

### ➕  New Features 
- Added a QIR to `squin` conversion method which allows users to execute QIR programs on `squin` enabled backends. This feature also opens up the Squin representation to many formats such as QASM, and Cirq using the built in qbraid-qir converters. Eg. - ([#252](https://github.com/qBraid/qbraid-qir/pull/252))

```python
# Converting a PyQIR module to squin
from qbraid_qir.squin import load
from pyqir import BasicQisBuilder, SimpleModule

mod = SimpleModule("ghz", num_qubits=3, num_results=3)
qis = BasicQisBuilder(mod.builder)

qis.h(mod.qubits[0])
qis.cx(mod.qubits[0], mod.qubits[1])
qis.cx(mod.qubits[1], mod.qubits[2])

squin_kernel = load(mod._module)
squin_kernel.print()
```

Output:
```stdout
func.func @main() -> !py.NoneType {
  ^0(%main_self):
  │ %0 = func.invoke new() : !py.Qubit maybe_pure=False
  │ %1 = func.invoke new() : !py.Qubit maybe_pure=False
  │ %2 = func.invoke h(%0) : !py.NoneType maybe_pure=False
  │ %3 = func.invoke x(%0) : !py.NoneType maybe_pure=False
  │ %4 = func.invoke x(%1) : !py.NoneType maybe_pure=False
  │ %5 = py.constant.constant 1.5707963267948966 : !py.float
  │ %6 = func.invoke rx(%5, %0) : !py.NoneType maybe_pure=False
  │ %7 = func.const.none() : !py.NoneType
  │      func.return %7
} // func.func main

```


### 🌟  Improvements
- Split `qbraid_qir.profile` into `qbraid_qir.module` and `qbraid_qir.visitor` ([#237](https://github.com/qBraid/qbraid-qir/pull/237))

- Improved circuit pre-processing for Cirq converter using Cirq's built-in `optimize_for_target_gateset` ([#248](https://github.com/qBraid/qbraid-qir/pull/248)) 

- Fix types in the `cirq` converter ([#255](https://github.com/qBraid/qbraid-qir/pull/255)) 

### 📜  Documentation
- Factor out docs deps into its own requirements file ([#237](https://github.com/qBraid/qbraid-qir/pull/237))

### 🐛  Bug Fixes

### ⬇️  Dependency Updates 
- Update `pyqasm` requirement from >=0.4.0,<0.5.0 to >=0.4.0,<0.6.0 ([#236](https://github.com/qBraid/qbraid-qir/pull/236))
- Update docutils requirement from <0.22 to <0.23 ([#238](https://github.com/qBraid/qbraid-qir/pull/238))
- Bump actions/upload-pages-artifact from 3 to 4 ([#241](https://github.com/qBraid/qbraid-qir/pull/241))
- Update pyqasm requirement from <0.6.0,>=0.4.0 to >=0.4.0,<1.1.0 ([#245](https://github.com/qBraid/qbraid-qir/pull/245))
- Update qbraid requirement from <0.10.0,>=0.9.0 to >=0.9.0,<0.11.0 ([#247](https://github.com/qBraid/qbraid-qir/pull/247))
- Bump actions/download-artifact from 5 to 6 ([#249](https://github.com/qBraid/qbraid-qir/pull/249))
- Bump actions/upload-artifact from 4 to 5 ([#250](https://github.com/qBraid/qbraid-qir/pull/250))
- Bump actions/checkout from v5 to v6 ([#254](https://github.com/qBraid/qbraid-qir/pull/254))


### 👋  Deprecations
