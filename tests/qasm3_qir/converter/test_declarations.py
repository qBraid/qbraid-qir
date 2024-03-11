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
from tests.qir_utils import check_attributes


# 1. Test qubit declarations in different ways
def test_qubit_declarations():
    """Test qubit declarations in different ways"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit q1;
    qubit[2] q2;
    qreg q3[3];
    qubit[1] q4;
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 7, 0)


# 2. Test clbit declarations in different ways
def test_clbit_declarations():
    """Test clbit declarations in different ways"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    bit c1;
    bit[2] c2;
    creg c3[3];
    bit[1] c4;
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 0, 7)


# 3. Test qubit and clbit declarations in different ways
def test_qubit_clbit_declarations():
    """Test qubit and clbit declarations in different ways"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";

    // qubit declarations
    qubit q1;
    qubit[2] q2;
    qreg q3[3];
    qubit[1] q4;

    // clbit declarations
    bit c1;
    bit[2] c2;
    creg c3[3];
    bit[1] c4;
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 7, 7)
