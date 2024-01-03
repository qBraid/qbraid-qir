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
Module containing unit tests for Cirq to QIR conversion functions.

"""
import cirq
import pytest

import tests.test_utils as test_utils
from qbraid_qir.cirq.convert import cirq_to_qir
from tests.fixtures.basic_gates import single_op_tests

from .qir_utils import assert_equal_qir


def test_cirq_to_qir_type_error():
    """Test raising exception for bad input type."""
    with pytest.raises(TypeError):
        cirq_to_qir(None)


def test_cirq_to_qir_conversion_error():
    """Test raising exception for conversion error."""
    circuit = cirq.Circuit()
    with pytest.raises(ValueError):
        cirq_to_qir(circuit)


@pytest.mark.parametrize("circuit_name", single_op_tests)
def test_single_qubit_gates(circuit_name, request):
    qir_op, circuit = request.getfixturevalue(circuit_name)
    qir_module = cirq_to_qir(circuit, record_output=False)
    qir_str = str(qir_module).splitlines()
    func = test_utils.get_entry_point_body(qir_str)
    assert func[0] == test_utils.initialize_call_string()
    assert func[1] == test_utils.single_op_call_string(qir_op, 0)
    assert func[2] == test_utils.return_string()
    assert len(func) == 3


def test_verify_qir_bell_fixture(pyqir_bell):
    """Test that pyqir fixture generates code equal to test_qir_bell.ll file."""
    assert_equal_qir(pyqir_bell.ir(), "test_qir_bell")


def test_entry_point_name(cirq_bell):
    """Test that entry point name is consistent with module ID."""
    name = "quantum_123"
    module = cirq_to_qir(cirq_bell, name=name)
    assert module.source_filename == name


def test_convert_bell_compare_file(cirq_bell):
    """Test converting Cirq bell circuit to QIR."""
    test_name = "test_qir_bell"
    module = cirq_to_qir(
        cirq_bell, name=test_name, initialize_runtime=False, record_output=False
    )
    assert_equal_qir(str(module), test_name)
