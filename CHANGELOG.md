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

- **PyQIR 0.12+ support**: Add compatibility for pyqir 0.12+ (opaque pointers / QIR 2.0) alongside existing 0.10.x support. New `_pyqir_compat` module provides `pointer_id`, `qubit_pointer_type`, and `pyqir_uses_opaque_pointers()` for version-agnostic code. ([#265](https://github.com/qBraid/qbraid-qir/pull/265))

### 🌟  Improvements

- **Backward-compatible PyQIR usage**: Cirq, QASM3, and Squin visitors use the compat layer so the codebase works with both pyqir &lt;0.12 (typed pointers) and ≥0.12 (opaque pointers). ([#265](https://github.com/qBraid/qbraid-qir/pull/265))
- **Version-aware tests**: Test helpers and fixtures choose typed vs opaque pointer expectations based on the installed pyqir version; added version-specific LL fixtures (e.g. `*_typed.ll`, `*_opaque.ll`) for Cirq and QASM3 tests. ([#265](https://github.com/qBraid/qbraid-qir/pull/265))
- **CI: test both PyQIR versions**: GitHub Actions test job runs the full suite with pyqir 0.10.x and 0.12+, then combines coverage and uploads to Codecov. ([#265](https://github.com/qBraid/qbraid-qir/pull/265))
- **Tox: dual PyQIR envs**: New `unit-tests-pyqir10` and `unit-tests-pyqir12` tox environments so `tox` runs unit tests against both pyqir version ranges.
- **Optional test deps**: Skip cudaq-to-Squin tests when cudaq is not installed; skip autoqasm converter tests when autoqasm is not installed. ([#265](https://github.com/qBraid/qbraid-qir/pull/265))

### 📜  Documentation

- **CHANGELOG**: Clarified "Past releases" section with a short description and link to the Releases page. ([#265](https://github.com/qBraid/qbraid-qir/pull/265))

### 🐛  Bug Fixes

- _(none this release)_

### ⬇️  Dependency Updates

- **pyqir**: Relax requirement from `>=0.10.0,<0.11.0` to `>=0.10.0,<0.13.0` so both 0.10.x and 0.12.x are supported. ([#265](https://github.com/qBraid/qbraid-qir/pull/265))

### 👋  Deprecations

- _(none)_

## Past releases

Release notes for earlier versions are published on the [Releases](https://github.com/qBraid/qbraid-qir/releases) page.