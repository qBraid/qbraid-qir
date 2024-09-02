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
converting OpenQASM3 programs that contain arrays in subroutines.

"""

import pytest

from qbraid_qir.qasm3 import qasm3_to_qir
from qbraid_qir.qasm3.exceptions import Qasm3ConversionError
from tests.qir_utils import check_attributes, check_single_qubit_rotation_op


def test_simple_function_call():
    """Test that a simple function call is correctly parsed."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(qubit a, readonly array[int[8], 2, 2] my_arr) {
        return;
    }
    qubit q;
    array[int[8], 2, 2] arr;
    my_function(q, arr);

    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1, 0)


def test_passing_array_to_function():
    """Test that passing an array to a function is correctly parsed."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(readonly array[int[8], 2, 2] my_arr, qubit q) {
        rx(my_arr[0][0]) q;
        rx(my_arr[0][1]) q;
        rx(my_arr[1][0]) q;
        rx(my_arr[1][1]) q;

        return;
    }
    qubit my_q;
    array[int[8], 2, 2] arr = { {1, 2}, {3, 4} };
    my_function(arr, my_q);
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1, 0)
    check_single_qubit_rotation_op(
        generated_qir, 4, qubit_list=[0, 0, 0, 0], param_list=[1, 2, 3, 4], gate_name="rx"
    )


def test_passing_subarray_to_function():
    """Test that passing a smaller subarray to a function is correctly parsed."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(readonly array[int[8], 2, 2] my_arr, qubit q) {
        rx(my_arr[0][0]) q;
        rx(my_arr[0][1]) q;
        return;
    }
    qubit my_q;
    array[int[8], 4, 3] arr_1 = { {1, 2, 3}, {4, 5, 6}, {7, 8, 9}, {10, 11, 12} };
    array[int[8], 2, 2] arr_2 = { {1, 2}, {3, 4} };
    my_function(arr_1[1:2][1:2], my_q);
    my_function(arr_2[0:1, :], my_q);

    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1, 0)
    check_single_qubit_rotation_op(
        generated_qir, 2, qubit_list=[0] * 4, param_list=[5, 6, 1, 2], gate_name="rx"
    )


def test_passing_array_with_dim_identifier():
    """Test that passing an array with a dimension identifier is correctly parsed."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(readonly array[int[8], #dim = 2] my_arr, qubit q) {
        rx(my_arr[0][0]) q;
        rx(my_arr[0][1]) q;
        return;
    }
    qubit my_q;
    array[int[8], 2, 2, 2] arr = { { {1, 2}, {3, 4} }, { {5, 6}, {7, 8} } };
    my_function(arr[0, :, :], my_q);
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1, 0)
    check_single_qubit_rotation_op(
        generated_qir, 2, qubit_list=[0] * 2, param_list=[1, 2], gate_name="rx"
    )


def test_pass_multiple_arrays_to_function():
    """Test that passing multiple arrays to a function is correctly parsed."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(readonly array[int[8], 2, 2] my_arr1, 
                    readonly array[int[8], 2, 2] my_arr2, 
                    qubit q) {
        for int[8] i in [0:1] {
            rx(my_arr1[i][0]) q;
            rx(my_arr2[i][1]) q;
        }

        return;
    }
    qubit my_q;
    array[int[8], 2, 2] arr_1 = { {1, 2}, {3, 4} };
    array[int[8], 2, 2] arr_2 = { {5, 6}, {7, 8} };
    my_function(arr_1, arr_2, my_q);
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1, 0)
    check_single_qubit_rotation_op(
        generated_qir, 4, qubit_list=[0] * 4, param_list=[1, 6, 3, 8], gate_name="rx"
    )


def test_non_array_raises_error():
    """Test that passing a non-array to an array parameter raises error."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(qubit a, readonly array[int[8], 2, 2] my_arr) {
        return;
    }
    qubit q;
    int[8] arr;
    my_function(q, arr);

    """

    with pytest.raises(
        Qasm3ConversionError,
        match=r"Expecting type 'array\[int\[8\],...\]' for 'my_arr' in function 'my_function'."
        r" Variable 'arr' has type 'int\[8\]'.",
    ):
        qasm3_to_qir(qasm_str)


def test_literal_raises_error():
    """Test that passing a literal to an array parameter raises error."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(qubit a, readonly array[int[8], 2, 2] my_arr) {
        return;
    }
    qubit q;
    my_function(q, 5);

    """

    with pytest.raises(
        Qasm3ConversionError,
        match=r"Expecting type 'array\[int\[8\],...\]' for 'my_arr' in function 'my_function'."
        r" Literal 5 found in function call",
    ):
        qasm3_to_qir(qasm_str)


def test_type_mismatch_in_array():
    """Test that passing an array of different type raises error."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(qubit a, readonly array[int[8], 2, 2] my_arr) {
        return;
    }
    qubit q;
    array[uint[32], 2, 2] arr;
    my_function(q, arr);

    """

    with pytest.raises(
        Qasm3ConversionError,
        match=r"Expecting type 'array\[int\[8\],...\]' for 'my_arr' in function 'my_function'."
        r" Variable 'arr' has type 'array\[uint\[32\], 2, 2\]'.",
    ):
        qasm3_to_qir(qasm_str)


