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
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 6, 0)
    check_resets(generated_qir, expected_resets=3, qubit_list=[0, 2, 5])


def test_incorrect_resets():
    undeclared = """
    OPENQASM 3;
    include "stdgates.inc";

    qubit[3] q1;

    // undeclared register 
    reset q2[0];
    """
    with pytest.raises(Qasm3ConversionError):
        _ = qasm3_to_qir(undeclared)

    index_error = """
    OPENQASM 3;
    include "stdgates.inc";

    qubit[2] q1;

    // out of bounds 
    reset q1[4];
    """
    with pytest.raises(Qasm3ConversionError):
        _ = qasm3_to_qir(index_error)
