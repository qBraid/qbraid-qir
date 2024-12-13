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

### 🌟  Improvements
- Update QIR-Runner docker container to `ubuntu:24.04` as base image ([#173](https://github.com/qBraid/qbraid-qir/pull/173))
- Changed examples notebook to sub-module linked to [qbraid-lab-demo](https://github.com/qBraid/qbraid-lab-demo) repo. ([#178](https://github.com/qBraid/qbraid-qir/pull/178))
- Improved typing in `qbraid_qir.qasm3.linalg` ([#178](https://github.com/qBraid/qbraid-qir/pull/178))
- Updated project metadata and README in anticipation of release v0.3 ([#178](https://github.com/qBraid/qbraid-qir/pull/178))

### 📜  Documentation
- Updated sphinx docs pages with PyQASM API reference links ([#174](https://github.com/qBraid/qbraid-qir/pull/174))
- Updated custom CSS so that stable/latest drop-down is visible for navigation. Before blended in white with background ([#185](https://github.com/qBraid/qbraid-qir/pull/185))
- Updated examples sub-module links, and added note in `CONTRIBUTING.md` about how to so ([#185](https://github.com/qBraid/qbraid-qir/pull/185))
- Updated `CONTRIBUTING.md` with latest linters commands instructions ([#185](https://github.com/qBraid/qbraid-qir/pull/185))

### 🐛  Bug Fixes

### ⬇️  Dependency Updates 
- Added `pyqasm` as project dependency ([#173](https://github.com/qBraid/qbraid-qir/pull/173))
- Updated `pyqasm` and `qbraid` dependencies ([#183](https://github.com/qBraid/qbraid-qir/pull/183))

### 👋  Deprecations
- Removed `qbraid_qir.qasm3.linag` module in favor of `pyqasm.linalg` ([#190](https://github.com/qBraid/qbraid-qir/pull/190))
