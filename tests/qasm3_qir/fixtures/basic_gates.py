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
Module defining Cirq basic gate fixtures for use in tests.

"""
import pytest

from qbraid_qir.qasm3.oq3_maps import PYQIR_ONE_QUBIT_OP_MAP, PYQIR_ONE_QUBIT_ROTATION_MAP, PYQIR_TWO_QUBIT_OP_MAP, PYQIR_THREE_QUBIT_OP_MAP

# All of the following dictionaries map from the names of methods on Cirq Circuit objects
# to the name of the equivalent pyqir BasicQisBuilder method



def _fixture_name(s: str) -> str:
    return f"Fixture_{s}"


def _validate_gate_name(gate_name: str) -> str:
    if gate_name in PYQIR_ONE_QUBIT_OP_MAP:
        return True 
    if gate_name in PYQIR_TWO_QUBIT_OP_MAP:
        return True
    if gate_name in PYQIR_ONE_QUBIT_ROTATION_MAP:
        return True
    if gate_name in PYQIR_THREE_QUBIT_OP_MAP:
        return True
    return False

def _generate_one_qubit_fixture(gate_name: str):
    @pytest.fixture()
    def test_fixture():
        if not _validate_gate_name(gate_name):
            raise ValueError(f"Unknown qasm3 gate {gate_name}")
        qasm3_string = f"""
        OPENQASM 3;
        include "stdgates.inc";
        
        qubit[2] q;
        {gate_name} q;
        {gate_name} q[0];
        {gate_name} q[0:2];
        """
        return qasm3_string

    return test_fixture


# Generate simple single-qubit gate fixtures
for gate in PYQIR_ONE_QUBIT_OP_MAP:
    name = _fixture_name(gate)
    locals()[name] = _generate_one_qubit_fixture(gate)


def _generate_rotation_fixture(gate_name: str):
    @pytest.fixture()
    def test_fixture():
        if not _validate_gate_name(gate_name):
            raise ValueError(f"Unknown qasm3 gate {gate_name}")
        
        qasm3_string = f"""
        OPENQASM 3;
        include "stdgates.inc";
        
        qubit[2] q;
        {gate_name}(0.5) q;
        {gate_name}(0.5) q[0];
        """
        return qasm3_string

    return test_fixture


# Generate rotation gate fixtures
for gate in PYQIR_ONE_QUBIT_ROTATION_MAP:
    name = _fixture_name(gate)
    locals()[name] = _generate_rotation_fixture(gate)


def _generate_two_qubit_fixture(gate_name: str):
    @pytest.fixture()
    def test_fixture():
        if not _validate_gate_name(gate_name):
            raise ValueError(f"Unknown qasm3 gate {gate_name}")
        qasm3_string = f"""
        OPENQASM 3;
        include "stdgates.inc";

        qubit[2] q;
        {gate_name} q[0], q[1];
        {gate_name} q;
        """
        return qasm3_string

    return test_fixture


# Create a new function to generate a fixture for n-qubit gates
# def _generate_n_qubit_fixture(gate_name: str, n: int):
#     @pytest.fixture()
#     def test_fixture():
#         circuit = cirq.Circuit()
#         qubits = [cirq.NamedQubit(f"q{i}") for i in range(n)]
#         circuit.append(getattr(cirq, gate_name)(*qubits))


# Generate double-qubit gate fixtures
for gate in  PYQIR_TWO_QUBIT_OP_MAP:
    name = _fixture_name(gate)
    locals()[name] = _generate_two_qubit_fixture(gate)


def _generate_three_qubit_fixture(gate_name: str):
    @pytest.fixture()
    def test_fixture():
        if not _validate_gate_name(gate_name):
            raise ValueError(f"Unknown qasm3 gate {gate_name}")
        qasm3_string = f"""
        OPENQASM 3;
        include "stdgates.inc";

        qubit[3] q;
        {gate_name} q[0], q[1], q[2];
        {gate_name} q;
        """
        return qasm3_string

    return test_fixture


# New function for more complex gate structures:
# def _generate_complex_gate_fixture(gate_sequence):
#     @pytest.fixture()
#     def test_fixture():
#         circuit = cirq.Circuit()
#         qubits = [cirq.NamedQubit(f"q{i}") for i in range(len(gate_sequence))]
#         for gate_op, qubit_indices in gate_sequence:
#             gates_to_apply = [getattr(cirq, gate_op)(qubits[i]) for i in qubit_indices]
#             circuit.append(gates_to_apply)
#         return circuit

#     return test_fixture


# Generate three-qubit gate fixtures
for gate in PYQIR_THREE_QUBIT_OP_MAP:
    name = _fixture_name(gate)
    locals()[name] = _generate_three_qubit_fixture(gate)

single_op_tests = [_fixture_name(s) for s in PYQIR_ONE_QUBIT_OP_MAP]
single_op_tests.remove("Fixture_id") # as we have already tested x gate

rotation_tests = [_fixture_name(s) for s in PYQIR_ONE_QUBIT_ROTATION_MAP]
double_op_tests = [_fixture_name(s) for s in PYQIR_TWO_QUBIT_OP_MAP]
triple_op_tests = [_fixture_name(s) for s in PYQIR_THREE_QUBIT_OP_MAP]
