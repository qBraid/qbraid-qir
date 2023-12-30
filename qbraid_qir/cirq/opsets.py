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
from typing import Callable

import cirq
import pyqir._native

ZPOWER_DICT = {
    1: pyqir._native.z,
    0.5: pyqir._native.s,
    0.25: pyqir._native.t,
    -0.5: pyqir._native.s_adj,
    -0.25: pyqir._native.t_adj,
}
CIRQ_GATES = {
    "TOFFOLI": pyqir._native.ccx,
    "CCX": pyqir._native.ccx,
    "CCNOT": pyqir._native.ccx,
    "CNOT": pyqir._native.cx,
    "CZ": pyqir._native.cz,
    "H": pyqir._native.h,
    "SWAP": pyqir._native.swap,
    "X": pyqir._native.x,
    "Y": pyqir._native.y,
    "T": pyqir._native.t,
    "Z": pyqir._native.z,
    "S": pyqir._native.s,
}


def map_cirq_op_to_pyqir_callable(op: cirq.Operation) -> Callable:
    """Maps a Cirq operation to its corresponding PyQIR callable function."""
    if isinstance(op, cirq.ops.ZPowGate):
        return ZPOWER_DICT[op.gate.exponent]
    return CIRQ_GATES[str(op.gate)]