def test_dimension_count_mismatch_1():
    """Test that passing an array with different dimension count raises error."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(qubit a, readonly array[int[8], 2, 2] my_arr) {
        return;
    }
    qubit q;
    array[int[8], 2] arr;
    my_function(q, arr);

    """

    with pytest.raises(
        Qasm3ConversionError,
        match=r"Dimension mismatch for 'my_arr' in function 'my_function'. Expected 2 dimensions"
        r" but variable 'arr' has 1",
    ):
        qasm3_to_qir(qasm_str)


def test_dimension_count_mismatch_2():
    """Test that passing an array with different dimension count raises error."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(qubit a, readonly array[int[8], #dim = 4] my_arr) {
        return;
    }
    qubit q;
    array[int[8], 2, 2] arr;
    my_function(q, arr);

    """

    with pytest.raises(
        Qasm3ConversionError,
        match=r"Dimension mismatch for 'my_arr' in function 'my_function'. Expected 4 dimensions "
        r"but variable 'arr' has 2",
    ):
        qasm3_to_qir(qasm_str)


def test_qubit_passed_as_array():
    """Test that passing a qubit as an array raises error."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(mutable array[int[8], 2, 2] my_arr) {
        return;
    }
    qubit[2] q;
    my_function(q);

    """

    with pytest.raises(
        Qasm3ConversionError,
        match=r"Expecting type 'array\[int\[8\],...\]' for 'my_arr' in function 'my_function'."
        r" Qubit register 'q' found for function call",
    ):
        qasm3_to_qir(qasm_str)


def test_invalid_dimension_number():
    """Test that passing an array with invalid dimension number raises error."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(qubit a, readonly array[int[8], #dim = -3] my_arr) {
        return;
    }
    qubit q;
    array[int[8], 2, 2, 2] arr;
    my_function(q, arr);

    """

    with pytest.raises(
        Qasm3ConversionError,
        match=r"Invalid number of dimensions -3 for 'my_arr' in function 'my_function'",
    ):
        qasm3_to_qir(qasm_str)


def test_invalid_non_int_dimensions_1():
    """Test that passing an array with non-integer dimensions raises error."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(qubit a, mutable array[int[8], #dim = 2.5] my_arr) {
        return;
    }
    qubit q;
    array[int[8], 2, 2] arr;
    my_function(q, arr);

    """

    with pytest.raises(
        Qasm3ConversionError,
        match=r"Invalid value 2.5 with type <class 'openqasm3.ast.FloatLiteral'> for required type "
        r"<class 'openqasm3.ast.IntType'>",
    ):
        qasm3_to_qir(qasm_str)


def test_invalid_non_int_dimensions_2():
    """Test that passing an array with non-integer dimensions raises error."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(qubit a, readonly array[int[8], 2.5, 2] my_arr) {
        return;
    }
    qubit q;
    array[int[8], 2, 2] arr;
    my_function(q, arr);

    """

    with pytest.raises(
        Qasm3ConversionError,
        match=r"Invalid value 2.5 with type <class 'openqasm3.ast.FloatLiteral'> for required type"
        r" <class 'openqasm3.ast.IntType'>",
    ):
        qasm3_to_qir(qasm_str)


def test_extra_dimensions_for_array():
    """Test that passing an array with extra dimensions raises error."""
    qasm_str = """OPENQASM 3.0;
    include "stdgates.inc";

    def my_function(qubit a, mutable array[int[8], 4, 2] my_arr) {
        return;
    }
    qubit q;
    array[int[8], 2, 2] arr;
    my_function(q, arr);

    """

    with pytest.raises(
        Qasm3ConversionError,
        match=r"Dimension mismatch for 'my_arr' in function 'my_function'. "
        r"Expected dimension 0 with size >= 4 but got 2",
    ):
        qasm3_to_qir(qasm_str)


def test_invalid_array_dimensions_formal_arg():
    """Test that passing an array with invalid dimensions raises error."""
    qasm_str = """
    OPENQASM 3;
    include "stdgates.inc";

    def my_function(readonly array[int[32], -1, 2] a) {
        return;
    }
    array[int[32], 1, 2] b;
    my_function(b);
    """
    with pytest.raises(
        Qasm3ConversionError,
        match=r"Invalid dimension size -1 for 'a' in function 'my_function'",
    ):
        qasm3_to_qir(qasm_str)


def test_invalid_array_mutation_for_readonly_arg():
    """Test that mutating an array passed as readonly raises error."""
    qasm_str = """
    OPENQASM 3;
    include "stdgates.inc";

    def my_function(readonly array[int[32], 1, 2] a) {
        a[1][0] = 5;
        return;
    }
    array[int[32], 1, 2] b;
    my_function(b);
    """
    with pytest.raises(
        Qasm3ConversionError,
        match=r"Assignment to readonly variable 'a' not allowed in function call",
    ):
        qasm3_to_qir(qasm_str)
