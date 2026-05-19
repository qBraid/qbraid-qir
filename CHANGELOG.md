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

### ⬇️  Dependency Updates

### 👋  Deprecations

## Past releases

Release notes for earlier versions are published on the [Releases](https://github.com/qBraid/qbraid-qir/releases) page.