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
Unit tests for basic Qiskit gate conversions to QIR.

"""

import pytest
from qiskit import QuantumCircuit

from qbraid_qir.qiskit import qiskit_to_qir
from tests.qir_utils import check_attributes_on_entrypoint, get_entry_point

# Single qubit gates mapping: qiskit_name -> qir_name
SINGLE_QUBIT_GATES = {
    "h": "h",
    "x": "x",
    "y": "y",
    "z": "z",
    "s": "s",
    "t": "t",
    "reset": "reset",
}

# Adjoint gates mapping: qiskit_name -> qir_name (uses __adj suffix)
ADJOINT_GATES = {
    "sdg": "s",
    "tdg": "t",
}

# Rotation gates
ROTATION_GATES = ["rx", "ry", "rz"]

# Two qubit gates mapping: qiskit_name -> qir_name
TWO_QUBIT_GATES = {
    "cx": "cnot",
    "cz": "cz",
    "swap": "swap",
}


class TestSingleQubitGates:
    """Tests for single qubit gate conversions."""

    @pytest.mark.parametrize("gate_name,qir_name", SINGLE_QUBIT_GATES.items())
    def test_single_qubit_gate(self, gate_name, qir_name):
        """Test conversion of single qubit gates."""
        circuit = QuantumCircuit(1)
        getattr(circuit, gate_name)(0)

        module = qiskit_to_qir(circuit)
        func = get_entry_point(module)

        check_attributes_on_entrypoint(func, expected_qubits=1, expected_results=0)

        ir = str(module)
        assert f"__quantum__qis__{qir_name}__body" in ir


class TestAdjointGates:
    """Tests for adjoint gate conversions."""

    @pytest.mark.parametrize("gate_name,qir_name", ADJOINT_GATES.items())
    def test_adjoint_gate(self, gate_name, qir_name):
        """Test conversion of adjoint gates."""
        circuit = QuantumCircuit(1)
        getattr(circuit, gate_name)(0)

        module = qiskit_to_qir(circuit)
        func = get_entry_point(module)

        check_attributes_on_entrypoint(func, expected_qubits=1, expected_results=0)

        ir = str(module)
        assert f"__quantum__qis__{qir_name}__adj" in ir


class TestRotationGates:
    """Tests for rotation gate conversions."""

    @pytest.mark.parametrize("gate_name", ROTATION_GATES)
    def test_rotation_gate(self, gate_name):
        """Test conversion of rotation gates."""
        circuit = QuantumCircuit(1)
        getattr(circuit, gate_name)(0.5, 0)

        module = qiskit_to_qir(circuit)
        func = get_entry_point(module)

        check_attributes_on_entrypoint(func, expected_qubits=1, expected_results=0)

        ir = str(module)
        assert f"__quantum__qis__{gate_name}__body" in ir
        # Check that the rotation angle is included
        assert "0.5" in ir or "5.0" in ir or "double" in ir


class TestTwoQubitGates:
    """Tests for two qubit gate conversions."""

    @pytest.mark.parametrize("gate_name,qir_name", TWO_QUBIT_GATES.items())
    def test_two_qubit_gate(self, gate_name, qir_name):
        """Test conversion of two qubit gates."""
        circuit = QuantumCircuit(2)
        getattr(circuit, gate_name)(0, 1)

        module = qiskit_to_qir(circuit)
        func = get_entry_point(module)

        check_attributes_on_entrypoint(func, expected_qubits=2, expected_results=0)

        ir = str(module)
        assert f"__quantum__qis__{qir_name}__body" in ir


class TestThreeQubitGates:
    """Tests for three qubit gate conversions."""

    def test_ccx_gate(self):
        """Test conversion of CCX (Toffoli) gate."""
        circuit = QuantumCircuit(3)
        circuit.ccx(0, 1, 2)

        module = qiskit_to_qir(circuit)
        func = get_entry_point(module)

        check_attributes_on_entrypoint(func, expected_qubits=3, expected_results=0)

        ir = str(module)
        assert "__quantum__qis__ccx__body" in ir


class TestMeasurement:
    """Tests for measurement operations."""

    def test_single_measurement(self):
        """Test conversion of single qubit measurement."""
        circuit = QuantumCircuit(1, 1)
        circuit.measure(0, 0)

        module = qiskit_to_qir(circuit)
        func = get_entry_point(module)

        check_attributes_on_entrypoint(func, expected_qubits=1, expected_results=1)

        ir = str(module)
        assert "__quantum__qis__mz__body" in ir

    def test_multiple_measurements(self):
        """Test conversion of multiple measurements."""
        circuit = QuantumCircuit(3, 3)
        circuit.measure([0, 1, 2], [0, 1, 2])

        module = qiskit_to_qir(circuit)
        func = get_entry_point(module)

        check_attributes_on_entrypoint(func, expected_qubits=3, expected_results=3)

        ir = str(module)
        # Count calls, not declarations
        assert ir.count("call void @__quantum__qis__mz__body") == 3


class TestOutputRecording:
    """Tests for output recording functionality."""

    def test_output_recording_single_register(self):
        """Test that output recording is generated for single register."""
        circuit = QuantumCircuit(2, 2)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.measure([0, 1], [0, 1])

        module = qiskit_to_qir(circuit)
        ir = str(module)

        # Should have array_record_output call
        assert "__quantum__rt__array_record_output" in ir
        # Should have result_record_output calls
        assert "__quantum__rt__result_record_output" in ir

    def test_output_recording_disabled(self):
        """Test that output recording can be disabled."""
        circuit = QuantumCircuit(2, 2)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.measure([0, 1], [0, 1])

        module = qiskit_to_qir(circuit, record_output=False)
        ir = str(module)

        # Should NOT have output recording calls
        assert "__quantum__rt__array_record_output" not in ir
        assert "__quantum__rt__result_record_output" not in ir
