# Copyright 2025 qBraid
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
Module mapping supported QASM gates/operations to pyqir functions.
"""
from typing import Callable

import pyqir
import pyqir._native

from .exceptions import Qasm3ConversionError


def i(_builder, qubit):
    """Identity gate - does nothing"""
    # Identity gate is a no-op
    return qubit


def sx(builder, qubit):
    """Sqrt(X) gate implementation using H and S gates"""
    pyqir._native.h(builder, qubit)
    pyqir._native.s(builder, qubit)
    pyqir._native.h(builder, qubit)
    return qubit


def sxdg(builder, qubit):
    """Inverse of Sqrt(X) gate implementation"""
    pyqir._native.h(builder, qubit)
    pyqir._native.s_adj(builder, qubit)
    pyqir._native.h(builder, qubit)
    return qubit


# Only keep the native PyQIR operations in the mapping dictionaries
PYQIR_ONE_QUBIT_OP_MAP = {
    "h": pyqir._native.h,
    "x": pyqir._native.x,
    "y": pyqir._native.y,
    "z": pyqir._native.z,
    "s": pyqir._native.s,
    "t": pyqir._native.t,
    "sdg": pyqir._native.s_adj,
    "si": pyqir._native.s_adj,
    "tdg": pyqir._native.t_adj,
    "ti": pyqir._native.t_adj,
    "id": i,
    "sx": sx,
    "sxdg": sxdg,
}

PYQIR_ONE_QUBIT_ROTATION_MAP = {
    "rx": pyqir._native.rx,
    "ry": pyqir._native.ry,
    "rz": pyqir._native.rz,
}

PYQIR_TWO_QUBIT_OP_MAP = {
    "cx": pyqir._native.cx,
    "CX": pyqir._native.cx,
    "cnot": pyqir._native.cx,
    "cz": pyqir._native.cz,
    "swap": pyqir._native.swap,
}

PYQIR_THREE_QUBIT_OP_MAP = {
    "ccx": pyqir._native.ccx,
    "ccnot": pyqir._native.ccx,
}

CONSTANTS_MAP = {"pi": 3.141592653589793}


def map_qasm_op_to_pyqir_callable(op_name: str) -> tuple[Callable, int]:
    """
    Map a QASM operation to a PyQIR callable.

    Args:
        op_name (str): The QASM operation name.

    Returns:
        tuple: A tuple containing the PyQIR callable and the number of qubits the operation acts on.

    Raises:
        Qasm3ConversionError: If the QASM operation is unsupported or undeclared.
    """
    qasm_op_mappings: list[tuple[dict, int]] = [
        (PYQIR_ONE_QUBIT_OP_MAP, 1),
        (PYQIR_ONE_QUBIT_ROTATION_MAP, 1),
        (PYQIR_TWO_QUBIT_OP_MAP, 2),
        (PYQIR_THREE_QUBIT_OP_MAP, 3),
    ]

    for mapping, qubits in qasm_op_mappings:
        if op_name.lower() in mapping:
            return mapping[op_name.lower()], qubits

    raise Qasm3ConversionError(f"Unsupported / undeclared QASM operation: {op_name}")
