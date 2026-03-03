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

# pylint: disable=line-too-long
# Portions of this module are adapted from microsoft/qiskit-qir
# (https://github.com/microsoft/qiskit-qir), with modifications by qBraid.
# The original MIT license notice is reproduced in NOTICE.md.
# pylint: enable=line-too-long

"""
Module containing Qiskit to QIR conversion functions.

"""

from typing import Optional

from pyqir import Context, Module, qir_module
from qiskit.circuit import QuantumCircuit

from .elements import QiskitModule, generate_module_id
from .exceptions import QiskitConversionError
from .visitor import BasicQiskitVisitor


def qiskit_to_qir(circuit: QuantumCircuit, name: Optional[str] = None, **kwargs) -> Module:
    """
    Converts a Qiskit QuantumCircuit to a PyQIR module.

    Args:
        circuit: The Qiskit QuantumCircuit to convert.
        name: Identifier for created QIR module. Auto-generated if not provided.

    Keyword Args:
        initialize_runtime (bool): Whether to perform quantum runtime environment initialization,
                                   default `True`.
        record_output (bool): Whether to record output calls for registers, default `True`.
        emit_barrier_calls (bool): Whether to emit barrier calls in the QIR, default `False`.

    Returns:
        The QIR ``pyqir.Module`` representation of the input Qiskit circuit.

    Raises:
        TypeError: If the input is not a valid Qiskit QuantumCircuit.
        ValueError: If the input circuit is empty.
        QiskitConversionError: If the conversion fails.

    Example:
        >>> from qiskit import QuantumCircuit
        >>> from qbraid_qir.qiskit import qiskit_to_qir
        >>>
        >>> qc = QuantumCircuit(2, 2)
        >>> qc.h(0)
        >>> qc.cx(0, 1)
        >>> qc.measure([0, 1], [0, 1])
        >>>
        >>> module = qiskit_to_qir(qc, name="bell")
        >>> ir = str(module)
    """
    if not isinstance(circuit, QuantumCircuit):
        raise TypeError("Input quantum program must be of type qiskit.QuantumCircuit.")

    if len(circuit.data) == 0:
        raise ValueError("Input quantum circuit must consist of at least one operation.")

    if name is None:
        name = generate_module_id(circuit)

    llvm_module = qir_module(Context(), name)
    module = QiskitModule.from_circuit(circuit, llvm_module)

    visitor = BasicQiskitVisitor(**kwargs)
    module.accept(visitor)

    error = llvm_module.verify()
    if error is not None:
        raise QiskitConversionError(error)

    return llvm_module
