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
from tests.qir_utils import check_attributes


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
    for line in generated_qir:
        print(line)

    check_attributes(generated_qir, 1, 0)


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
        match=r"Expecting array with base type 'int\[8\]' for 'my_arr' in function 'my_function'."
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
        match=r"Expecting array with base type 'int\[8\]' for 'my_arr' in function 'my_function'. "
        r"Literal found in function call for 'my_function'",
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
    array[float[32], 2, 2] arr;
    my_function(q, arr);

    """

    with pytest.raises(
        Qasm3ConversionError,
        match=r"Expecting array with base type 'int\[8\]' for 'my_arr' in function 'my_function'."
        r" Variable 'arr' has type 'array\[float\[32\], 2, 2\]'.",
    ):
        qasm3_to_qir(qasm_str)
