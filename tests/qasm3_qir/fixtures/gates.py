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
import os

import pytest

from openqasm3_qir.oq3_maps import (
    PYQIR_ONE_QUBIT_OP_MAP,
    PYQIR_ONE_QUBIT_ROTATION_MAP,
    PYQIR_THREE_QUBIT_OP_MAP,
    PYQIR_TWO_QUBIT_OP_MAP,
)

CUSTOM_OPS = ["simple", "nested", "complex"]

RESOURCES_DIR = os.path.join(os.path.dirname(__file__), "resources")


def resources_file(filename: str) -> str:
    return os.path.join(RESOURCES_DIR, f"{filename}")


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


# Generate double-qubit gate fixtures
for gate in PYQIR_TWO_QUBIT_OP_MAP:
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


# Generate three-qubit gate fixtures
for gate in PYQIR_THREE_QUBIT_OP_MAP:
    name = _fixture_name(gate)
    locals()[name] = _generate_three_qubit_fixture(gate)


def _generate_custom_op_fixture(op_name: str):
    print(os.getcwd())

    @pytest.fixture()
    def test_fixture():
        if not op_name in CUSTOM_OPS:
            raise ValueError(f"Invalid fixture {op_name} for custom ops")
        path = resources_file(f"custom_gate_{op_name}.qasm")
        with open(path, "r", encoding="utf-8") as file:
            return file.read()

    return test_fixture


for test_name in CUSTOM_OPS:
    name = _fixture_name(test_name)
    locals()[name] = _generate_custom_op_fixture(test_name)

single_op_tests = [_fixture_name(s) for s in PYQIR_ONE_QUBIT_OP_MAP]
single_op_tests.remove("Fixture_id")  # as we have already tested x gate
rotation_tests = [_fixture_name(s) for s in PYQIR_ONE_QUBIT_ROTATION_MAP if "u" not in s.lower()]
double_op_tests = [_fixture_name(s) for s in PYQIR_TWO_QUBIT_OP_MAP]
triple_op_tests = [_fixture_name(s) for s in PYQIR_THREE_QUBIT_OP_MAP]
custom_op_tests = [_fixture_name(s) for s in CUSTOM_OPS]

# qasm_input, expected_error
SINGLE_QUBIT_GATE_INCORRECT_TESTS = {
    "missing_register": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        qubit[2] q1;
        h q2;  // undeclared register
        """,
        "Missing register declaration for q2 .*",
    ),
    "undeclared_1qubit_op": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        qubit[2] q1;
        u_abc(0.5, 0.5, 0.5) q1;  // unsupported gate
        """,
        "Unsupported / undeclared QASM operation: u_abc",
    ),
    "undeclared_1qubit_op_with_indexing": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        qubit[2] q1;
        u_abc(0.5, 0.5, 0.5) q1[0], q1[1];  // unsupported gate
        """,
        "Unsupported / undeclared QASM operation: u_abc",
    ),
    "undeclared_3qubit_op": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        qubit[3] q1;
        u_abc(0.5, 0.5, 0.5) q1[0], q1[1], q1[2];  // unsupported gate
        """,
        "Unsupported / undeclared QASM operation: u_abc",
    ),
    "invalid_gate_application": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        qubit[3] q1;
        cx q1;  // invalid application of gate, as we apply it to 3 qubits in blocks of 2
        """,
        "Invalid number of qubits 3 for operation .*",
    ),
    "unsupported_parameter_type": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        qubit[2] q1;
        rx(a) q1; // unsupported parameter type
        """,
        "Undefined identifier a in.*",
    ),
}

# qasm_input, expected_error
CUSTOM_GATE_INCORRECT_TESTS = {
    "undeclared_custom": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        qubit[2] q1;
        custom_gate q1;  // undeclared gate
        """,
        "Unsupported / undeclared QASM operation: custom_gate",
    ),
    "parameter_mismatch": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        gate custom_gate(a,b) p, q{
            rx(a) p;
            ry(b) q;
        }

        qubit[2] q1;
        custom_gate(0.5) q1;  // parameter count mismatch
        """,
        "Parameter count mismatch for gate custom_gate. Expected 2 but got 1 .*",
    ),
    "qubit_mismatch": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        gate custom_gate(a,b) p, q{
            rx(a) p;
            ry(b) q;
        }

        qubit[3] q1;
        custom_gate(0.5, 0.5) q1;  // qubit count mismatch
        """,
        "Qubit count mismatch for gate custom_gate. Expected 2 but got 3 .*",
    ),
    "indexing_not_supported": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        gate custom_gate(a,b) p, q{
            rx(a) p;
            ry(b) q[0];
        }

        qubit[2] q1;
        custom_gate(0.5, 0.5) q1;  // indexing not supported
        """,
        "Indexing .* not supported in gate definition",
    ),
    "recursive_definition": (
        """
        OPENQASM 3;
        include "stdgates.inc";

        gate custom_gate(a,b) p, q{
            custom_gate(a,b) p, q;
        }

        qubit[2] q1;
        custom_gate(0.5, 0.5) q1;  // recursive definition
        """,
        "Recursive definitions not allowed .*",
    ),
}
