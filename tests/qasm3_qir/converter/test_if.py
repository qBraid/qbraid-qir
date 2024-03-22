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

from qbraid_qir.qasm3 import qasm3_to_qir
from tests.qir_utils import check_attributes


def test_simple_if():
    qasm = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[4] q;
    bit[4] c;
    h q;
    measure q -> c;
    if(c[0]){
        x q[0];
        cx q[0], q[1];    
    }
    """
    result = qasm3_to_qir(qasm)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 4, 4)
    # todo


def test_complex_if():
    qasm = """
    OPENQASM 3;
    include "stdgates.inc";
    gate custom a, b{
        cx a, b;
        h a;
    }
    qubit[4] q;
    bit[4] c;
    bit[4] c0;

    h q;
    measure q -> c0;
    if(c0[0]){
        x q[0];
        cx q[0], q[1];
        if (c0[1]){
            cx q[1], q[2];
        }
    }
    if (c[0]){
        custom q[2], q[3];
    }
    """
    result = qasm3_to_qir(qasm)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 4, 8)
    # todo


def test_incorrect_if():
    with pytest.raises(ValueError, match=r"Unsupported expression type .*"):
        _ = qasm3_to_qir(
            """
           OPENQASM 3;
           include "stdgates.inc";
           qubit[2] q;
           bit[2] c;

           h q;
           measure q->c;

           if(c == 4){
                cx q;
           }                   
           """
        )

    with pytest.raises(ValueError, match=r"Missing if block .*"):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
           include "stdgates.inc";
           qubit[2] q;
           bit[2] c;

           h q;
           measure q->c;

           if(c[0]){
           }
           """
        )

    with pytest.raises(ValueError, match=r"Missing register declaration for c2 .*"):
        _ = qasm3_to_qir(
            """
            OPENQASM 3;
           include "stdgates.inc";
           qubit[2] q;
           bit[2] c;

           h q;
           measure q->c;

           if(c2[0]){
            cx q;
           }
           """
        )
