# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module containing unit tests for converting OpenQASM 3 programs
with alias statements to QIR.

"""


from qbraid_qir.qasm3 import qasm3_to_qir
from tests.qir_utils import (
    check_attributes,
    check_single_qubit_gate_op,
    check_single_qubit_rotation_op,
)


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
                j = 5; // assignment inside scope
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


def test_subroutine_inside_switch():
    """Test that a subroutine inside a switch statement is correctly parsed."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit q, float[32] b) {
        rx(b) q;
        return;
    }

    qubit[2] q;
    int i = 1;
    float[32] r = 3.14;

    switch(i) {
        case 1 {
            my_function(q[0], r);
        }
        default {
            x q;
        }
    }
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 2, 0)
    check_single_qubit_rotation_op(generated_qir, 1, [0], [3.14], "rx")
