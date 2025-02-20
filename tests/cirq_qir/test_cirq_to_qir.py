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
Module containing unit tests for Cirq to QIR conversion functions.

"""
import os
from pathlib import Path

import cirq
import pyqir
import pytest

from qbraid_qir.cirq import CirqConversionError, cirq_to_qir
from tests.cirq_qir.fixtures.basic_gates import (
    double_op_tests,
    measurement_tests,
    rotation_tests,
    single_op_tests,
    triple_op_tests,
)
from tests.qir_utils import (
    assert_equal_qir,
    check_attributes,
    check_measure_op,
    check_single_qubit_gate_op,
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

RESOURCES_DIR = os.path.join(os.path.dirname(__file__), "resources")


def resources_file(filename: str) -> str:
    return os.path.join(RESOURCES_DIR, f"{filename}.ll")


def compare_reference_ir(generated_bitcode: bytes, name: str) -> None:
    module = pyqir.Module.from_bitcode(pyqir.Context(), generated_bitcode, f"{name}")
    ir = str(module)
    file = os.path.join(os.path.dirname(__file__), f"resources/{name}.ll")
    expected = Path(file).read_text(encoding="utf-8")
    assert ir == expected


def test_cirq_to_qir_type_error():
    """Test raising exception for bad input type."""
    with pytest.raises(TypeError):
        cirq_to_qir(None)


def test_cirq_qir_conversion_error():
    with pytest.raises(TypeError):
        cirq_to_qir(None)


def test_cirq_to_qir_conversion_error():
    """Test raising exception for conversion error."""
    op = cirq.XPowGate(exponent=0.25).controlled().on(cirq.LineQubit(1), cirq.LineQubit(2))
    circuit = cirq.Circuit(op)
    with pytest.raises(CirqConversionError):
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


def test_conditional_gates():
    qubits = [cirq.LineQubit(i) for i in range(3)]
    circuit = cirq.Circuit()

    circuit.append([cirq.H(qubits[0]), cirq.H(qubits[1])])

    circuit.append(cirq.measure(qubits[0]))
    circuit.append(cirq.measure(qubits[1]))

    sub_operation = cirq.Z(qubits[2])
    sub_operation_2 = cirq.rz(0.5).on(qubits[2])

    # This Z gate on qubit 2 will only be executed if the measurement on 0 and 1 qubit is True
    controlled_op_1 = cirq.ClassicallyControlledOperation(sub_operation, conditions=["0", "1"])
    controlled_op_2 = cirq.ClassicallyControlledOperation(sub_operation_2, conditions=["0", "1"])

    circuit.append(controlled_op_1)
    circuit.append(controlled_op_2)

    new_circuit = cirq_to_qir(circuit)
    compare_reference_ir(new_circuit.bitcode, "test_conditional_gates")


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
    assert func[1] == generic_op_call_string(qir_op, [], [0, 1, 2])
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


def test_single_pauli_measurement():
    # single Pauli gate
    qubit = cirq.LineQubit.range(1)
    circuit = cirq.Circuit()
    ps = cirq.X(qubit[0])
    meas_gates = cirq.measure_single_paulistring(ps)
    circuit.append(meas_gates)

    qir_module = cirq_to_qir(circuit, record_output=False)
    generated_qir = str(qir_module).splitlines()

    check_attributes(generated_qir, 1, 1)
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")
    check_measure_op(generated_qir, 1, [0], [0])


def test_pauli_term_measurements():
    # single terms
    qubits = cirq.LineQubit.range(3)
    circuit = cirq.Circuit()
    ps = cirq.X(qubits[0]) * cirq.Y(qubits[1]) * cirq.X(qubits[2])
    meas_gates = cirq.measure_paulistring_terms(ps)
    for gate in meas_gates:
        circuit.append(gate)

    qir_module = cirq_to_qir(circuit, record_output=False)
    generated_qir = str(qir_module).splitlines()

    check_attributes(generated_qir, 3, 3)
    check_single_qubit_gate_op(generated_qir, 1, [1], "sdg")
    check_single_qubit_gate_op(generated_qir, 3, [0, 1, 2], "h")
    check_measure_op(generated_qir, 3, [0, 1, 2], [0, 1, 2])


def test_verify_qir_bell_fixture(pyqir_bell):
    """Test that pyqir fixture generates code equal to test_qir_bell.ll file."""
    test_name = "test_qir_bell"
    filepath = resources_file(test_name)
    assert_equal_qir(pyqir_bell.ir(), filepath)


def test_entry_point_name(cirq_bell):
    """Test that entry point name is consistent with module ID."""
    name = "quantum_123"
    module = cirq_to_qir(cirq_bell, name=name)
    assert module.source_filename == name


def test_convert_bell_compare_file(cirq_bell):
    """Test converting Cirq bell circuit to QIR."""
    test_name = "test_qir_bell"
    filepath = resources_file(test_name)
    module = cirq_to_qir(cirq_bell, name=test_name, initialize_runtime=False, record_output=False)
    assert_equal_qir(str(module), filepath)


@pytest.mark.skip(reason="Test case incomplete")
def test_qft():
    """Test converting Cirq QFT circuit to QIR."""
    for n in range(2, 5):  # Test for different numbers of qubits
        circuit = cirq.Circuit()
        qubits = [cirq.NamedQubit(f"q{i}") for i in range(n)]
        circuit.append(cirq.qft(*qubits))
        # TODO Add assertions or checks here
