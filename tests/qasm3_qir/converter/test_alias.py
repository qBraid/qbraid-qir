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

import pytest

from qbraid_qir.qasm3 import qasm3_to_qir
from tests.qir_utils import (
    check_attributes,
    check_single_qubit_gate_op,
    check_three_qubit_gate_op,
    check_two_qubit_gate_op,
)

from .test_if import compare_reference_ir, resources_file, version_specific_ll_file


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
    //BASE PROFILE DOES NOT ALLOW REUSING OF QUBITS AFTER MEASUREMENT, SO WE RESET IT
    reset q[2];
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


def test_alias_in_scope_1():
    """Test converting OpenQASM 3 program with alias in scope."""
    qasm = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[4] q;
    bit[4] c;

    h q;
    measure q -> c;

    //BASE PROFILE DOES NOT ALLOW REUSING OF QUBITS AFTER MEASUREMENT, SO WE RESET IT
    reset q[0];
    reset q[1];
    reset q[2];

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
    simple_file = version_specific_ll_file("simple_if")
    compare_reference_ir(result.bitcode, simple_file)


# See reference : https://github.com/qBraid/pyqasm/pull/14
@pytest.mark.skip(reason="Alias parsing bug, enable after fixing")
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
    simple_file = version_specific_ll_file("simple_if")
    compare_reference_ir(result.bitcode, simple_file)
