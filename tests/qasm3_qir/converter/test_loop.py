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
Module containing unit tests for parsing, unrolling, and
converting OpenQASM3 programs that contain loops.

"""

import pytest

from qbraid_qir._pyqir_compat import pyqir_uses_opaque_pointers
from qbraid_qir.qasm3 import qasm3_to_qir
from tests.qir_utils import (
    check_attributes,
    check_single_qubit_gate_op,
    check_single_qubit_rotation_op,
)

EXAMPLE_WITHOUT_LOOP = """
OPENQASM 3.0;
include "stdgates.inc";

qubit[4] q;
bit[4] c;

h q;

cx q[0], q[1];
cx q[1], q[2];
cx q[2], q[3];

measure q->c;
"""


EXAMPLE_QIR_OUTPUT = """; ModuleID = 'test'
source_filename = "test"

define void @test() #0 {
entry:
  call void @__quantum__rt__initialize(ptr null)
  call void @__quantum__qis__h__body(ptr null)
  call void @__quantum__qis__h__body(ptr inttoptr (i64 1 to ptr))
  call void @__quantum__qis__h__body(ptr inttoptr (i64 2 to ptr))
  call void @__quantum__qis__h__body(ptr inttoptr (i64 3 to ptr))
  call void @__quantum__qis__cnot__body(ptr null, ptr inttoptr (i64 1 to ptr))
  call void @__quantum__qis__cnot__body(ptr inttoptr (i64 1 to ptr), ptr inttoptr (i64 2 to ptr))
  call void @__quantum__qis__cnot__body(ptr inttoptr (i64 2 to ptr), ptr inttoptr (i64 3 to ptr))
  call void @__quantum__qis__mz__body(ptr null, ptr null)
  call void @__quantum__qis__mz__body(ptr inttoptr (i64 1 to ptr), ptr inttoptr (i64 1 to ptr))
  call void @__quantum__qis__mz__body(ptr inttoptr (i64 2 to ptr), ptr inttoptr (i64 2 to ptr))
  call void @__quantum__qis__mz__body(ptr inttoptr (i64 3 to ptr), ptr inttoptr (i64 3 to ptr))
  call void @__quantum__rt__result_record_output(ptr null, ptr null)
  call void @__quantum__rt__result_record_output(ptr inttoptr (i64 1 to ptr), ptr null)
  call void @__quantum__rt__result_record_output(ptr inttoptr (i64 2 to ptr), ptr null)
  call void @__quantum__rt__result_record_output(ptr inttoptr (i64 3 to ptr), ptr null)
  ret void
}

declare void @__quantum__rt__initialize(ptr)

declare void @__quantum__qis__h__body(ptr)

declare void @__quantum__qis__cnot__body(ptr, ptr)

declare void @__quantum__qis__mz__body(ptr, ptr writeonly) #1

declare void @__quantum__rt__result_record_output(ptr, ptr)

attributes #0 = { "entry_point" "output_labeling_schema" "qir_profiles"="base" "required_num_qubits"="4" "required_num_results"="4" }
attributes #1 = { "irreversible" }

!llvm.module.flags = !{!0, !1, !2, !3}

!0 = !{i32 1, !"qir_major_version", i32 1}
!1 = !{i32 7, !"qir_minor_version", i32 0}
!2 = !{i32 1, !"dynamic_qubit_management", i1 false}
!3 = !{i32 1, !"dynamic_result_management", i1 false}
"""


EXAMPLE_QIR_OUTPUT_TYPED = """; ModuleID = 'test'
source_filename = "test"

%Qubit = type opaque
%Result = type opaque

