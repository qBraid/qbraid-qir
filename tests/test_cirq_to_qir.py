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
# isort: skip_file

import cirq
import pytest

from qbraid_qir.cirq.convert import cirq_to_qir
from tests.fixtures.basic_gates import (
    double_op_tests,
    measurement_tests,
    rotation_tests,
    single_op_tests,
    triple_op_tests,
)

from .qir_utils import assert_equal_qir
from .test_utils import (
    check_attributes,
    double_op_call_string,
    generic_op_call_string,
    get_entry_point_body,
    initialize_call_string,
    measure_call_string,
    result_record_output_string,
    return_string,
    rotation_call_string,
    single_op_call_string,
)


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
    func = get_entry_point_body(qir_str)
    assert func[0] == initialize_call_string()
    assert func[1] == single_op_call_string(qir_op, 0)
    assert func[2] == return_string()
    assert len(func) == 3


@pytest.mark.parametrize("circuit_name", rotation_tests)
def test_rotation_gates(circuit_name, request):
    qir_op, circuit = request.getfixturevalue(circuit_name)
    generated_qir = str(cirq_to_qir(circuit)).splitlines()
    check_attributes(generated_qir, 1, 1)
    func = get_entry_point_body(generated_qir)
    assert func[0] == initialize_call_string()
    assert func[1] == rotation_call_string(qir_op, 0.5, 0)
    assert func[3] == return_string()
    assert len(func) == 4


@pytest.mark.parametrize("circuit_name", double_op_tests)
def test_double_qubit_gates(circuit_name, request):
    qir_op, circuit = request.getfixturevalue(circuit_name)
    generated_qir = str(cirq_to_qir(circuit)).splitlines()
    check_attributes(generated_qir, 2, 2)
    func = get_entry_point_body(generated_qir)
    assert func[0] == initialize_call_string()
    assert func[1] == double_op_call_string(qir_op, 0, 1)
    assert func[4] == return_string()
    assert len(func) == 5


@pytest.mark.parametrize("circuit_name", triple_op_tests)
def test_triple_qubit_gates(circuit_name, request):
    qir_op, circuit = request.getfixturevalue(circuit_name)
    generated_qir = str(cirq_to_qir(circuit)).splitlines()
    check_attributes(generated_qir, 3, 3)
    func = get_entry_point_body(generated_qir)
    assert func[0] == initialize_call_string()
    assert func[1] == generic_op_call_string(qir_op, [0, 1, 2])
    assert func[5] == return_string()
    assert len(func) == 6


@pytest.mark.parametrize("circuit_name", measurement_tests)
def test_measurement(circuit_name, request):
    qir_op, circuit = request.getfixturevalue(circuit_name)
    module = cirq_to_qir(circuit)
    generated_qir = str(module).splitlines()
    check_attributes(generated_qir, 1, 1)
    func = get_entry_point_body(generated_qir)

    assert func[0] == initialize_call_string()
    assert func[1] == measure_call_string(qir_op, 0, 0)
    assert func[2] == result_record_output_string(0)
    assert func[3] == return_string()
    assert len(func) == 4


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


@pytest.mark.skip(reason="Test case incomplete")
def test_qft():
    """Test converting Cirq QFT circuit to QIR."""
    for n in range(2, 5):  # Test for different numbers of qubits
        circuit = cirq.Circuit()
        qubits = [cirq.NamedQubit(f"q{i}") for i in range(n)]
        circuit.append(cirq.qft(*qubits))
        # TODO Add assertions or checks here
