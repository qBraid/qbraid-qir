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

from openqasm3_qir import qasm3_to_qir

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
