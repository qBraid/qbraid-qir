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

from qbraid_qir.qasm3.convert import qasm3_to_qir
from tests.qasm3_qir.fixtures.basic_gates import (
    double_op_tests,
    rotation_tests,
    single_op_tests,
    triple_op_tests,
)
from tests.qir_utils import (
    check_attributes,
    check_barrier,
    check_measure_op,
    check_resets,
    check_single_qubit_gate_op,
    check_single_qubit_rotation_op,
    check_three_qubit_gate_op,
    check_two_qubit_gate_op,
)


# 1. Test qubit declarations in different ways
def test_qubit_declarations():
    """Test qubit declarations in different ways"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit q1;
    qubit[2] q2;
    qreg q3[3];
    qubit[1] q4;
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 7, 0)


# 2. Test clbit declarations in different ways
def test_clbit_declarations():
    """Test clbit declarations in different ways"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    bit c1;
    bit[2] c2;
    creg c3[3];
    bit[1] c4;
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 0, 7)


# 3. Test qubit and clbit declarations in different ways
def test_qubit_clbit_declarations():
    """Test qubit and clbit declarations in different ways"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";

    // qubit declarations
    qubit q1;
    qubit[2] q2;
    qreg q3[3];
    qubit[1] q4;

    // clbit declarations
    bit c1;
    bit[2] c2;
    creg c3[3];
    bit[1] c4;
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 7, 7)


# 4. Test reset operations in different ways
def test_reset_operations():
    """Test reset operations in different ways"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";

    // qubit declarations
    qubit q1;
    qubit[2] q2;
    qreg q3[3];

    // reset operations
    reset q1;
    reset q2[1];
    reset q3[2];
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 6, 0)
    check_resets(generated_qir, expected_resets=3, qubit_list=[0, 2, 5])


def test_incorrect_resets():
    undeclared = """
    OPENQASM 3;
    include "stdgates.inc";

    qubit[3] q1;

    // undeclared register 
    reset q2[0];
    """
    with pytest.raises(ValueError):
        _ = qasm3_to_qir(undeclared)

    index_error = """
    OPENQASM 3;
    include "stdgates.inc";

    qubit[2] q1;

    // out of bounds 
    reset q1[4];
    """
    with pytest.raises(ValueError):
        _ = qasm3_to_qir(index_error)


# 5. Test barrier operations in different ways
def test_barrier():
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";

    qubit[2] q1;
    qubit[5] q2;
    qubit q3;

    bit[2] c;
    bit c2;
    

    // Only full barrier supported in QIR
    barrier q1, q2, q3; 
    barrier q2, q3, q1;
    barrier q1[0], q1[1], q2[:], q3[0];
    barrier q1, q2[0:5], q3[:];
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 8, 3)
    check_barrier(generated_qir, expected_barriers=4)


def test_incorrect_barrier():
    undeclared = """
    OPENQASM 3;

    qubit[3] q1;

    barrier q2;
    """

    with pytest.raises(ValueError, match=r"Missing register declaration for q2 .*"):
        _ = qasm3_to_qir(undeclared)

    out_of_bounds = """
    OPENQASM 3;

    qubit[2] q1;

    barrier q1[:4];
    """

    with pytest.raises(ValueError, match="Index 3 out of range for register of size 2 in qubit"):
        _ = qasm3_to_qir(out_of_bounds)

    duplicate = """
    OPENQASM 3;

    qubit[2] q1;

    barrier q1, q1;
    """

    with pytest.raises(ValueError, match=r"Duplicate qubit .*argument"):
        _ = qasm3_to_qir(duplicate)


# 6. Test measurement operations in different ways
def test_measure():
    qasm3_string = """
    OPENQASM 3;

    qubit[2] q1;
    qubit[5] q2;
    qubit q3;

    bit[2] c1;
    bit c2;

    // supported
    c1 = measure q1;
    measure q1 -> c1;
    c2[0] = measure q3[0];
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 8, 3)
    qubit_list = [0, 1, 0, 1, 7]
    bit_list = [0, 1, 0, 1, 2]

    check_measure_op(generated_qir, 5, qubit_list, bit_list)


def test_incorrect_measure():
    def run_test(qasm3_code, error_message):
        with pytest.raises(ValueError, match=error_message):
            _ = qasm3_to_qir(qasm3_code)

    # Test for range based measurement not supported
    run_test(
        """
        OPENQASM 3;
        qubit[2] q1;
        bit[2] c1;
        c1[0:2] = measure q1[0:2];  // not supported 
    """,
        r"Range based measurement .* not supported at the moment",
    )

    # Test for undeclared register q2
    run_test(
        """
        OPENQASM 3;
        qubit[2] q1;
        bit[2] c1;
        c1[0] = measure q2[0];  // undeclared register
    """,
        r"Missing register declaration for q2 .*",
    )

    # Test for undeclared register c2
    run_test(
        """
        OPENQASM 3;
        qubit[2] q1;
        bit[2] c1;
        measure q1 -> c2;  // undeclared register
    """,
        r"Missing register declaration for c2 .*",
    )

    # Test for size mismatch between q1 and c2
    run_test(
        """
        OPENQASM 3;
        qubit[2] q1;
        bit[2] c1;
        bit[1] c2;
        c2 = measure q1;  // size mismatch
    """,
        r"Register sizes of q1 and c2 do not match .*",
    )

    # Test for out of bounds index for q1
    run_test(
        """
        OPENQASM 3;
        qubit[2] q1;
        bit[2] c1;
        measure q1[3] -> c1[0];  // out of bounds
    """,
        r"Index 3 out of range for register of size 2 in qubit",
    )

    # Test for out of bounds index for c1
    run_test(
        """
        OPENQASM 3;
        qubit[2] q1;
        bit[2] c1;
        measure q1 -> c1[3];  // out of bounds
    """,
        r"Index 3 out of range for register of size 2 in clbit",
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
    with pytest.raises(ValueError, match=r"Missing register declaration for q2 .*"):
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
    with pytest.raises(ValueError, match=r"Unsupported / undeclared QASM operation: u_abc"):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
            include "stdgates.inc";

            qubit[2] q1;
            u_abc(0.5, 0.5, 0.5) q1;  // unsupported gate
            """
        )
    # two qubits
    with pytest.raises(ValueError, match=r"Unsupported / undeclared QASM operation: u_abc"):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
            include "stdgates.inc";

            qubit[2] q1;
            u_abc(0.5, 0.5, 0.5) q1[0], q1[1];  // unsupported gate
            """
        )
    # three qubits
    with pytest.raises(ValueError, match=r"Unsupported / undeclared QASM operation: u_abc"):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
            include "stdgates.inc";

            qubit[3] q1;
            u_abc(0.5, 0.5, 0.5) q1[0], q1[1], q1[2];  // unsupported gate
            """
        )

    # Invalid application of gate according to register size
    with pytest.raises(ValueError, match=r"Invalid number of qubits 3 for operation .*"):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
            include "stdgates.inc";

            qubit[3] q1;
            cx q1;  // invalid application of gate, as we apply it to 3 qubits in blocks of 2
            """
        )

    # Invalid use of variables in gate application

    with pytest.raises(ValueError, match=r"Unsupported parameter type .* for operation .*"):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
            include "stdgates.inc";

            qubit[2] q1;
            rx(a) q1; // unsupported parameter type
            """
        )
