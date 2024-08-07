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
Module containing unit tests for parsing, unrolling, and
converting OpenQASM3 programs that contain subroutines.

"""

import pytest

from qbraid_qir.qasm3 import qasm3_to_qir
from qbraid_qir.qasm3.exceptions import Qasm3ConversionError
from tests.qasm3_qir.fixtures.subroutines import SUBROUTINE_INCORRECT_TESTS
from tests.qir_utils import (
    check_attributes,
    check_single_qubit_gate_op,
    check_single_qubit_rotation_op,
)


def test_function_declaration():
    """Test that a function declaration is correctly parsed."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";
    def my_function(qubit q) {
        h q;
        return;
    }
    qubit q;
    my_function(q);
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1, 0)
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")


def test_simple_function_call():
    """Test that a simple function call is correctly parsed."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(qubit a, float[32] b) {
        rx(b) a;
        float[64] c = 2*b;
        rx(c) a;
        return;
    }
    qubit q;
    bit c;
    float[32] r = 3.14;
    my_function(q, r);

    measure q -> c[0];
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()
    for line in generated_qir:
        print(line)

    check_attributes(generated_qir, 1, 1)
    check_single_qubit_rotation_op(generated_qir, 2, [0, 0], [3.14, 6.28], "rx")


def test_const_visible_in_function_call():
    """Test that a constant is visible in a function call."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";
    const float[32] pi2 = 3.14;

    def my_function(qubit q) {
        rx(pi2) q;
        return;
    }
    qubit q;
    my_function(q);
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1, 0)
    check_single_qubit_rotation_op(generated_qir, 1, [0], [3.14], "rx")


def test_update_variable_in_function():
    """Test that variable update works correctly in a function."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit q) {
        float[32] a = 3.14;
        a = 2*a;
        rx(a) q;
        return;
    }
    qubit q;
    my_function(q);
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1, 0)
    check_single_qubit_rotation_op(generated_qir, 1, [0], [6.28], "rx")


def test_function_call_in_expression():
    """Test that a function call in an expression is correctly parsed."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit q) -> bool{
        h q;
        return true;
    }
    qubit q;
    bool b = my_function(q);
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1, 0)
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")


def test_function_call_with_return():
    """Test that a function call with a return value is correctly parsed."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit q) -> float[32] {
        h q;
        return 3.14;
    }
    qubit q;
    float[32] r = my_function(q);
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1, 0)
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")


def test_return_values_from_function():
    """Test that the values returned from a function are used correctly in other function."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit q) -> float[32] {
        h q;
        return 3.14;
    }
    def my_function_2(qubit q, float[32] r) {
        rx(r) q;
        return;
    }
    qubit[2] q;
    float[32] r1 = my_function(q[0]);
    my_function_2(q[0], r1);

    array[float[32], 1, 1] r2 = {{3.14}};
    my_function_2(q[1], r2[0,0]);

    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 2, 0)
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")
    check_single_qubit_rotation_op(generated_qir, 2, [0, 1], [3.14, 3.14], "rx")


def test_function_call_with_custom_gate():
    """Test that a function call with a custom gate is correctly parsed."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    gate my_gate(a) q { rx(a) q; }

    def my_function(qubit a, float[32] b) {
        float[64] c = 2*b;
        my_gate(b) a;
        my_gate(c) a;
        return;
    }
    qubit q;
    bit c;
    float[32] r = 3.14;
    my_function(q, r);

    measure q -> c[0];
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1, 1)
    check_single_qubit_rotation_op(generated_qir, 2, [0, 0], [3.14, 6.28], "rx")


@pytest.mark.skip(reason="Not implemented for loop statement updates in scope")
def test_function_with_loop():
    """Test that a function with a loop is correctly parsed."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit[3] q2) {
        for int[32] i in [0:2] {
            h q2[i];
        }
        return;
    }
    qubit[3] q1;
    my_function(q1);
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 3, 0)
    check_single_qubit_gate_op(generated_qir, 3, [0, 1, 2], "h")


@pytest.mark.parametrize("data_type", ["int[32] a = 1;", "float[32] a = 1.0;", "bit a = 0;"])
def test_return_value_mismatch(data_type):
    """Test that returning a value of incorrect type raises error."""
    qasm_str = (
        """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit q) {
        h q;
    """
        + data_type
        + """
        return a;
    }
    qubit q;
    my_function(q);
    """
    )

    with pytest.raises(
        Qasm3ConversionError, match=r"Return type mismatch for subroutine 'my_function'.*"
    ):
        qasm3_to_qir(qasm_str)


@pytest.mark.parametrize("keyword", ["pi", "euler", "tau"])
def test_subroutine_keyword_naming(keyword):
    """Test that using a keyword as a subroutine name raises error."""
    qasm_str = f"""OPENQASM 3;
    include "stdgates.inc";

    def {keyword}(qubit q) {{
        h q;
        return;
    }}
    qubit q;
    {keyword}(q);
    """

    with pytest.raises(
        Qasm3ConversionError, match=f"Subroutine name '{keyword}' is a reserved keyword"
    ):
        qasm3_to_qir(qasm_str)


@pytest.mark.parametrize("qubit_params", ["q", "q[:2]", "q[{0,1}]"])
def test_qubit_size_arg_mismatch(qubit_params):
    """Test that passing a qubit of different size raises error."""
    qasm_str = (
        """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit[3] q) {
        h q;
        return;
    }
    qubit[2] q;
    my_function("""
        + qubit_params
        + """);
    """
    )

    with pytest.raises(
        Qasm3ConversionError,
        match="Qubit register size mismatch for function 'my_function'. "
        "Expected 3 in variable 'q' but got 2",
    ):
        qasm3_to_qir(qasm_str)


@pytest.mark.parametrize("test_name", SUBROUTINE_INCORRECT_TESTS.keys())
def test_incorrect_custom_ops(test_name):
    qasm_input, error_message = SUBROUTINE_INCORRECT_TESTS[test_name]
    with pytest.raises(Qasm3ConversionError, match=error_message):
        _ = qasm3_to_qir(qasm_input)
