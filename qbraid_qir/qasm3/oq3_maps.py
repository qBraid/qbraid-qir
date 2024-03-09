# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module mapping supported QASM gates/operations to pyqir functions.

"""

import pyqir


def id_gate(builder, qubits):
    pyqir._native.x(builder, qubits)
    pyqir._native.x(builder, qubits)


PYQIR_ONE_QUBIT_OP_MAP = {
    # Identity Gate
    "id": id_gate,
    # Single-Qubit Clifford Gates
    "h": pyqir._native.h,
    "x": pyqir._native.x,
    "y": pyqir._native.y,
    "z": pyqir._native.z,
    # Single-Qubit Non-Clifford Gates
    "s": pyqir._native.s,
    "t": pyqir._native.t,
    "sdg": pyqir._native.s_adj,
    "tdg": pyqir._native.t_adj,
}

PYQIR_ONE_QUBIT_ROTATION_MAP = {
    "rx": pyqir._native.rx,
    "ry": pyqir._native.ry,
    "rz": pyqir._native.rz,
}

PYQIR_TWO_QUBIT_OP_MAP = {
    "cx": pyqir._native.cx,
    "CX": pyqir._native.cx,
    "cz": pyqir._native.cz,
    "swap": pyqir._native.swap,
}

PYQIR_THREE_QUBIT_OP_MAP = {
    "ccx": pyqir._native.ccx,
}


def map_qasm_op_to_pyqir_callable(op_name: str):
    try:
        return PYQIR_ONE_QUBIT_OP_MAP[op_name], 1
    except KeyError:
        pass
    try:
        return PYQIR_ONE_QUBIT_ROTATION_MAP[op_name], 1
    except KeyError:
        pass
    try:
        return PYQIR_TWO_QUBIT_OP_MAP[op_name], 2
    except KeyError:
        pass
    try:
        return PYQIR_THREE_QUBIT_OP_MAP[op_name], 3
    except KeyError:
        raise ValueError(f"Unsupported / undeclared QASM operation: {op_name}")
