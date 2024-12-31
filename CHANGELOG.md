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
- Add support for externally linked gates in QASM3 ([#182](https://github.com/qBraid/qbraid-qir/pull/182)). Users can now supply a list of external gates to the unroll method and the unroller will leave these gates as is. Usage - 
```python
In [14]: from qbraid_qir.qasm3 import qasm3_to_qir

In [15]: qasm = """OPENQASM 3.0;
    ...: include "stdgates.inc";
    ...: gate mygate(p0) _gate_q_0, _gate_q_1 {
    ...:   h _gate_q_1;
    ...:   cx _gate_q_0, _gate_q_1;
    ...:   rz(p0) _gate_q_1;
    ...:   cx _gate_q_0, _gate_q_1;
    ...:   h _gate_q_1;
    ...: }
    ...: bit[2] c;
    ...: qubit[2] q;
    ...: ry(pi/2) q[0];
    ...: mygate(pi/2) q[0], q[1];"""

In [16]: result = qasm3_to_qir(qasm, external_gates=["mygate"])

In [17]: str(result).splitlines()
Out[17]: 
["; ModuleID = 'program-295790fc-c761-11ef-9fef-cae339f58536'",
 'source_filename = "program-295790fc-c761-11ef-9fef-cae339f58536"',
 '',
 '%Qubit = type opaque',
 '%Result = type opaque',
 '',
 'define void @program-295790fc-c761-11ef-9fef-cae339f58536() #0 {',
 'entry:',
 '  call void @__quantum__rt__initialize(i8* null)',
 '  call void @__quantum__qis__ry__body(double 0x3FF921FB54442D18, %Qubit* null)',
 '  call void @__quantum__qis__mygate__body(double 0x3FF921FB54442D18, %Qubit* null, %Qubit* inttoptr (i64 1 to %Qubit*))',
 '  call void @__quantum__rt__result_record_output(%Result* null, i8* null)',
 '  call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 1 to %Result*), i8* null)',
 '  ret void',
 '}',
 '',
 'declare void @__quantum__rt__initialize(i8*)',
 '',
 'declare void @__quantum__qis__ry__body(double, %Qubit*)',
 '',
 'declare void @__quantum__qis__mygate__body(double, %Qubit*, %Qubit*)',
 '',
 'declare void @__quantum__rt__result_record_output(%Result*, i8*)',
 '',
 'attributes #0 = { "entry_point" "output_labeling_schema" "qir_profiles"="custom" "required_num_qubits"="2" "required_num_results"="2" }',
 '',
 '!llvm.module.flags = !{!0, !1, !2, !3}',
 '',
 '!0 = !{i32 1, !"qir_major_version", i32 1}',
 '!1 = !{i32 7, !"qir_minor_version", i32 0}',
 '!2 = !{i32 1, !"dynamic_qubit_management", i1 false}',
 '!3 = !{i32 1, !"dynamic_result_management", i1 false}']
```

### 🌟  Improvements
- Update QIR-Runner docker container to `ubuntu:24.04` as base image ([#173](https://github.com/qBraid/qbraid-qir/pull/173))
- Update lazy imports in QIR, and add linalg tests ([#176](https://github.com/qBraid/qbraid-qir/pull/176))
- Changed examples notebook to sub-module linked to [qbraid-lab-demo](https://github.com/qBraid/qbraid-lab-demo) repo. ([#178](https://github.com/qBraid/qbraid-qir/pull/178))
- Improved typing in `qbraid_qir.qasm3.linalg` ([#178](https://github.com/qBraid/qbraid-qir/pull/178))
- Updated project metadata and README in anticipation of release v0.3 ([#178](https://github.com/qBraid/qbraid-qir/pull/178))

### 📜  Documentation
- Updated sphinx docs pages with PyQASM API reference links ([#174](https://github.com/qBraid/qbraid-qir/pull/174))
- Updated custom CSS so that stable/latest drop-down is visible for navigation. Before blended in white with background ([#185](https://github.com/qBraid/qbraid-qir/pull/185))
- Updated examples sub-module links, and added note in `CONTRIBUTING.md` about how to so ([#185](https://github.com/qBraid/qbraid-qir/pull/185))
- Updated `CONTRIBUTING.md` with latest linters commands instructions ([#185](https://github.com/qBraid/qbraid-qir/pull/185))

### 🐛  Bug Fixes
- Fix broken links for notebook examples ([#180](https://github.com/qBraid/qbraid-qir/pull/180))

### ⬇️  Dependency Updates 
- Added `pyqasm` as project dependency ([#173](https://github.com/qBraid/qbraid-qir/pull/173))
- Updated `pyqasm` and `qbraid` dependencies ([#181](https://github.com/qBraid/qbraid-qir/pull/181) [#183](https://github.com/qBraid/qbraid-qir/pull/183))
- Bump `pyqasm` version to `0.1.0` ([#189](https://github.com/qBraid/qbraid-qir/pull/189))
- Update qbraid requirement from <0.9.0,>=0.8.3 to >=0.8.3,<0.10.0 ([#191](https://github.com/qBraid/qbraid-qir/pull/191))

### 👋  Deprecations
- Removed `qbraid_qir.qasm3.linag` module in favor of `pyqasm.linalg` ([#190](https://github.com/qBraid/qbraid-qir/pull/190))
