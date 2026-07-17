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
Module containing unit tests for QASM3 programs that address physical (hardware)
qubits, e.g. "$0", rather than declaring a qubit register.

Physical qubits are valid OpenQASM 3 and are what Qiskit emits when a circuit is
transpiled against a backend (``qasm3.dumps(transpile(circuit, backend))``). They
carry their index in the identifier itself, so "$3" is hardware qubit 3 and maps
directly onto QIR qubit 3.

"""

import openqasm3.ast as qasm3_ast
import pytest

from qbraid_qir.qasm3 import qasm3_to_qir
from qbraid_qir.qasm3.exceptions import Qasm3ConversionError
from qbraid_qir.qasm3.visitor import QasmQIRVisitor
from tests.qir_utils import (
    check_attributes,
    check_measure_op,
    check_resets,
    check_single_qubit_gate_op,
    check_single_qubit_rotation_op,
    check_two_qubit_gate_op,
)


def test_physical_qubit_gates_and_measurement():
    """A bell pair on physical qubits lowers to QIR addressing qubits 0 and 1."""
    qasm3_string = """
    OPENQASM 3.0;
    include "stdgates.inc";
    bit[2] meas;
    h $0;
    cx $0, $1;
    meas[0] = measure $0;
    meas[1] = measure $1;
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 2, 2)
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_measure_op(generated_qir, 2, [0, 1], [0, 1])


def test_physical_qubit_index_is_preserved():
    """Physical qubit indices are hardware addresses, so "$3" stays qubit 3 and
    the entry point must declare enough qubits to cover the highest index used."""
    qasm3_string = """
    OPENQASM 3.0;
    include "stdgates.inc";
    bit[2] meas;
    h $3;
    cx $3, $7;
    meas[0] = measure $3;
    meas[1] = measure $7;
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()

    # Highest index is 7, so the entry point requires 8 qubits.
    check_attributes(generated_qir, 8, 2)
    check_single_qubit_gate_op(generated_qir, 1, [3], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[3, 7]], "cx")
    check_measure_op(generated_qir, 2, [3, 7], [0, 1])


def test_qiskit_style_transpiled_program():
    """The shape Qiskit emits after transpiling against a backend: physical
    qubits, a barrier, and register-indexed measurements."""
    qasm3_string = """
    OPENQASM 3.0;
    include "stdgates.inc";
    bit[3] meas;
    rz(pi / 2) $0;
    sx $0;
    cz $0, $1;
    cz $1, $2;
    barrier $0, $1, $2;
    meas[0] = measure $0;
    meas[1] = measure $1;
    meas[2] = measure $2;
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 3, 3)
    # pyqir emits pi/2 as its IEEE-754 hex form rather than a decimal literal.
    check_single_qubit_rotation_op(generated_qir, 1, [0], ["0x3FF921FB54442D18"], "rz")
    # QIR has no native "sx", so pyqasm decomposes it to h - s - h, all on qubit 0.
    check_single_qubit_gate_op(generated_qir, 2, [0, 0], "h")
    check_single_qubit_gate_op(generated_qir, 1, [0], "s")
    check_two_qubit_gate_op(generated_qir, 2, [[0, 1], [1, 2]], "cz")
    check_measure_op(generated_qir, 3, [0, 1, 2], [0, 1, 2])


def test_physical_qubit_reset():
    """Reset on a physical qubit targets the same hardware index."""
    qasm3_string = """
    OPENQASM 3.0;
    include "stdgates.inc";
    bit[1] meas;
    h $2;
    reset $2;
    meas[0] = measure $2;
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 3, 1)
    check_single_qubit_gate_op(generated_qir, 1, [2], "h")
    check_resets(generated_qir, 1, [2])
    check_measure_op(generated_qir, 1, [2], [0])


def test_measurement_without_target_raises_conversion_error():
    """'measure q;' parses but has no classical target to record into. It must
    report that, not raise a bare AssertionError with an empty message."""
    qasm3_string = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] q;
    bit[2] c;
    h q[0];
    measure q;
    """
    with pytest.raises(Qasm3ConversionError, match="must be assigned to a classical bit"):
        qasm3_to_qir(qasm3_string)


def test_unsupported_operand_raises_conversion_error():
    """An operand the visitor cannot lower raises a Qasm3ConversionError naming
    the problem, never a bare AssertionError with an empty message."""
    visitor = QasmQIRVisitor()
    operation = qasm3_ast.QuantumGate(
        modifiers=[],
        name=qasm3_ast.Identifier(name="h"),
        arguments=[],
        # Neither an IndexedIdentifier (virtual) nor a "$n" Identifier (physical).
        qubits=[qasm3_ast.Identifier(name="q")],
    )

    with pytest.raises(Qasm3ConversionError, match="Unsupported qubit operand"):
        visitor._get_op_bits(operation)  # pylint: disable=protected-access
