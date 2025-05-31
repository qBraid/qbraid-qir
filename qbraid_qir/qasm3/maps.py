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
Only includes native gates that are directly supported by pyqir.
All other gates will be automatically unrolled by pyqasm.
"""
from typing import Callable

import pyqir

from .exceptions import Qasm3ConversionError


def id_gate(builder, qubits):
    """Identity gate implementation using native gates."""
    pyqir._native.x(builder, qubits)
    pyqir._native.x(builder, qubits)


def map_qasm_op_to_pyqir_callable(op_name: str) -> tuple[Callable, int]:
    """
    Maps QASM operation names to their corresponding PyQIR implementations.
    Only includes native gates and essential custom gates that aren't handled by pyqasm's unroll.

    Args:
        op_name: Name of the QASM operation.

    Returns:
        tuple: (callable, number of qubits required)

    Raises:
        TypeError: If op_name is not a string.
        Qasm3ConversionError: If the operation is not supported.
    """
    if not isinstance(op_name, str):
        raise TypeError(f"Operation name must be a string, got {type(op_name)}")

    # Native single-qubit gates
    if op_name == "id":
        return id_gate, 1
    if op_name == "x":
        return pyqir._native.x, 1
    if op_name == "y":
        return pyqir._native.y, 1
    if op_name == "z":
        return pyqir._native.z, 1
    if op_name == "h":
        return pyqir._native.h, 1
    if op_name == "s":
        return pyqir._native.s, 1
    if op_name == "sdg":
        return pyqir._native.s_adj, 1
    if op_name == "t":
        return pyqir._native.t, 1
    if op_name == "tdg":
        return pyqir._native.t_adj, 1
    
    # Native two-qubit gates
    if op_name == "cx":
        return pyqir._native.cx, 2
    if op_name == "cz":
        return pyqir._native.cz, 2
    if op_name == "swap":
        return pyqir._native.swap, 2

    # Native rotation gates
    if op_name == "rx":
        return pyqir._native.rx, 1
    if op_name == "ry":
        return pyqir._native.ry, 1
    if op_name == "rz":
        return pyqir._native.rz, 1

    raise Qasm3ConversionError(f"Operation {op_name} is not supported")

