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
Test functions that preprocess Cirq circuits before conversion to QIR.

"""
import cirq
import numpy as np
import pytest
import qbraid

from qbraid_qir.cirq.exceptions import CirqConversionError
from qbraid_qir.cirq.passes import preprocess_circuit

@pytest.fixture
def gridqubit_circuit():
    qubits = [cirq.GridQubit(x, 0) for x in range(4)]
    circuit = cirq.Circuit(cirq.H(q) for q in qubits)
    yield circuit


@pytest.fixture
def namedqubit_circuit():
    qubits = [cirq.NamedQubit(f"q{i}") for i in range(4)]
    circuit = cirq.Circuit(cirq.H(q) for q in qubits)
    yield circuit


def test_convert_gridqubits_to_linequbits(gridqubit_circuit):
    linequbit_circuit = preprocess_circuit(gridqubit_circuit)
    for qubit in linequbit_circuit.all_qubits():
        assert isinstance(qubit, cirq.LineQubit), "Qubit is not a LineQubit"
    qbraid.interface.assert_allclose_up_to_global_phase(
        linequbit_circuit.unitary(), gridqubit_circuit.unitary(), atol=1e-6
    ), "Circuits are not equal"


def test_convert_namedqubits_to_linequbits(namedqubit_circuit):
    linequbit_circuit = preprocess_circuit(namedqubit_circuit)
    for qubit in linequbit_circuit.all_qubits():
        assert isinstance(qubit, cirq.LineQubit), "Qubit is not a LineQubit"
    qbraid.interface.assert_allclose_up_to_global_phase(
        linequbit_circuit.unitary(), namedqubit_circuit.unitary(), atol=1e-6
    ), "Circuits are not equal"


def test_empty_circuit_conversion():
    circuit = cirq.Circuit()
    converted_circuit = preprocess_circuit(circuit)
    assert len(converted_circuit.all_qubits()) == 0, "Converted empty circuit should have no qubits"

