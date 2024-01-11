# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for processing Cirq circuits before conversion to QIR.

"""
import itertools
from typing import List

import cirq

from qbraid_qir.cirq.opsets import map_cirq_op_to_pyqir_callable
from qbraid_qir.exceptions import QirConversionError


def _decompose_gate_op(op: cirq.GateOperation) -> List[cirq.OP_TREE]:
    try:
        # Try converting to PyQIR. If successful, keep the operation.
        _ = map_cirq_op_to_pyqir_callable(op)
        return [op]
    except QirConversionError:
        pass
    new_ops = cirq.decompose_once(op, flatten=True, default=[op])
    if len(new_ops) == 1 and new_ops[0] == op:
        return [op]
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
        for op in moment:
            if isinstance(op, cirq.GateOperation):
                decomposed_ops = _decompose_gate_op(op)
                new_ops.extend(decomposed_ops)
            else:
                new_ops.append(op)

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
    qubit_map = {
        qubit: cirq.LineQubit(i) for i, qubit in enumerate(circuit.all_qubits())
    }
    line_qubit_circuit = circuit.transform_qubits(lambda q: qubit_map[q])
    return _decompose_unsupported_gates(line_qubit_circuit)
