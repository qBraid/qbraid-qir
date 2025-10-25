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
Module that contains QIRTargetGateSet class.

"""

from typing import List, Sequence, Type, Union

import cirq
import numpy as np
from cirq import Moment, protocols, transformers
from cirq.protocols.decompose_protocol import DecomposeResult
from cirq.transformers import create_transformer_with_kwargs, merge_k_qubit_gates


def _add_rads_attribute(
    circuit: cirq.Circuit, *, context: cirq.TransformerContext = cirq.TransformerContext()
) -> cirq.Circuit:
    """
    Transformer that attaches a `_rads` attribute to all XPowGate, YPowGate, and ZPowGate
    instances in the circuit.

    This is required because downstream components (e.g., the QIR visitor) expect each
    single-qubit rotation gate to expose a `_rads` attribute representing its rotation
    angle in radians. Newer versions of Cirq removed this private field, so this
    transformer ensures backward compatibility by computing `_rads` as:

        _rads = gate.exponent * π

    Returns:
        cirq.Circuit: A new circuit with `_rads` attributes added to all relevant gates.
    """

    new_moments = []
    for moment in circuit:
        new_ops = []
        for op in moment.operations:
            gate = op.gate
            # The visitor later expects rotation gates to have a `_rads` field (radians).
            # Cirq's newer API no longer includes it, so we compute and attach it here.
            if isinstance(gate, (cirq.XPowGate, cirq.YPowGate, cirq.ZPowGate)):
                # Compute radians from exponent
                try:
                    gate._rads = float(gate.exponent * np.pi)
                except AttributeError:
                    # Older Cirq may already have _rads, ignore
                    pass
            new_ops.append(op)
        new_moments.append(Moment(new_ops))
    return cirq.Circuit(new_moments)


class QirTargetGateSet(cirq.TwoQubitCompilationTargetGateset):
    def __init__(
        self,
        *,
        atol: float = 1e-8,
        allow_partial_czs: bool = False,
        additional_gates: Sequence[Union[Type["cirq.Gate"], "cirq.Gate", "cirq.GateFamily"]] = (),
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
    def preprocess_transformers(self) -> List["cirq.TRANSFORMER"]:
        """Override to handle TOFFOLI gate."""

        return [
            create_transformer_with_kwargs(
                transformers.expand_composite,
                # Don't decompose operations that are in our gateset OR have <= 2 qubits
                no_decomp=lambda op: protocols.num_qubits(op) <= 2 or op in self,
            ),
            create_transformer_with_kwargs(
                merge_k_qubit_gates.merge_k_qubit_unitaries,
                k=2,
                rewriter=lambda op: op.with_tags(self._intermediate_result_tag),
            ),
        ]

    @property
    def postprocess_transformers(self) -> List["cirq.TRANSFORMER"]:
        return [_add_rads_attribute]

    def _decompose_single_qubit_operation(
        self, op: "cirq.Operation", moment_idx: int
    ) -> DecomposeResult:
        # Unwrap TaggedOperation and CircuitOperation to get the actual gate
        actual_op = op

        if isinstance(actual_op, cirq.TaggedOperation):
            actual_op = actual_op.sub_operation

        if isinstance(actual_op, cirq.CircuitOperation):
            ops = list(actual_op.circuit.all_operations())
            if len(ops) == 1:
                actual_op = ops[0]

        gate = actual_op.gate if hasattr(actual_op, "gate") else actual_op

        # Check if gate is already in our target gateset
        # For Pow gates, any exponent is fine (they're all supported)
        if isinstance(gate, (cirq.HPowGate, cirq.XPowGate, cirq.YPowGate, cirq.ZPowGate)):
            yield actual_op
            return

        # Other supported single-qubit gates
        if isinstance(
            gate,
            (cirq.IdentityGate, cirq.ResetChannel, cirq.MeasurementGate, cirq.PauliMeasurementGate),
        ):
            yield actual_op
            return

        # Decompose everything else
        qubit = op.qubits[0]
        mat = cirq.unitary(op)
        for gate_result in cirq.single_qubit_matrix_to_gates(mat, self.atol):
            yield gate_result(qubit)

    def _decompose_two_qubit_operation(self, op: "cirq.Operation", _) -> "cirq.OP_TREE":
        # Unwrap TaggedOperation and CircuitOperation to get the actual gate
        actual_op = op

        if isinstance(actual_op, cirq.TaggedOperation):
            actual_op = actual_op.sub_operation

        if isinstance(actual_op, cirq.CircuitOperation):
            ops = list(actual_op.circuit.all_operations())
            if len(ops) == 1:
                actual_op = ops[0]

        gate = actual_op.gate if hasattr(actual_op, "gate") else actual_op

        # Check if gate is already in our target gateset
        # CNOT, CZ, SWAP are in the target set
        # (they're CNotPowGate, CZPowGate, SwapPowGate with exponent=1)
        if isinstance(gate, (cirq.CNotPowGate, cirq.CZPowGate, cirq.SwapPowGate)):
            yield actual_op
            return

        # Decompose unsupported gates
        if not cirq.has_unitary(op):
            return NotImplemented

        yield cirq.two_qubit_matrix_to_cz_operations(
            op.qubits[0],
            op.qubits[1],
            cirq.unitary(op),
            allow_partial_czs=self.allow_partial_czs,
            atol=self.atol,
        )

    def _decompose_multi_qubit_operation(
        self, op: cirq.Operation, moment_idx: int
    ) -> DecomposeResult:
        """Decomposes operations acting on more than 2 qubits using gates from this gateset."""

        # Check if operation is already valid (in our gateset)
        if self.validate(op):
            # Don't decompose - return the operation as-is
            yield op
            return

        # If not valid, try to unwrap and check the actual gate
        actual_op = op

        if isinstance(actual_op, cirq.TaggedOperation):
            actual_op = actual_op.sub_operation

        if isinstance(actual_op, cirq.CircuitOperation):
            ops_list = list(actual_op.circuit.all_operations())
            if len(ops_list) == 1:
                actual_op = ops_list[0]

        gate = actual_op.gate if hasattr(actual_op, "gate") else actual_op

        # Check if the unwrapped gate is TOFFOLI
        if isinstance(gate, cirq.CCXPowGate):
            yield actual_op
            return

        # Unknown multi-qubit operation - can't decompose
        return NotImplemented
