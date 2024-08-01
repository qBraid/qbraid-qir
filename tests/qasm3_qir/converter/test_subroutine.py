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

import openqasm3
import pytest

from qbraid_qir.qasm3 import qasm3_to_qir
from qbraid_qir.qasm3.exceptions import Qasm3ConversionError
from tests.qir_utils import check_attributes

# Equivalent OpenQASM 3 programs that apply a Hadamard gate and measure the qubit.
# The first is uses the conventional synatx, while the second contains a subroutine.

qasm3_h_mz = """
OPENQASM 3.0;
include "stdgates.inc";

qreg q[1];
creg c[1];

h q[0];

measure q[0] -> c[0];
"""

qasm3_h_mz_sub = """
OPENQASM 3.0;
include "stdgates.inc";

def apply_h_and_measure(qubit q) -> bit {
    bit result;
    h q;
    measure q -> result;
    return result;
}

qreg q[1];
creg c[1];

c[0] = apply_h_and_measure(q[0]);
"""


@pytest.mark.skip(reason="Subroutines not supported yet")
def test_unroll_qasm3_subroutine():
    """Test unrolling a QASM3 program that contains a subroutine."""
    # pylint: disable-next=unnecessary-lambda-assignment
    _unroll_qam3_sub = lambda x: x  # TODO: Implement this function
    qasm3_unrolled = _unroll_qam3_sub(qasm3_h_mz_sub)
    qasm3_program = openqasm3.parse(qasm3_unrolled)
    qasm3_expected = openqasm3.parse(qasm3_h_mz)
    assert qasm3_program == qasm3_expected


@pytest.mark.skip(reason="Subroutines not supported yet")
def test_convert_qasm3_subroutine():
    """Test converting a QASM3 program that contains a subroutine."""
    qir_expected = qasm3_to_qir(qasm3_h_mz, name="test")
    qir_from_sub = qasm3_to_qir(qasm3_h_mz_sub, name="test")
    assert str(qir_expected) == str(qir_from_sub)


def test_function_declaration():
    """Test that a function declaration is correctly parsed."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit q) -> int[32] {
        h q;
        return;
    }
    qubit q;
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1, 0)


def test_simple_function_call():
    """Test that a simple function call is correctly parsed."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit q) {
        x q;
        return;
    }
    qubit q;
    bit c;
    my_function(q);

    measure q -> c[0];
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1, 1)


def test_undeclared_call():
    """Test that calling an undeclared function raises error."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";
    qubit q;
    my_function(1);
    """

    with pytest.raises(
        Qasm3ConversionError, match=r"Undefined subroutine 'my_function' was called"
    ):
        qasm3_to_qir(qasm_str)


def test_redefinition_raises_error():
    """Test that redefining a function with same name raises error."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit q) -> int[32] {
        h q;
        return;
    }
    def my_function(qubit q) -> float[32] {
        x q;
        return;
    }
    qubit q;
    """

    with pytest.raises(Qasm3ConversionError, match="Redefinition of subroutine 'my_function'"):
        qasm3_to_qir(qasm_str)


def test_incorrect_param_count():
    """Test that calling a subroutine with incorrect number of parameters raises error."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit q, qubit r) {
        h q;
        return;
    }
    qubit q;
    my_function(q);
    """

    with pytest.raises(
        Qasm3ConversionError,
        match="Parameter count mismatch for subroutine"
        " 'my_function'. Expected 2 but got 1 in call",
    ):
        qasm3_to_qir(qasm_str)


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
