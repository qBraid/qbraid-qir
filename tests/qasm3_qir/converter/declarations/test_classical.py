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
from qbraid_qir.qasm3.exceptions import Qasm3ConversionError
from tests.qasm3_qir.fixtures.variables import ASSIGNMENT_TESTS, DECLARATION_TESTS
from tests.qir_utils import check_attributes, check_single_qubit_rotation_op


# 1. Test scalar declarations in different ways
def test_scalar_declarations():
    """Test scalar declarations in different ways"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    int a;
    uint b;
    int[2] c;
    uint[3] d;
    float[32] f;
    float[64] g;
    bit h;
    bool i;
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 0, 1)


# 2. Test const declarations in different ways
def test_const_declarations():
    """Test const declarations in different ways"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    const int a = 5;
    const uint b = 10;
    const int[2*9] c = 1;
    const uint[3-1] d = 2;
    const bool boolean_var = true;
    const float[32] f = 0.00000023;
    const float[64] g = 2345623454564564564564545456456546456456456.0;

    const int a1 = 5 + a;
    const uint b1 = 10 + b;
    const int[2*9] c1 = 1 + 2*c + a;
    const uint[6-1] d1 = 2 + d;
    const bool boolean_var1 = !boolean_var;
    const float[32] f1 = 0.00000023 + f;
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 0, 0)


# 3. Test non-constant scalar assignments
def test_scalar_assignments():
    """Test scalar assignments in different ways"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    int a = 5;
    uint b;
    int[2*9] c = 1;
    uint[3-1] d = 2;
    float r;
    float[32] f = 0.00000023;
    float[64] g = 23456.023424983573645873465836483645876348564387;
    b = 12;
    r = 12.2;
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 0, 0)


# 4. Scalar value assignment
def test_scalar_value_assignment():
    """Test assigning variable values from other variables"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    int a = 5;
    float[32] r;
    float[32] f = 0.5;
    int b = a;
    r = 0.23;
    qubit q;
    rx(b) q;
    rx(r + f*4) q;
    """

    b = 5.0
    r = 0.23
    f = 0.5
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 1, 0)
    check_single_qubit_rotation_op(generated_qir, 2, [0, 0], [b, r + f * 4], "rx")


def test_scalar_type_casts():
    """Test type casts on scalar variables"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    int[32] a = 5.1;
    float[32] r = 245;
    uint[4] b = -4; // -4 % 16 = 12
    bit bit_var = 0;
    bool f = 0;
    bool g = 1;

    qubit q;
    rx(a) q;
    rx(r) q;
    rx(b) q;
    rx(f) q;
    rx(g) q;
    
    """
    a = 5
    r = 245
    b = 12
    f = 0
    g = 1

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 1, 1)
    check_single_qubit_rotation_op(generated_qir, 5, [0, 0, 0, 0, 0], [a, r, b, f, g], "rx")


def test_array_type_casts():
    """Test type casts on  array variables"""

    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    array[int[32], 3, 2] arr_int = { {1, 2}, {3, 4}, {5, 6.2} };
    array[uint[32], 3, 2] arr_uint = { {1, 2}, {3, 4}, {5, 6.2} };
    array[bool, 3, 2] arr_bool = { {true, false}, {true, false}, {true, 12} };
    array[float[32], 3, 2] arr_float32 = { {1.0, 2.0}, {3.0, 4.0}, {5.0, 6} };

    qubit q;
    rx(arr_int[2][1]) q; // should be 6
    rx(arr_uint[2][1]) q; // should be 6
    rx(arr_bool[2][1]) q; // should be 1 (true)
    rx(arr_float32[2][1]) q; // should be 6.0

    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 1, 0)
    check_single_qubit_rotation_op(generated_qir, 4, [0, 0, 0, 0], [6, 6, 1, 6.0], "rx")


# 5. Array declarations
def test_array_declarations():
    """Test array declarations in different ways"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    array[int[32], 3, 2] arr_int;
    array[uint[32-9], 3, 2] arr_uint;
    array[float[32], 3, 2] arr_float32;
    array[float[64], 3, 2] arr_float64;
    array[bool, 3, 2] arr_bool;
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 0, 0)


