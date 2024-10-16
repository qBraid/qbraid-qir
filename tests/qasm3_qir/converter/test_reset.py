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
from tests.qir_utils import check_attributes, check_resets


# 4. Test reset operations in different ways
def test_reset_operations():
    """Test reset operations in different ways"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";

    // qubit declarations
    qubit q1;
    qubit[2] q2;
    qreg q3[3];

    // reset operations
    reset q1;
    reset q2[1];
    reset q3[2];
    reset q3[:2];
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 6, 0)
    check_resets(generated_qir, expected_resets=5, qubit_list=[0, 2, 5, 3, 4])


def test_reset_inside_function():
    """Test that a qubit reset inside a function is correctly parsed."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit a) {
        reset a;
        return;
    }
    qubit[3] q;
    my_function(q[1]);
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 3, 0)
    check_resets(generated_qir, 1, [1])
