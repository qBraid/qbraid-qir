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

from qbraid_qir.cirq.exceptions import CirqConversionError
from qbraid_qir.cirq.passes import preprocess_circuit

# pylint: disable=redefined-outer-name


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
    assert np.allclose(
        linequbit_circuit.unitary(), gridqubit_circuit.unitary()
    ), "Circuits are not equal"


def test_convert_namedqubits_to_linequbits(namedqubit_circuit):
    linequbit_circuit = preprocess_circuit(namedqubit_circuit)
    for qubit in linequbit_circuit.all_qubits():
        assert isinstance(qubit, cirq.LineQubit), "Qubit is not a LineQubit"
    assert np.allclose(
        linequbit_circuit.unitary(), namedqubit_circuit.unitary()
    ), "Circuits are not equal"


def test_empty_circuit_conversion():
    circuit = cirq.Circuit()
    converted_circuit = preprocess_circuit(circuit)
    assert len(converted_circuit.all_qubits()) == 0, "Converted empty circuit should have no qubits"


def test_multi_qubit_measurement_error():
    qubits = cirq.LineQubit.range(3)
    circuit = cirq.Circuit()
    ps = cirq.X(qubits[0]) * cirq.Y(qubits[1]) * cirq.X(qubits[2])
    meas_gates = cirq.measure_single_paulistring(ps)
    circuit.append(meas_gates)
    with pytest.raises(CirqConversionError):
        preprocess_circuit(circuit)
