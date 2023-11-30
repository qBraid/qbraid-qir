# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

import pytest
import cirq

# All of the following dictionaries map from the names of methods on Cirq Circuit objects
# to the name of the equivalent pyqir BasicQisBuilder method

_zero_qubit_operations = {"barrier": "barrier"}

_one_qubit_gates = {
    "H": "h",
    "reset": "reset",
    "T": "t",
    "X": "x",
    "Y": "y",
    "Z": "z",
}


def _fixture_name(s: str) -> str:
    return f"Fixture_{s}"


def _map_gate_name(gate: str) -> str:
    if gate in _one_qubit_gates:
        return _one_qubit_gates[gate]
    else:
        raise ValueError(f"Unknown Cirq gate {gate}")


def _generate_one_qubit_fixture(gate: str):
    @pytest.fixture()
    def test_fixture():
        circuit = cirq.Circuit()
        q = cirq.NamedQubit('q')
        circuit.append(getattr(cirq, gate)(q))
        return _map_gate_name(gate), circuit

    return test_fixture

# Generate simple single-qubit gate fixtures
for gate in _one_qubit_gates.keys():
    name = _fixture_name(gate)
    locals()[name] = _generate_one_qubit_fixture(gate)

single_op_tests = [_fixture_name(s) for s in _one_qubit_gates.keys()]
