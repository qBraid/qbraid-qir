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

from qbraid_qir.qasm3.maps import (
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
already_tested_single_op = ["id", "si", "ti", "v", "sx", "vi", "sxdg"]
for gate in already_tested_single_op:
    single_op_tests.remove(_fixture_name(gate))

rotation_tests = [_fixture_name(s) for s in PYQIR_ONE_QUBIT_ROTATION_MAP if "u" not in s.lower()]
already_tested_rotation = ["prx", "phaseshift", "p", "gpi", "gpi2"]
for gate in already_tested_rotation:
    rotation_tests.remove(_fixture_name(gate))

double_op_tests = [_fixture_name(s) for s in PYQIR_TWO_QUBIT_OP_MAP]
already_tested_double_op = [
    "cv",
    "cy",
    "xx",
    "xy",
    "yy",
    "zz",
    "pswap",
    "cp",
    "cp00",
    "cp01",
    "cp10",
    "cphaseshift",
    "cphaseshift00",
    "cphaseshift01",
    "cphaseshift10",
    "ecr",
    "ms",
]
for gate in already_tested_double_op:
    double_op_tests.remove(_fixture_name(gate))

triple_op_tests = [_fixture_name(s) for s in PYQIR_THREE_QUBIT_OP_MAP]
already_tested_triple_op = ["ccnot", "cswap"]
for gate in already_tested_triple_op:
    triple_op_tests.remove(_fixture_name(gate))

custom_op_tests = [_fixture_name(s) for s in CUSTOM_OPS]
