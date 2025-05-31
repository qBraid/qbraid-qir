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
Module defining QASM3 native gate fixtures for use in tests.

"""
import os

import pytest

# Define native gates that are directly supported by pyqir
NATIVE_SINGLE_QUBIT_GATES = ["id", "x", "y", "z", "h", "s", "sdg", "t", "tdg"]
NATIVE_TWO_QUBIT_GATES = ["cx", "cz", "swap"]
NATIVE_ROTATION_GATES = ["rx", "ry", "rz"]

CUSTOM_OPS = ["simple", "nested", "complex"]

RESOURCES_DIR = os.path.join(os.path.dirname(__file__), "resources")


def resources_file(filename: str) -> str:
    return os.path.join(RESOURCES_DIR, f"{filename}")


def _fixture_name(s: str) -> str:
    return f"Fixture_{s}"


def _validate_gate_name(gate_name: str) -> str:
    if gate_name in NATIVE_SINGLE_QUBIT_GATES:
        return True
    if gate_name in NATIVE_TWO_QUBIT_GATES:
        return True
    if gate_name in NATIVE_ROTATION_GATES:
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
        {gate_name} q[0];
        """
        return qasm3_string

    return test_fixture


# Generate simple single-qubit gate fixtures
for gate in NATIVE_SINGLE_QUBIT_GATES:
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
        {gate_name}(0.5) q[0];
        """
        return qasm3_string

    return test_fixture


# Generate rotation gate fixtures
for gate in NATIVE_ROTATION_GATES:
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
        """
        return qasm3_string

    return test_fixture


# Generate two-qubit gate fixtures
for gate in NATIVE_TWO_QUBIT_GATES:
    name = _fixture_name(gate)
    locals()[name] = _generate_two_qubit_fixture(gate)


def _generate_custom_op_fixture(op_name: str):
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

# Define test groups
single_op_tests = [_fixture_name(s) for s in NATIVE_SINGLE_QUBIT_GATES]
rotation_tests = [_fixture_name(s) for s in NATIVE_ROTATION_GATES]
double_op_tests = [_fixture_name(s) for s in NATIVE_TWO_QUBIT_GATES]
custom_op_tests = [_fixture_name(s) for s in CUSTOM_OPS]
