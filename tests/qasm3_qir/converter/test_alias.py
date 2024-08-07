# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module containing unit tests for converting OpenQASM 3 programs
with alias statements to QIR.

"""

import re

import pytest

from qbraid_qir.qasm3 import Qasm3ConversionError, qasm3_to_qir
from tests.qir_utils import (
    check_attributes,
    check_single_qubit_gate_op,
    check_three_qubit_gate_op,
    check_two_qubit_gate_op,
)

from .test_if import compare_reference_ir, resources_file


def test_alias():
    """Test converting OpenQASM 3 program with openqasm3.ast.AliasStatement."""

    qasm3_alias_program = """
    OPENQASM 3.0;
    include "stdgates.inc";

    qubit[5] q;

    let myqreg0 = q;
    let myqreg1 = q[1];
    let myqreg2 = q[1:];
    let myqreg3 = q[:4];
    let myqreg4 = q[1:4];
    let myqreg5 = q[1:2:4];
    let myqreg6 = q[{0, 1}];

    x myqreg0[0];
    h myqreg1;
    cx myqreg2[0], myqreg2[1];
    cx myqreg3[2], myqreg3[3];
    ccx myqreg4;
    swap myqreg5[0], myqreg5[1];
    cz myqreg6;
    """
    result = qasm3_to_qir(qasm3_alias_program, name="test")
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 5)

    check_single_qubit_gate_op(generated_qir, 1, [0], "x")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_two_qubit_gate_op(generated_qir, 2, [[1, 2], [2, 3]], "cx")
    check_three_qubit_gate_op(generated_qir, 1, [[1, 2, 3]], "ccx")
    check_two_qubit_gate_op(generated_qir, 1, [[1, 3]], "swap")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cz")


def test_alias_update():
    """Test converting OpenQASM 3 program with alias update."""

    qasm3_alias_program = """
    OPENQASM 3.0;
    include "stdgates.inc";

    qubit[4] q;

    let alias = q[1:];
    let alias = q[2:];

    x alias[1];
    """
    result = qasm3_to_qir(qasm3_alias_program, name="test")
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 4)

    check_single_qubit_gate_op(generated_qir, 1, [3], "x")


def test_valid_alias_redefinition():
    """Test converting OpenQASM 3 program with redefined alias in scope."""

    qasm3_alias_program = """
    OPENQASM 3.0;
    include "stdgates.inc";

    qubit[5] q;
    bit[5] c;
    h q;
    measure q -> c;

    if (c[0] == 1) {
        float[32] alias = 4.3;
    }
    // valid alias
    let alias = q[2];
    x alias;
    """
    result = qasm3_to_qir(qasm3_alias_program, name="test")
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 5, 5)
    check_single_qubit_gate_op(generated_qir, 1, [2], "x")


def test_alias_wrong_indexing():
    """Test converting OpenQASM 3 program with wrong alias indexing."""
    with pytest.raises(
        Qasm3ConversionError,
        match=re.escape(
            r"An index set can be specified by a single integer (signed or unsigned), "
            "a comma-separated list of integers contained in braces {a,b,c,…}, or a range"
        ),
    ):
        qasm3_alias_program = """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[5] q;

        let myqreg = q[1,2];

        x myqreg[0];
        """
        _ = qasm3_to_qir(qasm3_alias_program, name="test")


def test_alias_invalid_discrete_indexing():
    """Test converting OpenQASM 3 program with invalid alias discrete indexing."""
    with pytest.raises(
        Qasm3ConversionError,
        match=r"Unsupported discrete set value .*",
    ):
        qasm3_alias_program = """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[5] q;

        let myqreg = q[{0.1}];

        x myqreg[0];
        """
        _ = qasm3_to_qir(qasm3_alias_program, name="test")


def test_invalid_alias_redefinition():
    """Test converting OpenQASM 3 program with redefined alias."""
    with pytest.raises(
        Qasm3ConversionError,
        match=re.escape(r"Re-declaration of variable 'alias'"),
    ):
        qasm3_alias_program = """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[5] q;
        float[32] alias = 4.2;

        let alias = q[2];

        x alias;
        """
        _ = qasm3_to_qir(qasm3_alias_program, name="test")


def test_alias_defined_before():
    """Test converting OpenQASM 3 program with alias defined before the qubit register."""
    with pytest.raises(
        Qasm3ConversionError,
        match=re.escape(r"Qubit register q2 not found for aliasing"),
    ):
        qasm3_alias_program = """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[5] q1;

        let myqreg = q2[1];
        """
        _ = qasm3_to_qir(qasm3_alias_program, name="test")


def test_unsupported_alias():
    """Test converting OpenQASM 3 program with unsupported alias."""
    with pytest.raises(
        Qasm3ConversionError,
        match=r"Unsupported aliasing .*",
    ):
        qasm3_alias_program = """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[5] q;

        let myqreg = q[0] ++ q[1];
        """
        _ = qasm3_to_qir(qasm3_alias_program, name="test")


def test_alias_in_scope_1():
    """Test converting OpenQASM 3 program with alias in scope."""
    qasm = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[4] q;
    bit[4] c;

    h q;
    measure q -> c;
    if(c[0]){
        let alias = q[0:2];
        x alias[0];
        cx alias[0], alias[1];
    }

    if(c[1] == 1){
        cx q[1], q[2];
    }

    if(!c[2]){
        h q[2];
    }
    """
    result = qasm3_to_qir(qasm)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 4, 4)
    simple_file = resources_file("simple_if.ll")
    compare_reference_ir(result.bitcode, simple_file)


def test_alias_in_scope_2():
    """Test converting OpenQASM 3 program with alias in scope."""
    qasm = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[4] q;
    bit[4] c;

    let alias = q[0:2];

    h q;
    measure q -> c;
    if(c[0]){
        x alias[0];
        cx alias[0], alias[1];
    }

    if(c[1] == 1){
        cx alias[1], q[2];
    }

    if(!c[2]){
        h q[2];
    }
    """
    result = qasm3_to_qir(qasm)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 4, 4)
    simple_file = resources_file("simple_if.ll")
    compare_reference_ir(result.bitcode, simple_file)


def test_alias_out_of_scope():
    """Test converting OpenQASM 3 program with alias out of scope."""
    with pytest.raises(
        Qasm3ConversionError,
        match=r"Variable alias not in scope for operation .*",
    ):
        qasm = """
        OPENQASM 3;
        include "stdgates.inc";
        qubit[4] q;
        bit[4] c;

        h q;
        measure q -> c;
        if(c[0]){
            let alias = q[0:2];
            x alias[0];
            cx alias[0], alias[1];
        }

        if(c[1] == 1){
            cx alias[1], q[2];
        }

        if(!c[2]){
            h q[2];
        }
        """
        _ = qasm3_to_qir(qasm)
