# Copyright (C) 2024 qBraid
#
# This file is part of qbraid-qir
#
# Qbraid-qir is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for qbraid-qir, as per Section 15 of the GPL v3.

"""
Module for processing Cirq circuits before conversion to QIR.

"""
import itertools
from typing import Iterable, Any, Dict, Sequence, Type, Union, TYPE_CHECKING


import cirq
from cirq.transformers.analytical_decompositions import two_qubit_to_cz


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


# PYQIR_OP_MAP: dict[str, Callable] = {
#     # Identity Gate
#     "I": i,
#     "S**-1": pyqir._native.s_adj,
#     "T**-1": pyqir._native.t_adj,
#     # Two-Qubit Gates
#     "SWAP": pyqir._native.swap,
#     "CNOT": pyqir._native.cx,
#     "CZ": pyqir._native.cz,
#     # Three-Qubit Gates
#     "TOFFOLI": pyqir._native.ccx,
#     # Classical Gates/Operations
#     "measure_z": pyqir._native.mz,
#     "measure_x": measure_x,
#     "measure_y": measure_y,
#     "reset": pyqir._native.reset,
# }

class QIRGateset(cirq.TwoQubitCompilationTargetGateset):
    def __init__(
        self,
        *,
        atol: float = 1e-8,
        allow_partial_czs: bool = False,
        preserve_moment_structure: bool = True,
    ) -> None:
        super().__init__(
            cirq.ops.MeasurementGate,
            cirq.ops.H,
            cirq.ops.X, cirq.ops.Rx,
            cirq.ops.Y, cirq.ops.Ry,
            cirq.ops.Z, cirq.ops.Rz,
            cirq.ops.S, cirq.ops.T,
            cirq.ops.SWAP, cirq.ops.CNOT, cirq.ops.CZ,
            name='QIRGateset',
            preserve_moment_structure=preserve_moment_structure,
        )
        
        self.atol = atol
        self.allow_partial_czs = allow_partial_czs

    def _decompose_two_qubit_operation(self, op: 'cirq.Operation', _) -> 'cirq.OP_TREE':
        if not cirq.protocols.has_unitary(op):
            return NotImplemented
        return two_qubit_to_cz.two_qubit_matrix_to_cz_operations(
            op.qubits[0],
            op.qubits[1],
            cirq.protocols.unitary(op),
            allow_partial_czs=self.allow_partial_czs,
            atol=self.atol,
        )

    def _value_equality_values_(self) -> Any:
        return self.atol, self.allow_partial_czs, frozenset(self.additional_gates)

    def _json_dict_(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {'atol': self.atol, 'allow_partial_czs': self.allow_partial_czs}
        if self.additional_gates:
            d['additional_gates'] = list(self.additional_gates)
        return d

    @classmethod
    def _from_json_dict_(cls, atol, allow_partial_czs, additional_gates=(), **kwargs):
        return cls(
            atol=atol, allow_partial_czs=allow_partial_czs, additional_gates=additional_gates
        )
    

def _decompose_unsupported_gates(circuit: cirq.Circuit) -> cirq.Circuit:
    """
    Decompose gates in a circuit that are not in the supported set.

    Args:
        circuit (cirq.Circuit): The quantum circuit to process.

    Returns:
        cirq.Circuit: A new circuit with unsupported gates decomposed.
    """
    return cirq.optimize_for_target_gateset(circuit, gateset=cirq.CZTargetGateset)
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
