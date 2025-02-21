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
Module containing Cirq to qBraid QIR conversion functions

"""
from typing import Optional

import cirq
from pyqir import Context, Module, qir_module

from .elements import CirqModule, generate_module_id
from .exceptions import CirqConversionError
from .passes import preprocess_circuit
from .visitor import BasicCirqVisitor


def cirq_to_qir(circuit: cirq.Circuit, name: Optional[str] = None, **kwargs) -> Module:
    """
    Converts a Cirq circuit to a PyQIR module.

    Args:
        circuit (cirq.Circuit): The Cirq circuit to convert.
        name (str, optional): Identifier for created QIR module. Auto-generated if not provided.

    Keyword Args:
        initialize_runtime (bool): Whether to perform quantum runtime environment initialization,
                                   default `True`.
        record_output (bool): Whether to record output calls for registers, default `True`

    Returns:
        The QIR ``pyqir.Module`` representation of the input Cirq circuit.

    Raises:
        TypeError: If the input is not a valid Cirq circuit.
        ValueError: If the input circuit is empty.
        CirqConversionError: If the conversion fails.
    """
    if not isinstance(circuit, cirq.Circuit):
        raise TypeError("Input quantum program must be of type cirq.Circuit.")

    if len(circuit) == 0:
        raise ValueError("Input quantum circuit must consist of at least one operation.")

    if name is None:
        name = generate_module_id(circuit)

    try:
        circuit = preprocess_circuit(circuit)
    except Exception as err:  # pylint: disable=broad-exception-caught
        raise CirqConversionError("Failed to preprocess circuit.") from err

    llvm_module = qir_module(Context(), name)
    module = CirqModule.from_circuit(circuit, llvm_module)

    visitor = BasicCirqVisitor(**kwargs)
    module.accept(visitor)

    error = llvm_module.verify()
    if error is not None:
        raise CirqConversionError(error)
    return llvm_module
