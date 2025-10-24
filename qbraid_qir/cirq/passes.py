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

from typing import Sequence, Union, Type, List

import cirq
from cirq.protocols.decompose_protocol import DecomposeResult
from .exceptions import CirqConversionError

class QirTargetGateSet(cirq.TwoQubitCompilationTargetGateset):
    def __init__(
        self,
        *,
        atol: float = 1e-8,
        allow_partial_czs: bool = False,
        additional_gates: Sequence[
            Union[Type["cirq.Gate"], "cirq.Gate", "cirq.GateFamily"]
        ] = (),
        preserve_moment_structure: bool = True,
    ) -> None:
        super().__init__(
            cirq.IdentityGate,
            cirq.HPowGate,
            cirq.XPowGate,
            cirq.YPowGate,
            cirq.ZPowGate,
            cirq.SWAP,
            cirq.CNOT,
            cirq.CZ,
            cirq.TOFFOLI,
            cirq.ResetChannel,
            cirq.MeasurementGate,
            cirq.PauliMeasurementGate,
            *additional_gates,
            name="QirTargetGateset",
            preserve_moment_structure=preserve_moment_structure,
        )
        self.allow_partial_czs = allow_partial_czs
        self.atol = atol

    @property
    def postprocess_transformers(self) -> List["cirq.TRANSFORMER"]:
        return []

    def _decompose_single_qubit_operation(
        self, op: "cirq.Operation", moment_idx: int
    ) -> DecomposeResult:
        qubit = op.qubits[0]
        mat = cirq.unitary(op)
        for gate in cirq.single_qubit_matrix_to_gates(mat, self.atol):
            yield gate(qubit)

    def _decompose_two_qubit_operation(self, op: "cirq.Operation", _) -> "cirq.OP_TREE":
        if not cirq.has_unitary(op):
            return NotImplemented
        return cirq.two_qubit_matrix_to_cz_operations(
            op.qubits[0],
            op.qubits[1],
            cirq.unitary(op),
            allow_partial_czs=self.allow_partial_czs,
            atol=self.atol,
        )

def preprocess_circuit(circuit: cirq.Circuit) -> cirq.Circuit:
    """
    Preprocesses a Cirq circuit to ensure that it is compatible with the QIR conversion.

    Args:
        circuit (cirq.Circuit): The Cirq circuit to preprocess.

    Returns:
        cirq.Circuit: The preprocessed Cirq circuit.

    """
    gateset = QirTargetGateSet()
    qubit_map = {qubit: cirq.LineQubit(i) for i, qubit in enumerate(circuit.all_qubits())}
    line_qubit_circuit = circuit.transform_qubits(lambda q: qubit_map[q])
    try: 
        qir_circuit = cirq.optimize_for_target_gateset(line_qubit_circuit, gateset=gateset)
        return qir_circuit
    except CirqConversionError: 
        raise CirqConversionError("Couldn't convert circuit to QIR gate set.")

