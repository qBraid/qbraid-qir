# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module mapping supported Cirq gates/operations to pyqir functions.

"""
from typing import Callable, Tuple

import cirq
import pyqir._native

from .exceptions import CirqConversionError


# NOTE: Upper/lower case matters here, and were set to
# match the Cirq gate/op string representation.
def i(builder, qubits):
    pyqir._native.x(builder, qubits)
    pyqir._native.x(builder, qubits)


def measure_x(builder, qubit, result):
    pyqir._native.h(builder, qubit)
    pyqir._native.mz(builder, qubit, result)


def measure_y(builder, qubit, result):
    pyqir._native.s_adj(builder, qubit)
    pyqir._native.h(builder, qubit)
    pyqir._native.mz(builder, qubit, result)


PYQIR_OP_MAP = {
    # Identity Gate
    "I": i,
    # Single-Qubit Clifford Gates
    "H": pyqir._native.h,
    "X": pyqir._native.x,
    "Y": pyqir._native.y,
    "Z": pyqir._native.z,
    # Single-Qubit Rotation Gates
    "Rx": pyqir._native.rx,
    "Ry": pyqir._native.ry,
    "Rz": pyqir._native.rz,
    # Single-Qubit Non-Clifford Gates
    "S": pyqir._native.s,
    "T": pyqir._native.t,
    "S**-1": pyqir._native.s_adj,
    "T**-1": pyqir._native.t_adj,
    # Two-Qubit Gates
    "SWAP": pyqir._native.swap,
    "CNOT": pyqir._native.cx,
    "CZ": pyqir._native.cz,
    # Three-Qubit Gates
    "TOFFOLI": pyqir._native.ccx,
    # Classical Gates/Operations
    "measure_z": pyqir._native.mz,
    "measure_x": measure_x,
    "measure_y": measure_y,
    "reset": pyqir._native.reset,
}


def map_cirq_op_to_pyqir_callable(
    operation: cirq.Operation,
) -> Tuple[Callable, str]:
    """
    Maps a Cirq operation to its corresponding PyQIR callable function.

    Args:
        operation (cirq.Operation): The Cirq operation to map.

    Returns:
        Tuple[Callable, str]: Tuple containing the corresponding PyQIR callable function,
                               and a string representing the gate/operation type.

    Raises:
        CirqConversionError: If the operation or gate is not supported.
    """
    if isinstance(operation, cirq.ops.GateOperation):
        gate = operation.gate

        if isinstance(gate, cirq.ops.MeasurementGate):
            op_name = "measure_z"

        elif isinstance(gate, cirq.ops.PauliMeasurementGate):
            op_name = str(gate.observable())
            op_name = op_name.removeprefix("+")  # Remove the '+' sign
            op_name = op_name.removeprefix("-")  # Remove the '-' sign
            # TODO: is XYZ same as X tensor Y tensor Z?
            #      if yes, then we can extend this to multi-qubit measurements

            if op_name not in ["X", "Y", "Z"]:
                raise CirqConversionError(
                    f"Multi-qubit gate {op_name} not supported for measurement."
                )

            op_name = f"measure_{op_name.lower()}"

        elif isinstance(gate, (cirq.ops.Rx, cirq.ops.Ry, cirq.ops.Rz)):
            op_name = gate.__class__.__name__
        elif isinstance(gate, cirq.ops.Pauli):
            op_name = gate.__class__.__name__[-1]  # X, Y, Z
        elif isinstance(gate, (cirq.ops.XPowGate, cirq.ops.YPowGate, cirq.ops.ZPowGate)):
            if gate.exponent == 1 or (
                isinstance(gate, cirq.ZPowGate) and gate.exponent in [0.25, -0.25, 0.5, -0.5]
            ):
                op_name = str(gate)  # X, Y, Z, S, T, S**-1, T**-1
            else:
                op_name = f"R{gate.__class__.__name__[0].lower()}"  # Rotations
        else:
            op_name = str(gate)
    else:
        op_name = str(operation)

    try:
        return PYQIR_OP_MAP[op_name], op_name
    except KeyError as err:
        raise CirqConversionError(f"Cirq gate {operation} not supported.") from err
