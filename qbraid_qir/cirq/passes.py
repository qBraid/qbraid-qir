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
from typing import Iterable, List, Sequence, Type, Union

import cirq
from cirq.protocols.decompose_protocol import DecomposeResult

from .exceptions import CirqConversionError
from .opsets import map_cirq_op_to_pyqir_callable


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
    circuit = cirq.optimize_for_target_gateset(circuit, gateset=QirTargetGateSet(), ignore_failures=True, max_num_passes=1)

    return circuit

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
