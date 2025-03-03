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
Module for processing Cirq circuits before conversion to QIR.

"""
import itertools
from typing import Iterable

import cirq

from .exceptions import CirqConversionError
from .opsets import map_cirq_op_to_pyqir_callable


def _decompose_gate_op(operation: cirq.Operation) -> Iterable[cirq.OP_TREE]:
    """Decomposes a single Cirq gate operation into a sequence of operations
    that are directly supported by PyQIR.

    Args:
        operation (cirq.Operation): The gate operation to decompose.

    Returns:
        Iterable[cirq.OP_TREE]: A list of decomposed gate operations.
    """
    try:
        # Try converting to PyQIR. If successful, keep the operation.
        _ = map_cirq_op_to_pyqir_callable(operation)
        return [operation]
    except CirqConversionError:
        pass
    new_ops = cirq.decompose_once(operation, flatten=True, default=[operation])
    if len(new_ops) == 1 and new_ops[0] == operation:
        raise CirqConversionError("Couldn't convert circuit to QIR gate set.")
    return list(itertools.chain.from_iterable(map(_decompose_gate_op, new_ops)))


def _decompose_unsupported_gates(circuit: cirq.Circuit) -> cirq.Circuit:
    """
    Decompose gates in a circuit that are not in the supported set.

    Args:
        circuit (cirq.Circuit): The quantum circuit to process.

    Returns:
        cirq.Circuit: A new circuit with unsupported gates decomposed.
    """
    new_circuit = cirq.Circuit()
    for moment in circuit:
        new_ops = []
        for operation in moment:
            if isinstance(operation, cirq.GateOperation):
                decomposed_ops = list(_decompose_gate_op(operation))
                new_ops.extend(decomposed_ops)
            elif isinstance(operation, cirq.ClassicallyControlledOperation):
                new_ops.append(operation)
            else:
                new_ops.append(operation)

        new_circuit.append(new_ops)
    return new_circuit


def preprocess_circuit(circuit: cirq.Circuit) -> cirq.Circuit:
    """
    Preprocesses a Cirq circuit to ensure that it is compatible with the QIR conversion.

    Args:
        circuit (cirq.Circuit): The Cirq circuit to preprocess.

    Returns:
        cirq.Circuit: The preprocessed Cirq circuit.

    """
    qubit_map = {qubit: cirq.LineQubit(i) for i, qubit in enumerate(circuit.all_qubits())}
    line_qubit_circuit = circuit.transform_qubits(lambda q: qubit_map[q])
    return _decompose_unsupported_gates(line_qubit_circuit)
