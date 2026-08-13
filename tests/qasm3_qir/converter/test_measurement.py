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

from qbraid_qir.qasm3 import qasm3_to_qir
from tests.qir_utils import check_attributes, check_measure_op


# 6. Test measurement operations in different ways
def test_measure():
    qasm3_string = """
    OPENQASM 3;

    qubit[2] q1;
    qubit[5] q2;
    qubit q3;

    bit[2] c1;
    bit[1] c2;

    // supported
    c1 = measure q1;
    measure q1 -> c1;
    c2[0] = measure q3[0];
    measure q1[:1] -> c1[1];
    measure q2[{0, 1}] -> c1[{1, 0}];

    """

    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 8, 3)
    qubit_list = [0, 1, 0, 1, 7, 0, 2, 3]
    bit_list = [0, 1, 0, 1, 2, 1, 1, 0]

    check_measure_op(generated_qir, 8, qubit_list, bit_list)


def _recorded_results(generated_qir: list[str]) -> list[str]:
    return [line for line in generated_qir if "result_record_output" in line and "call" in line]


def test_no_measurement_records_no_results():
    """A circuit with no measurement must record nothing.

    Recording one result per qubit here produced a module declaring
    required_num_results=0 while reading back two results, and qir-runner
    reported that uninitialised state as a measurement outcome — a Bell state
    submitted from the circuit composer came back as {"01": 1000}.
    """
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";

    qubit[2] q;

    h q[0];
    cx q[0], q[1];
    """

    generated_qir = str(qasm3_to_qir(qasm3_string)).splitlines()
    check_attributes(generated_qir, 2, 0)
    assert _recorded_results(generated_qir) == []


def test_records_only_measured_results():
    """Recording follows the results mz wrote, not the declared bit count.

    Here `c` is declared but never measured and `c0` holds the measurement, so
    the recorded results must be c0's (4-7). Iterating qubits instead recorded
    0-3, reporting the untouched `c` register and discarding the real outcome.
    """
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";

    qubit[4] q;
    bit[4] c;
    bit[4] c0;

    h q;
    measure q -> c0;
    """

    generated_qir = str(qasm3_to_qir(qasm3_string)).splitlines()
    check_attributes(generated_qir, 4, 8)
    recorded = _recorded_results(generated_qir)
    assert len(recorded) == 4
    for index, line in zip([4, 5, 6, 7], recorded):
        assert f"i64 {index} to" in line, f"expected result {index}, got: {line.strip()}"
