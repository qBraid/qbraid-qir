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
Module containing unit tests for parsing, unrolling, and
converting OpenQASM3 programs that contain loops.

"""

import pytest

from qbraid_qir.qasm3 import qasm3_to_qir
from qbraid_qir.qasm3.visitor import Qasm3ConversionError

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

%Qubit = type opaque
%Result = type opaque

define void @main() #0 {
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

attributes #0 = { "entry_point" "output_labeling_schema" "qir_profiles"="custom" "required_num_qubits"="4" "required_num_results"="4" }
attributes #1 = { "irreversible" }

!llvm.module.flags = !{!0, !1, !2, !3}

!0 = !{i32 1, !"qir_major_version", i32 1}
!1 = !{i32 7, !"qir_minor_version", i32 0}
!2 = !{i32 1, !"dynamic_qubit_management", i1 false}
!3 = !{i32 1, !"dynamic_result_management", i1 false}
"""


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
    assert str(qir_from_loop) == EXAMPLE_QIR_OUTPUT


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
    assert str(qir_from_loop) == EXAMPLE_QIR_OUTPUT


def test_convert_qasm3_for_loop_unsupported_type():
    """Test correct error when converting a QASM3 program that contains a for loop initialized from
    an unsupported type."""
    with pytest.raises(
        Qasm3ConversionError,
        match=(
            "Unexpected type <class 'openqasm3.ast.BitstringLiteral'>"
            " of set_declaration in loop."
        ),
    ):
        _ = qasm3_to_qir(
            """
            OPENQASM 3.0;
            include "stdgates.inc";

            qubit[4] q;
            bit[4] c;

            h q;
            for bit b in "001" { 
                x q[b];
            } 
            measure q->c;
            """,
            name="test",
        )
