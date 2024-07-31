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

from qbraid_qir.qasm3 import qasm3_to_qir
from qbraid_qir.qasm3.exceptions import Qasm3ConversionError
from tests.qir_utils import check_attributes, check_single_qubit_gate_op


def test_switch():
    """Test converting OpenQASM 3 program with openqasm3.ast.SwitchStatement."""

    qasm3_switch_program = """
    OPENQASM 3.0;
    include "stdgates.inc";
    
    const int i = 5;
    qubit q;

    switch(i) {
    case 1,3,5,7 {
        x q;
    }
    case 2,4,6,8 {
        y q;
    }
    default {
        z q;
    }
    }
    """

    result = qasm3_to_qir(qasm3_switch_program, name="test")
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1)
    check_single_qubit_gate_op(generated_qir, 1, [0], "x")


def test_switch_default():
    """Test converting OpenQASM 3 program with openqasm3.ast.SwitchStatement and default case."""

    qasm3_switch_program = """
    OPENQASM 3.0;
    include "stdgates.inc";
    
    const int i = 10;
    qubit q;

    switch(i) {
    case 1,3,5,7 {
        x q;
    }
    case 2,4,6,8 {
        y q;
    }
    default {
        z q;
    }
    }
    """

    result = qasm3_to_qir(qasm3_switch_program, name="test")
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1)
    check_single_qubit_gate_op(generated_qir, 1, [0], "z")


def test_switch_identifier_case():
    """Test converting OpenQASM 3 program with openqasm3.ast.SwitchStatement and identifier case."""

    qasm3_switch_program = """
    OPENQASM 3.0;
    include "stdgates.inc";
    
    const int i = 4;
    const int j = 4;
    qubit q;

    switch(i) {
    case 6, j {
        x q;
    }
    default {
        z q;
    }
    }
    """

    result = qasm3_to_qir(qasm3_switch_program, name="test")
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1)
    check_single_qubit_gate_op(generated_qir, 1, [0], "x")


def test_switch_const_int():
    """Test converting OpenQASM 3 program switch and constant integer case."""

    qasm3_switch_program = """
    OPENQASM 3.0;
    include "stdgates.inc";
    
    const int i = 4;
    const int j = 5;
    qubit q;

    switch(i) {
    case j-1 {
        x q;
    }
    default {
        z q;
    }
    }
    """

    result = qasm3_to_qir(qasm3_switch_program, name="test")
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1)
    check_single_qubit_gate_op(generated_qir, 1, [0], "x")


def test_switch_duplicate_cases():
    """Test that switch raises error if duplicate values are present in case."""

    with pytest.raises(
        Qasm3ConversionError, match=re.escape("Duplicate case value 4 in switch statement")
    ):
        qasm3_switch_program = """
        OPENQASM 3.0;
        include "stdgates.inc";
        
        const int i = 4;
        qubit q;

        switch(i) {
        case 4, 4 {
            x q;
        }
        default {
            z q;
        }
        }
        """

        qasm3_to_qir(qasm3_switch_program, name="test")


def test_no_case_switch():
    """Test that switch raises error if no case is present."""

    with pytest.raises(
        Qasm3ConversionError, match=re.escape("Switch statement must have at least one case")
    ):
        qasm3_switch_program = """
        OPENQASM 3.0;
        include "stdgates.inc";
        
        const int i = 4;
        qubit q;

        switch(i) {
        default {
            z q;
        }
        }
        """

        qasm3_to_qir(qasm3_switch_program, name="test")


def test_nested_switch():
    """Test that switch works correctly in case of nested switch"""

    qasm3_switch_program = """
    OPENQASM 3.0;
    include "stdgates.inc";
    
    const int i = 1;
    qubit q;

    switch(i) {
    case 1,3,5,7 {
        int j = 4; // definition inside scope
        switch(j) {
        case 1,3,5,7 {
            x q; 
        }
        case 2,4,6,8 {
            y q; // this will be executed
        }
        default {
            z q;
        }
        }
    }
    case 2,4,6,8 {
        y q;
    }
    default {
        z q;
    }
    
    }
    """

    result = qasm3_to_qir(qasm3_switch_program, name="test")
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1, 0)
    check_single_qubit_gate_op(generated_qir, 1, [0], "y")


