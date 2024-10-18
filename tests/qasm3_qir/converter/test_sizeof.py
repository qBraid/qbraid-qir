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
from tests.qir_utils import check_attributes, check_single_qubit_rotation_op


def test_simple_sizeof():
    """Test sizeof over an array"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";

    array[int[32], 3, 2] my_ints;

    const uint[32] size0 = sizeof(my_ints); // this is 3 and valid 

    int[32] size1 = sizeof(my_ints); // this is 3 

    int[32] size2 = sizeof(my_ints, 1); // this is 2

    int[32] size3 = sizeof(my_ints, 0); // this is 3
    qubit[2] q;

    rx(size0) q[0];
    rx(size1) q[0];
    rx(size2) q[1];
    rx(size3) q[1];
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)

    check_single_qubit_rotation_op(generated_qir, 4, [0, 0, 1, 1], [3, 3, 2, 3], "rx")