define void @test() #0 {
entry:
  call void @__quantum__rt__initialize(i8* null)
  call void @__quantum__qis__h__body(%Qubit* null)
  call void @__quantum__qis__h__body(%Qubit* inttoptr (i64 1 to %Qubit*))
  call void @__quantum__qis__h__body(%Qubit* inttoptr (i64 2 to %Qubit*))
  call void @__quantum__qis__h__body(%Qubit* inttoptr (i64 3 to %Qubit*))
  call void @__quantum__qis__cnot__body(%Qubit* null, %Qubit* inttoptr (i64 1 to %Qubit*))
  call void @__quantum__qis__cnot__body(%Qubit* inttoptr (i64 1 to %Qubit*), %Qubit* inttoptr (i64 2 to %Qubit*))
  call void @__quantum__qis__cnot__body(%Qubit* inttoptr (i64 2 to %Qubit*), %Qubit* inttoptr (i64 3 to %Qubit*))
  call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  call void @__quantum__qis__mz__body(%Qubit* inttoptr (i64 1 to %Qubit*), %Result* inttoptr (i64 1 to %Result*))
  call void @__quantum__qis__mz__body(%Qubit* inttoptr (i64 2 to %Qubit*), %Result* inttoptr (i64 2 to %Result*))
  call void @__quantum__qis__mz__body(%Qubit* inttoptr (i64 3 to %Qubit*), %Result* inttoptr (i64 3 to %Result*))
  call void @__quantum__rt__result_record_output(%Result* null, i8* null)
  call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 1 to %Result*), i8* null)
  call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 2 to %Result*), i8* null)
  call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 3 to %Result*), i8* null)
  ret void
}

declare void @__quantum__rt__initialize(i8*)

declare void @__quantum__qis__h__body(%Qubit*)

declare void @__quantum__qis__cnot__body(%Qubit*, %Qubit*)

declare void @__quantum__qis__mz__body(%Qubit*, %Result* writeonly) #1

declare void @__quantum__rt__result_record_output(%Result*, i8*)

attributes #0 = { "entry_point" "output_labeling_schema" "qir_profiles"="base" "required_num_qubits"="4" "required_num_results"="4" }
attributes #1 = { "irreversible" }

!llvm.module.flags = !{!0, !1, !2, !3}

!0 = !{i32 1, !"qir_major_version", i32 1}
!1 = !{i32 7, !"qir_minor_version", i32 0}
!2 = !{i32 1, !"dynamic_qubit_management", i1 false}
!3 = !{i32 1, !"dynamic_result_management", i1 false}
"""


def _example_qir_expected():
    return EXAMPLE_QIR_OUTPUT if pyqir_uses_opaque_pointers() else EXAMPLE_QIR_OUTPUT_TYPED


def test_convert_qasm3_for_loop():
    """Test converting a QASM3 program that contains a for loop."""
    qir_expected = qasm3_to_qir(EXAMPLE_WITHOUT_LOOP, name="test")
    qir_from_loop = qasm3_to_qir(
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[4] q;
        bit[4] c;

        h q;
        for int i in [0:2]{ 
            cx q[i], q[i+1];
        } 
        measure q->c;
        """,
        name="test",
    )
    assert str(qir_expected) == str(qir_from_loop)
    assert str(qir_from_loop) == _example_qir_expected()


def test_convert_qasm3_for_loop_shadow():
    """Test for loop where loop variable shadows variable from global scope."""
    qir_expected = qasm3_to_qir(
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[4] q;
        bit[4] c;

        int i = 3;

        h q;
        cx q[0], q[1];
        cx q[1], q[2];
        cx q[2], q[3];
        h q[i];
        measure q->c;
        """,
        name="test",
    )
    qir_from_loop = qasm3_to_qir(
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[4] q;
        bit[4] c;

        int i = 3;

        h q;
        for int i in [0:2]{
            cx q[i], q[i+1];
        }
        h q[i];
        measure q->c;
        """,
        name="test",
    )
    assert str(qir_expected) == str(qir_from_loop)