@pytest.mark.parametrize("invalid_type", ["float", "bool", "bit"])
def test_invalid_scalar_switch_target(invalid_type):
    """Test that switch raises error if target is not an integer."""

    base_invalid_program = (
        """
    OPENQASM 3.0;
    include "stdgates.inc";
    """
        + invalid_type
        + """ i;

    qubit q;

    switch(i) {
        case 4 {
            x q;
        }
        default {
            z q;
        }
    }
    """
    )

    with pytest.raises(
        Qasm3ConversionError, match=re.escape("Switch target i must be of type int")
    ):
        qasm3_switch_program = base_invalid_program
        qasm3_to_qir(qasm3_switch_program, name="test")


@pytest.mark.parametrize("invalid_type", ["float", "bool", "bit"])
def test_invalid_array_switch_target(invalid_type):
    """Test that switch raises error if target is array element and not an integer."""

    base_invalid_program = (
        """
    OPENQASM 3.0;
    include "stdgates.inc";
    array["""
        + invalid_type
        + """, 3, 2] i;

    qubit q;

    switch(i[0][1]) {
        case 4 {
            x q;
        }
        default {
            z q;
        }
    }
    """
    )

    with pytest.raises(
        Qasm3ConversionError, match=re.escape("Switch target i must be of type int")
    ):
        qasm3_switch_program = base_invalid_program
        qasm3_to_qir(qasm3_switch_program, name="test")


@pytest.mark.parametrize(
    "invalid_stmt",
    ["def test1() { int i = 1; }", "array[int[32], 3, 2] arr_int;", "gate test_1() q { h q;}"],
)
def test_unsupported_statements_in_case(invalid_stmt):
    """Test that switch raises error if invalid statements are present in the case block"""

    base_invalid_program = (
        """

    OPENQASM 3.0;
    include "stdgates.inc"; 
    qubit q;
    int i = 4;

    switch(i) {
        case 4 {
            x q;
    """
        + invalid_stmt
        + """
        }
        default {
            z q;
        }
    }
    """
    )
    with pytest.raises(Qasm3ConversionError, match=r"Unsupported statement .*"):
        qasm3_switch_program = base_invalid_program
        qasm3_to_qir(qasm3_switch_program, name="test")


def test_non_int_expression_case():
    """Test that switch raises error if case expression is not an integer."""

    base_invalid_program = """
    OPENQASM 3.0;
    include "stdgates.inc";
    const int i = 4;
    qubit q;

    switch(i) {
        case 4.3, 2 {
            x q;
        }
        default {
            z q;
        }
    }
    """

    with pytest.raises(
        Qasm3ConversionError,
        match=r"Invalid type .* for required type <class 'openqasm3.ast.IntType'>",
    ):
        qasm3_switch_program = base_invalid_program
        qasm3_to_qir(qasm3_switch_program, name="test")


def test_non_int_variable_expression():
    """Test that switch raises error if case expression has a non-int
    variable in expression."""

    base_invalid_program = """
    OPENQASM 3.0;
    include "stdgates.inc";
    const int i = 4;
    const float f = 4.0;
    qubit q;

    switch(i) {
        case f, 2 {
            x q;
        }
        default {
            z q;
        }
    }
    """
    with pytest.raises(
        Qasm3ConversionError,
        match=r"Invalid type of variable .* for required type <class 'openqasm3.ast.IntType'>",
    ):
        qasm3_switch_program = base_invalid_program
        qasm3_to_qir(qasm3_switch_program, name="test")


def test_non_constant_expression_case():
    """Test that switch raises error if case expression is not a constant."""

    base_invalid_program = """
    OPENQASM 3.0;
    include "stdgates.inc";
    int i = 4;
    qubit q;
    int j = 3;
    int k = 2;

    switch(i) {
        case j + k {
            x q;
        }
        default {
            z q;
        }
    }
    """

    with pytest.raises(
        Qasm3ConversionError, match=r"Variable .* is not a constant in given expression"
    ):
        qasm3_switch_program = base_invalid_program
        qasm3_to_qir(qasm3_switch_program, name="test")
