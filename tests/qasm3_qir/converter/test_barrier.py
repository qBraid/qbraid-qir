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

from qbraid_qir.qasm3 import Qasm3ConversionError, qasm3_to_qir
from tests.qir_utils import check_attributes, check_barrier


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
    subset = """
    OPENQASM 3;

    qubit[3] q1;

    barrier q1[:2];
    """
    with pytest.raises(
        NotImplementedError, match="Barrier operation on a qubit subset is not supported in pyqir"
    ):
        _ = qasm3_to_qir(subset)

    undeclared = """
    OPENQASM 3;

    qubit[3] q1;

    barrier q2;
    """

    with pytest.raises(Qasm3ConversionError, match=r"Missing register declaration for q2 .*"):
        _ = qasm3_to_qir(undeclared)

    out_of_bounds = """
    OPENQASM 3;

    qubit[2] q1;

    barrier q1[:4];
    """

    with pytest.raises(
        Qasm3ConversionError, match="Index 3 out of range for register of size 2 in qubit"
    ):
        _ = qasm3_to_qir(out_of_bounds)

    duplicate = """
    OPENQASM 3;

    qubit[2] q1;

    barrier q1, q1;
    """

    with pytest.raises(Qasm3ConversionError, match=r"Duplicate qubit .*argument"):
        _ = qasm3_to_qir(duplicate)