# 6. Array assignments
def test_array_assignments():
    """Test array assignments"""

    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";

    array[int[32], 3, 2] arr_int;
    array[uint[32], 3, 2] arr_uint;
    array[float[32], 3, 2] arr_float32;
    array[float[64], 3, 2] arr_float64;
    array[bool, 3, 2] arr_bool;

    int a = 2;
    uint b = 3;
    float[32] c = 4.5;
    float[64] d = 6.7;
    bool f = true;

    arr_int[0][1] = a*a;
    arr_int[0,1] = a*a;

    arr_uint[0][1] = b*b;
    arr_uint[0,1] = b*b;

    arr_float32[0][1] = c*c;
    arr_float32[0,1] = c*c;
    
    arr_float64[0][1] = d*d;
    arr_float64[0,1] = d*d;

    arr_bool[0][1] = f;
    arr_bool[0,1] = f;

    qubit q;
    rx(arr_int[0,1]) q;
    rx(arr_uint[0][1]) q;
    rx(arr_float32[0,1]) q;
    rx(arr_float64[0][1]) q;
    rx(arr_bool[0,1]) q;
    """

    a = 2
    b = 3
    c = 4.5
    d = 6.7
    f = True
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 1, 0)
    check_single_qubit_rotation_op(
        generated_qir, 5, [0, 0, 0, 0, 0], [a * a, b * b, c * c, d * d, f], "rx"
    )


# 7. Test expressions which involves arrays
def test_array_expressions():
    """Test array expressions"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";

    array[int[32], 3, 2] arr_int;
    array[uint[32], 3, 2] arr_uint;
    array[float[32], 3, 2] arr_float32;
    array[float[64], 3, 2] arr_float64;
    array[bool, 3, 2] arr_bool;

    int a = 2;
    uint b = 3;
    float[32] c = 4.5;
    float[64] d = 6.7;
    bool f = true;

    arr_int[0][1] = a*a;
    arr_uint[0][1] = b*b;
    arr_float32[0][1] = c*c;
    arr_float64[0][1] = d*d;

    qubit q;
    rx(arr_int[0][1] + arr_uint[0][1]) q;
    rx(arr_float32[0][1] + arr_float64[0][1]) q;
    """

    a = 2
    b = 3
    c = 4.5
    d = 6.7
    f = True
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 1, 0)
    check_single_qubit_rotation_op(generated_qir, 2, [0, 0], [a * a + b * b, c * c + d * d], "rx")


def test_array_initializations():
    """Test array initializations"""

    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";

    array[int[32], 3, 2] arr_int = { {1, 2}, {3, 4}, {5, 6} };
    array[uint[32], 3, 2] arr_uint = { {1, 2}, {3, 4}, {5, 6} };
    array[float[32], 3, 2] arr_float32 = { {1.0, 2.0}, {3.0, 4.0}, {5.0, 6.0} };
    array[float[64], 3, 2] arr_float64 = { {1.0, 2.0}, {3.0, 4.0}, {5.0, 6.0} };
    array[bool, 3, 2] arr_bool = { {true, false}, {true, false}, {true, false} };

    qubit q;
    rx(arr_int[0][1]) q;
    rx(arr_uint[0][1]) q;
    rx(arr_float32[0][1]) q;
    rx(arr_float64[0][1]) q;
    rx(arr_bool[0][1]) q;
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 1, 0)
    check_single_qubit_rotation_op(generated_qir, 5, [0, 0, 0, 0, 0], [2, 2, 2.0, 2.0, 0], "rx")


@pytest.mark.parametrize("test_name", DECLARATION_TESTS.keys())
def test_incorrect_declarations(test_name):
    qasm_input, error_message = DECLARATION_TESTS[test_name]
    with pytest.raises(Qasm3ConversionError, match=error_message):
        _ = qasm3_to_qir(qasm_input)


@pytest.mark.parametrize("test_name", ASSIGNMENT_TESTS.keys())
def test_incorrect_assignments(test_name):
    qasm_input, error_message = ASSIGNMENT_TESTS[test_name]
    with pytest.raises(Qasm3ConversionError, match=error_message):
        _ = qasm3_to_qir(qasm_input)
