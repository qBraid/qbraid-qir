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
Module containing unit tests for QASM3 to QIR conversion functions.

"""

import os
from pathlib import Path

import pyqir

from qbraid_qir.qasm3 import qasm3_to_qir
from tests.qir_utils import check_attributes, get_entry_point_body

RESOURCES_DIR = os.path.join(
    os.path.dirname(__file__).removesuffix("converter"), "fixtures/resources"
)


def resources_file(filename: str) -> str:
    return str(os.path.join(RESOURCES_DIR, f"{filename}"))


def compare_reference_ir(generated_bitcode: bytes, file_path: str) -> None:
    module = pyqir.Module.from_bitcode(pyqir.Context(), generated_bitcode, f"{file_path}")
    ir = str(module)
    pyqir_ir_body = get_entry_point_body(ir.splitlines())

    expected = Path(file_path).read_text(encoding="utf-8")
    expected_ir_body = get_entry_point_body(expected.splitlines())
    assert pyqir_ir_body == expected_ir_body


def test_simple_if():
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
        x q[0];
        cx q[0], q[1];    
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
    # simple_file = resources_file("simple_if.ll")
    # compare_reference_ir(result.bitcode, simple_file)
    # SINCE WE RESET THE QUBITS, WE CANNOT COMPARE THE IR AS IT IS DIFFERENT


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
    //BASE PROFILE DOES NOT ALLOW REUSING OF QUBITS AFTER MEASUREMENT, SO WE RESET IT
    reset q[0];
    reset q[1];
    reset q[2];
    reset q[3];

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
    # complex_if = resources_file("complex_if.ll")
    # compare_reference_ir(result.bitcode, complex_if)
    # SINCE WE RESET THE QUBITS, WE CANNOT COMPARE THE IR AS IT IS DIFFERENT
