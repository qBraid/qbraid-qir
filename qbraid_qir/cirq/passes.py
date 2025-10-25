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

import cirq
from .exceptions import CirqConversionError
from .QIRTargetGateSet import QirTargetGateSet


def preprocess_circuit(circuit: cirq.Circuit) -> cirq.Circuit:
    """ Preprocesses a Cirq circuit to ensure that it is compatible with the QIR conversion. """
    
    gateset = QirTargetGateSet()
    qubit_map = {qubit: cirq.LineQubit(i) for i, qubit in enumerate(circuit.all_qubits())}
    line_qubit_circuit = circuit.transform_qubits(lambda q: qubit_map[q])
    
    # Check if circuit has ClassicallyControlledOperations
    has_conditional = any(
        isinstance(op, cirq.ClassicallyControlledOperation) 
        for op in line_qubit_circuit.all_operations()
    )
    
    if has_conditional:
        # For circuits with conditional operations, skip the full optimization
        # and just apply the postprocessors
        processed = line_qubit_circuit
        for transformer in gateset.postprocess_transformers:
            processed = transformer(processed)
        return processed
    
    try:
        qir_circuit = cirq.optimize_for_target_gateset(line_qubit_circuit, gateset=gateset)
        return qir_circuit
    except Exception as e:
        raise CirqConversionError("Failed to preprocess circuit.")


