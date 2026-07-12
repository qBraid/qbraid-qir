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

- Added `qbraid_qir.qiskit` module for Qiskit to QIR conversion, ported from the archived [microsoft/qiskit-qir](https://github.com/microsoft/qiskit-qir) repository (MIT License). The module has been updated for compatibility with Qiskit 2.x and follows qbraid-qir conventions. Main entry point is `qiskit_to_qir(circuit, name=None, **kwargs)` which converts a Qiskit `QuantumCircuit` to a PyQIR `Module`. ([#272](https://github.com/qBraid/qbraid-qir/issues/272), [#271](https://github.com/qBraid/qbraid-qir/pull/271))

### 🌟  Improvements

### 📜  Documentation

- Updated the `qbraid_qir.squin` module imports and __all__ to explicitly expose `SquinVisitor` and `InvalidSquinInput` alongside `load`, making these components part of the public API.

### 🐛  Bug Fixes

- Fixed `qasm3_to_qir` raising a bare `AssertionError` (with an empty message) for programs that address physical qubits, e.g. `h $0;`. Physical qubits are valid OpenQASM 3 and are what Qiskit emits when a circuit is transpiled against a backend (`qasm3.dumps(transpile(circuit, backend))`), but they survive unrolling as plain `Identifier` nodes rather than `IndexedIdentifier`, which the visitor assumed. They now lower to the QIR qubit of the same index (`$3` is qubit 3), and the entry point declares enough qubits to cover the highest index used. Operands the visitor cannot lower now raise `Qasm3ConversionError` with a message instead of an empty `AssertionError`.

### ⬇️  Dependency Updates

- Updated `pyqasm` requirement from `>=0.4.0,<1.1.0` to `>=1.0.4,<1.1.0`, which is the first release that preserves physical qubits in `reset` statements rather than rewriting them to the internal pulse register.
- Updated `autoqasm` requirement from `>=0.1.0` to `>=0.2.0` ([#278](https://github.com/qBraid/qbraid-qir/pull/278))
- Updated `qbraid` requirement from `>=0.11.0,<0.12.0` to `>=0.11.1,<0.12.0` ([#279](https://github.com/qBraid/qbraid-qir/pull/279))
- Updated `sphinx` requirement from `>=7.3.7,<=8.3.0` to `>=8.1.3,<=8.3.0` ([#282](https://github.com/qBraid/qbraid-qir/pull/282))
- Updated `sphinx-rtd-theme` requirement from `>=2.0,<3.2` to `>=3.1.0,<3.2` ([#280](https://github.com/qBraid/qbraid-qir/pull/280))
- Updated `sphinx-autodoc-typehints` requirement from `>=1.24,<3.2` to `>=3.0.1,<3.2` ([#281](https://github.com/qBraid/qbraid-qir/pull/281))
- Bumped `actions/configure-pages` from 5 to 6 ([#274](https://github.com/qBraid/qbraid-qir/pull/274))
- Bumped `actions/deploy-pages` from 4 to 5 ([#275](https://github.com/qBraid/qbraid-qir/pull/275))
- Bumped `codecov/codecov-action` from 5.5.2 to 6.0.1 ([#276](https://github.com/qBraid/qbraid-qir/pull/276))

### 👋  Deprecations

## Past releases

Release notes for earlier versions are published on the [Releases](https://github.com/qBraid/qbraid-qir/releases) page.