# Copyright (C) 2024 qBraid
#
# This file is part of qbraid-qir
#
# Qbraid-qir is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for qbraid-qir, as per Section 15 of the GPL v3.

"""
Module containing unit tests for QASM3 to QIR conversion functions.

"""

from qbraid_qir.qasm3 import qasm3_to_qir
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
    measure q1[:1] -> c1[1];
    measure q2[{0, 1}] -> c1[{1, 0}];

    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 8, 3)
    qubit_list = [0, 1, 0, 1, 7, 0, 2, 3]
    bit_list = [0, 1, 0, 1, 2, 1, 1, 0]

    check_measure_op(generated_qir, 8, qubit_list, bit_list)
