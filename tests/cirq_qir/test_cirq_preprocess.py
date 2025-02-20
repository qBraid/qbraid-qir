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
