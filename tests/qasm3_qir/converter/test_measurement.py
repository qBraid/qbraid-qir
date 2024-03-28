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
from tests.qir_utils import check_attributes, check_measure_op


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
        with pytest.raises(Qasm3ConversionError, match=error_message):
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
