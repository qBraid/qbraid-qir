# Copyright 2026 qBraid
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
Pytest fixtures for Qiskit QIR tests.

"""

import pytest
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister


@pytest.fixture()
def bell_circuit():
    """A simple Bell state circuit."""
    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])
    return circuit


@pytest.fixture()
def ghz_circuit():
    """A 3-qubit GHZ state circuit."""
    circuit = QuantumCircuit(3, 3)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.measure([0, 1, 2], [0, 1, 2])
    return circuit


@pytest.fixture()
def single_qubit_gates_circuit():
    """Circuit with various single-qubit gates."""
    circuit = QuantumCircuit(1)
    circuit.h(0)
    circuit.x(0)
    circuit.y(0)
    circuit.z(0)
    circuit.s(0)
    circuit.sdg(0)
    circuit.t(0)
    circuit.tdg(0)
    return circuit


@pytest.fixture()
def rotation_gates_circuit():
    """Circuit with rotation gates."""
    circuit = QuantumCircuit(1)
    circuit.rx(0.5, 0)
    circuit.ry(1.0, 0)
    circuit.rz(1.5, 0)
    return circuit


@pytest.fixture()
def two_qubit_gates_circuit():
    """Circuit with two-qubit gates."""
    circuit = QuantumCircuit(2)
    circuit.cx(0, 1)
    circuit.cz(0, 1)
    circuit.swap(0, 1)
    return circuit


@pytest.fixture()
def three_qubit_gates_circuit():
    """Circuit with three-qubit gates."""
    circuit = QuantumCircuit(3)
    circuit.ccx(0, 1, 2)
    return circuit


@pytest.fixture()
def reset_circuit():
    """Circuit with reset gate."""
    circuit = QuantumCircuit(1)
    circuit.reset(0)
    circuit.h(0)
    return circuit


@pytest.fixture()
def identity_circuit():
    """Circuit with identity gate."""
    circuit = QuantumCircuit(1)
    circuit.id(0)
    return circuit


@pytest.fixture()
def barrier_circuit():
    """Circuit with barrier."""
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.barrier()
    circuit.cx(0, 1)
    return circuit


@pytest.fixture()
def delay_circuit():
    """Circuit with delay instruction."""
    circuit = QuantumCircuit(1)
    circuit.h(0)
    circuit.delay(100, 0, "ns")
    circuit.x(0)
    return circuit


@pytest.fixture()
def named_registers_circuit():
    """Circuit with named quantum and classical registers."""
    qr = QuantumRegister(2, name="qreg")
    cr = ClassicalRegister(2, name="creg")
    circuit = QuantumCircuit(qr, cr, name="named_circuit")
    circuit.h(qr[0])
    circuit.cx(qr[0], qr[1])
    circuit.measure(qr, cr)
    return circuit


@pytest.fixture()
def multiple_registers_circuit():
    """Circuit with multiple registers."""
    qr1 = QuantumRegister(2, name="q1")
    qr2 = QuantumRegister(1, name="q2")
    cr1 = ClassicalRegister(2, name="c1")
    cr2 = ClassicalRegister(1, name="c2")
    circuit = QuantumCircuit(qr1, qr2, cr1, cr2, name="multi_reg")
    circuit.h(qr1[0])
    circuit.cx(qr1[0], qr1[1])
    circuit.h(qr2[0])
    circuit.measure(qr1, cr1)
    circuit.measure(qr2, cr2)
    return circuit


@pytest.fixture()
def composite_gate_circuit():
    """Circuit with a composite (custom) gate."""
    # Create a custom gate from a circuit
    sub_circuit = QuantumCircuit(2, name="bell_prep")
    sub_circuit.h(0)
    sub_circuit.cx(0, 1)
    bell_gate = sub_circuit.to_gate()

    # Use the custom gate in a larger circuit
    circuit = QuantumCircuit(2, 2)
    circuit.append(bell_gate, [0, 1])
    circuit.measure([0, 1], [0, 1])
    return circuit
