# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and inspired by the [Pennylane changelog](https://github.com/PennyLaneAI/pennylane/blob/master/doc/releases/changelog-dev.md). This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Types of changes:
- `New Features` : for new features.
- `Improvements` : for improvements to existing functionality.
- `Documentation` : for any additions to documentation.
- `Bug Fixes` : for any bug fixes.
- `Dependency updates` : for any dependency changes
- `Deprecations` (optional) : for soon-to-be removed features.

## [Unreleased]

### ➕  New Features 
* Add support for pauli measurement operators in `cirq` converter ( [#144](https://github.com/qBraid/qbraid-qir/pull/144) )
* Add support for `sizeof` operator in `openqasm` converter ( [#146](https://github.com/qBraid/qbraid-qir/pull/146) )
* Add complete support for `array` type in subroutines ( [#151](https://github.com/qBraid/qbraid-qir/pull/151) )

### 🌟  Improvements 
* Re-factor the `BasicQasmVisitor` and improve modularity ( [#142](https://github.com/qBraid/qbraid-qir/pull/142) )
* Add static type checking with `mypy` ( [#150](https://github.com/qBraid/qbraid-qir/pull/150) )
* Improve measurement statement parsing logic and add support for range definition and discrete set ( [#150](https://github.com/qBraid/qbraid-qir/pull/150) )
* Expanded support for parameters used in gate body expressions. Initially, if a statement inside a gate body used its parameters in arbitrary expressions, the expression was not evaluated correctly as the identifiers were not replaced. ( [#157](https://github.com/qBraid/qbraid-qir/pull/157) ). Example - 

```c++
// previous  
gate my_gate(a, b) q {
    rx(a) q;
    ry(b) q;

    // this was not supported 
    rz(5 * a) q;
}

// current 
gate my_gate(a, b) q {
    rz(a) q;

    // expressions supported now
    rx(a * 3.2) q; 
    ry(a / b + pi) q;
}
```

### 📜  Documentation 
* Housekeeping updates for release ( [#135](https://github.com/qBraid/qbraid-qir/pull/135) )
* Update `CHANGELOG.md` to add new template ( [#137](https://github.com/qBraid/qbraid-qir/pull/137) )
* Update `CONTRIBUTING.md` to mention changelog updates ( [#140](https://github.com/qBraid/qbraid-qir/pull/140) )

### 🐛  Bug Fixes
* Fix function block issues where qubit references were not getting populated correctly. Users can now use `for`, `switch` and other constructs inside functions. ( [#141](https://github.com/qBraid/qbraid-qir/pull/141) )

### ⬇️  Dependency Updates 
* Update sphinx-autodoc-typehints requirement from <2.3,>=1.24 to >=1.24,<2.4 ( [#152](https://github.com/qBraid/qbraid-qir/pull/152) )
* Update sphinx-autodoc-typehints requirement from <2.4,>=1.24 to >=1.24,<2.5 ( [#153](https://github.com/qBraid/qbraid-qir/pull/153) )

### 👋  Deprecations

**Full Changelog**: https://github.com/qBraid/qbraid-qir/compare/v0.2.1...v0.2.2
