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
import pytest

from qbraid_qir.qasm3 import qasm3_to_qir
from tests.qir_utils import check_attributes, check_barrier, check_single_qubit_gate_op


# Test barrier operations in different ways
def test_barrier():
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";

    qubit[2] q1;
    qubit[5] q2;
    qubit q3;

    bit[2] c;
    bit[1] c2;


    // Only full barrier supported in QIR
    barrier q1, q2, q3;
    barrier q2, q3, q1;
    x q1[0];
    barrier q1[0], q1[1], q2[:], q3[0];

    for int i in [0:1] {
        x q1[i];
    }

    barrier q1, q2[0:5], q3[:];
    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 8, 3)
    check_barrier(generated_qir, expected_barriers=4)
    check_single_qubit_gate_op(generated_qir, 3, [0, 0, 1], "x")


def test_barrier_in_function():
    """Test that a barrier in a function is correctly parsed."""
    qasm_str = """OPENQASM 3;
    include "stdgates.inc";

    def my_function(qubit[4] a) {
        barrier a;
        return;
    }
    qubit[4] q;
    my_function(q);
    """

    result = qasm3_to_qir(qasm_str)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 4, 0)
    check_barrier(generated_qir, 1)


def test_incorrect_barrier():
    subset = """
    OPENQASM 3;

    qubit[3] q1;

    barrier q1[:2];
    """
    with pytest.raises(
        NotImplementedError, match="Barrier operation on a qubit subset is not supported in pyqir"
    ):
        qasm3_to_qir(subset)
