# Copyright 2026 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module mapping supported Qiskit gates/operations to pyqir functions.

"""

from typing import Callable

import pyqir._native

from .exceptions import QiskitConversionError


def _identity(_builder, _qubit):
    """Identity gate — no operation."""


PYQIR_ONE_QUBIT_OP_MAP: dict[str, Callable] = {
    "h": pyqir._native.h,
    "x": pyqir._native.x,
    "y": pyqir._native.y,
    "z": pyqir._native.z,
    "s": pyqir._native.s,
    "sdg": pyqir._native.s_adj,
    "t": pyqir._native.t,
    "tdg": pyqir._native.t_adj,
    "id": _identity,
    "reset": pyqir._native.reset,
}

PYQIR_ONE_QUBIT_ROTATION_MAP: dict[str, Callable] = {
    "rx": pyqir._native.rx,
    "ry": pyqir._native.ry,
    "rz": pyqir._native.rz,
}

PYQIR_TWO_QUBIT_OP_MAP: dict[str, Callable] = {
    "cx": pyqir._native.cx,
    "cz": pyqir._native.cz,
    "swap": pyqir._native.swap,
}

PYQIR_THREE_QUBIT_OP_MAP: dict[str, Callable] = {
    "ccx": pyqir._native.ccx,
}

PYQIR_MEASUREMENT_OP_MAP: dict[str, Callable] = {
    "measure": pyqir._native.mz,
    "m": pyqir._native.mz,
    "mz": pyqir._native.mz,
}

NOOP_INSTRUCTIONS: set[str] = {"delay"}

SUPPORTED_INSTRUCTIONS: list[str] = sorted(
    set(PYQIR_ONE_QUBIT_OP_MAP)
    | set(PYQIR_ONE_QUBIT_ROTATION_MAP)
    | set(PYQIR_TWO_QUBIT_OP_MAP)
    | set(PYQIR_THREE_QUBIT_OP_MAP)
    | set(PYQIR_MEASUREMENT_OP_MAP)
    | {"barrier"}
    | NOOP_INSTRUCTIONS
)

QISKIT_BASIS_GATES: list[str] = sorted(
    (set(PYQIR_ONE_QUBIT_OP_MAP) - {"reset"})
    | set(PYQIR_ONE_QUBIT_ROTATION_MAP)
    | set(PYQIR_TWO_QUBIT_OP_MAP)
    | set(PYQIR_THREE_QUBIT_OP_MAP)
    | {"measure", "reset"}
)


def map_qiskit_op_to_pyqir_callable(op_name: str) -> tuple[Callable, int]:
    """Map a Qiskit operation to a PyQIR callable and expected qubit count.

    Args:
        op_name: The Qiskit operation name.

    Returns:
        A tuple of (callable, num_qubits).

    Raises:
        QiskitConversionError: If the operation is unsupported.
    """
    op_name_lower = op_name.lower()

    op_mappings: list[tuple[dict, int]] = [
        (PYQIR_ONE_QUBIT_OP_MAP, 1),
        (PYQIR_ONE_QUBIT_ROTATION_MAP, 1),
        (PYQIR_TWO_QUBIT_OP_MAP, 2),
        (PYQIR_THREE_QUBIT_OP_MAP, 3),
    ]

    for mapping, num_qubits in op_mappings:
        if op_name_lower in mapping:
            return mapping[op_name_lower], num_qubits

    raise QiskitConversionError(f"Unsupported Qiskit operation: {op_name}")
