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

from typing import Union

import pyqir
from openqasm3.ast import (
    AngleType,
    ArrayType,
    BitType,
    BoolType,
    ComplexType,
    FloatType,
    IntType,
    UintType,
)

from .elements import InversionOp
from .exceptions import Qasm3ConversionError

OPERATOR_MAP = {
    "+": lambda x, y: x + y,
    "-": lambda x, y: x - y,
    "*": lambda x, y: x * y,
    "/": lambda x, y: x / y,
    "%": lambda x, y: x % y,
    "==": lambda x, y: x == y,
    "!=": lambda x, y: x != y,
    "<": lambda x, y: x < y,
    ">": lambda x, y: x > y,
    "<=": lambda x, y: x <= y,
    ">=": lambda x, y: x >= y,
    "&&": lambda x, y: x and y,
    "||": lambda x, y: x or y,
    "^": lambda x, y: x ^ y,
    "&": lambda x, y: x & y,
    "|": lambda x, y: x | y,
    "<<": lambda x, y: x << y,
    ">>": lambda x, y: x >> y,
    "~": lambda x: ~x,
    "!": lambda x: not x,
    "UMINUS": lambda x: -x,
}


def qasm3_expression_op_map(op_name: str, *args):
    """
    Return the result of applying the given operator to the given operands.

    Args:
        op_name (str): The operator name.
        *args: The operands of type Union[int, float, bool]
                1. For unary operators, a single operand (e.g., ~3)
                2. For binary operators, two operands (e.g., 3 + 2)

    Returns:
        (Union[float, int, bool]): The result of applying the operator to the operands.
    """
    try:
        return OPERATOR_MAP[op_name](*args)
    except KeyError as exc:
        raise Qasm3ConversionError(f"Unsupported / undeclared QASM operator: {op_name}") from exc


def id_gate(builder, qubits):
    pyqir._native.x(builder, qubits)
    pyqir._native.x(builder, qubits)


def u3_gate(
    builder, theta: Union[int, float], phi: Union[int, float], lam: Union[int, float], qubits
):
    """
    Implements the U3 gate using the following decomposition:
         https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.UGate
         https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.PhaseGate

    Args:
        builder (pyqir._native.QirBuilder): The QIR builder.
        theta (Union[int, float]): The theta angle.
        phi (Union[int, float]): The phi angle.
        lam (Union[int, float]): The lambda angle.
        qubits: The qubits on which the gate is applied.

    Returns:
        None
    """
    pyqir._native.rz(builder, lam, qubits)
    pyqir._native.rx(builder, CONSTANTS_MAP["pi"] / 2, qubits)
    pyqir._native.rz(builder, theta + CONSTANTS_MAP["pi"], qubits)
    pyqir._native.rx(builder, CONSTANTS_MAP["pi"] / 2, qubits)
    pyqir._native.rz(builder, phi + CONSTANTS_MAP["pi"], qubits)
    # global phase - e^(i*(phi+lambda)/2) is missing in the above implementation


def u3_inv_gate(
    builder, theta: Union[int, float], phi: Union[int, float], lam: Union[int, float], qubits
):
    """
    Implements the inverse of the U3 gate using the decomposition present in
    the u3_gate function.
    """
    pyqir._native.rz(builder, -1.0 * (phi + CONSTANTS_MAP["pi"]), qubits)
    pyqir._native.rx(builder, -1.0 * (CONSTANTS_MAP["pi"] / 2), qubits)
    pyqir._native.rz(builder, -1.0 * (theta + CONSTANTS_MAP["pi"]), qubits)
    pyqir._native.rx(builder, -1.0 * (CONSTANTS_MAP["pi"] / 2), qubits)
    pyqir._native.rz(builder, -1.0 * lam, qubits)


def u2_gate(builder, phi, lam, qubits):
    """
    Implements the U2 gate using the following decomposition:
        https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.U2Gate
    """
    u3_gate(builder, CONSTANTS_MAP["pi"] / 2, phi, lam, qubits)


def u2_inv_gate(builder, phi, lam, qubits):
    """
    Implements the inverse of the U2 gate using the decomposition present in
    the u2_gate function.
    """
    u3_inv_gate(builder, CONSTANTS_MAP["pi"] / 2, phi, lam, qubits)


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
    "U": u3_gate,
    "u3": u3_gate,
    "U3": u3_gate,
    "U2": u2_gate,
    "u2": u2_gate,
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
    """
    Map a QASM operation to a PyQIR callable.

    Args:
        op_name (str): The QASM operation name.

    Returns:
        tuple: A tuple containing the PyQIR callable and the number of qubits the operation acts on.
    """
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
    except KeyError as exc:
        raise Qasm3ConversionError(f"Unsupported / undeclared QASM operation: {op_name}") from exc


PYQIR_SELF_INVERTING_ONE_QUBIT_OP_SET = {"id", "h", "x", "y", "z"}
PYQIR_ST_GATE_INV_MAP = {
    "s": "sdg",
    "t": "tdg",
    "sdg": "s",
    "tdg": "t",
}
PYQIR_ROTATION_INVERSION_ONE_QUBIT_OP_MAP = {"rx", "ry", "rz"}
PYQIR_U_INV_ROTATION_MAP = {
    "U": u3_inv_gate,
    "u3": u3_inv_gate,
    "U3": u3_inv_gate,
    "U2": u2_inv_gate,
    "u2": u2_inv_gate,
}


def map_qasm_inv_op_to_pyqir_callable(op_name: str):
    """
    Map a QASM operation to a PyQIR callable.

    Args:
        op_name (str): The QASM operation name.

    Returns:
        tuple: A tuple containing the PyQIR callable, the number of qubits the operation acts on,
        and what is to be done with the basic gate which we are trying to invert.
    """
    if op_name in PYQIR_SELF_INVERTING_ONE_QUBIT_OP_SET:
        return PYQIR_ONE_QUBIT_OP_MAP[op_name], 1, InversionOp.NO_OP
    if op_name in PYQIR_ST_GATE_INV_MAP:
        inv_gate_name = PYQIR_ST_GATE_INV_MAP[op_name]
        return PYQIR_ONE_QUBIT_OP_MAP[inv_gate_name], 1, InversionOp.NO_OP
    if op_name in PYQIR_TWO_QUBIT_OP_MAP:
        return PYQIR_TWO_QUBIT_OP_MAP[op_name], 2, InversionOp.NO_OP
    if op_name in PYQIR_THREE_QUBIT_OP_MAP:
        return PYQIR_THREE_QUBIT_OP_MAP[op_name], 3, InversionOp.NO_OP
    if op_name in PYQIR_U_INV_ROTATION_MAP:
        # Special handling for U gate as it is composed of multiple
        # basic gates and we need to invert each of them
        return PYQIR_U_INV_ROTATION_MAP[op_name], 1, InversionOp.NO_OP
    if op_name in PYQIR_ROTATION_INVERSION_ONE_QUBIT_OP_MAP:
        return PYQIR_ONE_QUBIT_ROTATION_MAP[op_name], 1, InversionOp.INVERT_ROTATION
    raise Qasm3ConversionError(f"Unsupported / undeclared QASM operation: {op_name}")


CONSTANTS_MAP = {
    "pi": 3.141592653589793,
    "π": 3.141592653589793,
    "e": 2.718281828459045,
    "tau": 6.283185307179586,
}

VARIABLE_TYPE_MAP = {
    BitType: bool,
    IntType: int,
    UintType: int,
    BoolType: bool,
    FloatType: float,
    ArrayType: None,  # not sure
    AngleType: None,  # not sure
    ComplexType: complex,
}
