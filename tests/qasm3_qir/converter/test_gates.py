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
Module containing unit tests for QASM3 to QIR conversion functions.

"""
import pytest

from qbraid_qir.exceptions import Qasm3ConversionError
from qbraid_qir.qasm3.convert import qasm3_to_qir
from tests.qasm3_qir.fixtures.gates import (
    custom_op_tests,
    double_op_tests,
    rotation_tests,
    single_op_tests,
    triple_op_tests,
)
from tests.qir_utils import (
    check_attributes,
    check_custom_qasm_gate_op,
    check_single_qubit_gate_op,
    check_single_qubit_rotation_op,
    check_three_qubit_gate_op,
    check_two_qubit_gate_op,
)


# 7. Test gate operations in different ways
@pytest.mark.parametrize("circuit_name", single_op_tests)
def test_single_qubit_qasm3_gates(circuit_name, request):
    # see _generate_one_qubit_fixture for details
    qubit_list = [0, 1, 0, 0, 1]
    gate_name = circuit_name.removeprefix("Fixture_")

    qasm3_string = request.getfixturevalue(circuit_name)
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    check_single_qubit_gate_op(generated_qir, 5, qubit_list, gate_name)


@pytest.mark.parametrize("circuit_name", double_op_tests)
def test_two_qubit_qasm3_gates(circuit_name, request):
    qubit_list = [[0, 1], [0, 1]]
    gate_name = circuit_name.removeprefix("Fixture_")

    qasm3_string = request.getfixturevalue(circuit_name)
    result = qasm3_to_qir(qasm3_string)

    print(result)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    check_two_qubit_gate_op(generated_qir, 2, qubit_list, gate_name)


@pytest.mark.parametrize("circuit_name", rotation_tests)
def test_rotation_qasm3_gates(circuit_name, request):
    qubit_list = [0, 1, 0]
    param_list = [0.5, 0.5, 0.5]
    gate_name = circuit_name.removeprefix("Fixture_")

    qasm3_string = request.getfixturevalue(circuit_name)
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    check_single_qubit_rotation_op(generated_qir, 3, qubit_list, param_list, gate_name)


@pytest.mark.parametrize("circuit_name", triple_op_tests)
def test_three_qubit_qasm3_gates(circuit_name, request):
    qubit_list = [[0, 1, 2], [0, 1, 2]]
    gate_name = circuit_name.removeprefix("Fixture_")

    qasm3_string = request.getfixturevalue(circuit_name)
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 3, 0)
    check_three_qubit_gate_op(generated_qir, 2, qubit_list, gate_name)


def test_incorrect_single_qubit_gates():
    # Test for undeclared register q2
    with pytest.raises(Qasm3ConversionError, match=r"Missing register declaration for q2 .*"):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
            include "stdgates.inc";

            qubit[2] q1;
            h q2;  // undeclared register
            """
        )

    # Test for unsupported gate : TO DO

    # one qubit
    with pytest.raises(
        Qasm3ConversionError, match=r"Unsupported / undeclared QASM operation: u_abc"
    ):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
            include "stdgates.inc";

            qubit[2] q1;
            u_abc(0.5, 0.5, 0.5) q1;  // unsupported gate
            """
        )
    # two qubits
    with pytest.raises(
        Qasm3ConversionError, match=r"Unsupported / undeclared QASM operation: u_abc"
    ):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
            include "stdgates.inc";

            qubit[2] q1;
            u_abc(0.5, 0.5, 0.5) q1[0], q1[1];  // unsupported gate
            """
        )
    # three qubits
    with pytest.raises(
        Qasm3ConversionError, match=r"Unsupported / undeclared QASM operation: u_abc"
    ):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
            include "stdgates.inc";

            qubit[3] q1;
            u_abc(0.5, 0.5, 0.5) q1[0], q1[1], q1[2];  // unsupported gate
            """
        )

    # Invalid application of gate according to register size
    with pytest.raises(Qasm3ConversionError, match=r"Invalid number of qubits 3 for operation .*"):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
            include "stdgates.inc";

            qubit[3] q1;
            cx q1;  // invalid application of gate, as we apply it to 3 qubits in blocks of 2
            """
        )

    # Invalid use of variables in gate application

    with pytest.raises(Qasm3ConversionError, match=r"Undefined identifier a in.*"):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
            include "stdgates.inc";

            qubit[2] q1;
            rx(a) q1; // unsupported parameter type
            """
        )


@pytest.mark.parametrize("test_name", custom_op_tests)
def test_custom_ops(test_name, request):
    qasm3_string = request.getfixturevalue(test_name)
    gate_type = test_name.removeprefix("Fixture_")
    result = qasm3_to_qir(qasm3_string)

    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)

    # Check for custom gate definition
    check_custom_qasm_gate_op(generated_qir, gate_type)


def test_incorrect_custom_ops():
    #  1. Undeclared gate application
    with pytest.raises(
        Qasm3ConversionError, match=r"Unsupported / undeclared QASM operation: custom_gate"
    ):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
            include "stdgates.inc";

            qubit[2] q1;
            custom_gate q1;  // undeclared gate
            """
        )

    # 2. Parameter mismatch
    with pytest.raises(
        Qasm3ConversionError,
        match=r"Parameter count mismatch for gate custom_gate. Expected 2 but got 1 .*",
    ):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
            include "stdgates.inc";

            gate custom_gate(a,b) p, q{
                rx(a) p;
                ry(b) q;
            }

            qubit[2] q1;
            custom_gate(0.5) q1;  // parameter count mismatch
            """
        )

    # 3. Qubit count mismatch
    with pytest.raises(
        Qasm3ConversionError,
        match=r"Qubit count mismatch for gate custom_gate. Expected 2 but got 3 .*",
    ):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
            include "stdgates.inc";

            gate custom_gate(a,b) p, q{
                rx(a) p;
                ry(b) q;
            }

            qubit[3] q1;
            custom_gate(0.5, 0.5) q1;  // qubit count mismatch
            """
        )
    # 4. Argument indexing in gate definition
    with pytest.raises(Qasm3ConversionError, match=r"Indexing .* not supported in gate definition"):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
            include "stdgates.inc";

            gate custom_gate(a,b) p, q{
                rx(a) p;
                ry(b) q[0];
            }

            qubit[2] q1;
            custom_gate(0.5, 0.5) q1;  // indexing not supported
            """
        )
