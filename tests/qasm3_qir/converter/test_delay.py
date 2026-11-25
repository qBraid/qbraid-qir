# Copyright 2026 qBraid
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

from qbraid_qir.qasm3 import qasm3_to_qir
from tests.qir_utils import get_entry_point_body, measure_call_string, single_op_call_string


# Test qasm3 delay operations produce a NOP in qir
def test_delay():
    qasm3_string = """
    OPENQASM 3.0;
    include "stdgates.inc";

    qubit[1] q;
    bit[1] c;

    x q[0];
    delay[100ns] q[0];
    c[0] = measure q[0];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result)
    entry_body = get_entry_point_body(generated_qir.splitlines())

    qis_calls = [line for line in entry_body if line.startswith("call void @__quantum__qis__")]

    assert qis_calls == [
        single_op_call_string("x", 0),
        measure_call_string("mz", 0, 0),
    ]

    assert "delay" not in generated_qir.lower()