def test_convert_qasm3_for_loop_enclosing():
    """Test for loop where variable from outer loop is accessed from inside the loop."""
    qir_expected = qasm3_to_qir(
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[4] q;
        bit[4] c;

        int j = 3;

        h q;
        cx q[0], q[1];
        h q[j];
        cx q[1], q[2];
        h q[j];
        cx q[2], q[3];
        h q[j];
        measure q->c;
        """,
        name="test",
    )
    qir_from_loop = qasm3_to_qir(
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[4] q;
        bit[4] c;

        int j = 3;

        h q;
        for int i in [0:2]{
            cx q[i], q[i+1];
            h q[j];
        }
        measure q->c;
        """,
        name="test",
    )
    assert str(qir_expected) == str(qir_from_loop)


def test_convert_qasm3_for_loop_enclosing_modifying():
    """Test for loop where variable from outer loop is modified from inside the loop."""
    qir_expected = qasm3_to_qir(
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[4] q;
        bit[4] c;

        int j = 0;

        h q;
        cx q[0], q[1];
        h q[j];
        j += 1;
        cx q[1], q[2];
        h q[j];
        j += 1;
        cx q[2], q[3];
        h q[j];
        j += 1;

        h q[j];
        measure q->c;
        """,
        name="test",
    )
    qir_from_loop = qasm3_to_qir(
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[4] q;
        bit[4] c;

        int j = 0;

        h q;
        for int i in [0:2]{
            cx q[i], q[i+1];
            h q[j];
            j += 1;
        }
        h q[j];
        measure q->c;
        """,
        name="test",
    )
    assert str(qir_expected) == str(qir_from_loop)


def test_convert_qasm3_for_loop_discrete_set():
    """Test converting a QASM3 program that contains a for loop initialized from a DiscreteSet."""
    qir_expected = qasm3_to_qir(EXAMPLE_WITHOUT_LOOP, name="test")
    qir_from_loop = qasm3_to_qir(
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[4] q;
        bit[4] c;

        h q;
        for int i in {0, 1, 2} { 
            cx q[i], q[i+1];
        } 
        measure q->c;
        """,
        name="test",
    )
    assert str(qir_expected) == str(qir_from_loop)
    assert str(qir_from_loop) == _example_qir_expected()


def test_function_executed_in_loop():
    """Test that a function executed in a loop is correctly parsed."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit q_arg, float[32] b) {
        rx(b) q_arg;
        return;
    }
    qubit[5] q;

    int[32] n = 2;
    float[32] b = 3.14;

    for int i in [0:n] {
        my_function(q[i], i*b);
    }
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 5, 0)
    check_single_qubit_rotation_op(generated_qir, 3, list(range(3)), [0, 3.14, 2 * 3.14], "rx")


def test_loop_inside_function():
    """Test that a function with a loop is correctly parsed."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit[3] q2) {
        for int[32] i in [0:2] {
            h q2[i];
        }
        return;
    }
    qubit[3] q1;
    my_function(q1);
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 3, 0)
    check_single_qubit_gate_op(generated_qir, 3, [0, 1, 2], "h")


def test_function_in_nested_loop():
    """Test that a function executed in a nested loop is correctly parsed."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit q_arg, float[32] b) {
        rx(b) q_arg;
        return;
    }
    qubit[5] q;

    int[32] n = 2;
    float[32] b = 3.14;

    for int i in [0:n] {
        for int j in [0:n] {
            my_function(q[i], j*b);
        }
    }

    my_function(q[0], 2*b);
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 5, 0)
    check_single_qubit_rotation_op(
        generated_qir,
        9,
        [0, 0, 0, 1, 1, 1, 2, 2, 2, 0],
        [0, 3.14, 2 * 3.14, 0, 3.14, 2 * 3.14, 0, 3.14, 2 * 3.14, 2 * 3.14],
        "rx",
    )


@pytest.mark.skip(reason="Not implemented nested functions yet")
def test_loop_in_nested_function_call():
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    def my_function_1(qubit q1, int[32] a){
        for int[32] i in [0:2]{
            rx(a*i) q1;
        }
    }

    def my_function_2(qubit q2, int[32] b){
        my_function_1(q2, b);
    }

    qubit q;
    my_function_2(q, 3);
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 1, 0)
    check_single_qubit_rotation_op(generated_qir, 3, [0, 0, 0], [0, 3, 6], "rx")
