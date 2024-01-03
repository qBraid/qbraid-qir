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
Module mapping supported Cirq gates/operations to pyqir functions.

"""
import re
from typing import Callable, Tuple

import cirq
import pyqir._native

from qbraid_qir.exceptions import QirConversionError

# NOTE: Upper/lower case matters here, and were set to
# match the Cirq gate/op string representation.

PYQIR_OP_MAP = {
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
    "MEASURE": pyqir._native.mz,
    "reset": pyqir._native.reset,
}


def map_cirq_op_to_pyqir_callable(op: cirq.Operation) -> Tuple[Callable, str]:
    """
    Maps a Cirq operation to its corresponding PyQIR callable function.

    Args:
        op (cirq.Operation): The Cirq operation to map.

    Returns:
        Tuple[Callable, str]: Tuple containing the corresponding PyQIR callable function,
                               and a string representing the gate/operation type.

    Raises:
        QirConversionError: If the operation or gate is not supported.
    """
    if isinstance(op, cirq.ops.GateOperation):
        gate = op.gate

        if isinstance(gate, cirq.ops.MeasurementGate):
            op_name = "MEASURE"
        elif isinstance(gate, (cirq.ops.Rx, cirq.ops.Ry, cirq.ops.Rz)):
            op_name = re.search(r"([Rx-z]+)\(", str(gate)).group(1)
        else:
            op_name = str(gate)
    else:
        op_name = str(op)

    try:
        return PYQIR_OP_MAP[op_name], op_name
    except KeyError as err:
        raise QirConversionError(f"Cirq gate {op} not supported.") from err
