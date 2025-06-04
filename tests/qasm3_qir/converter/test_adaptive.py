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
Module containing unit tests for adaptive profile QIR validation and compliance.
"""
import pytest

from qbraid_qir.qasm3 import qasm3_to_qir
from tests.qir_utils import (
    check_adaptive_gate_set,
    check_adaptive_profile_compliance,
    check_attributes,
    check_barrier,
    check_conditional_branching,
    check_full_barrier_coverage,
    check_measure_op,
    check_measurement_state_tracking,
    check_no_backward_jumps,
    check_parameter_constants_only,
    check_qubit_reuse_after_measurement,
    check_read_result_calls,
    check_resets,
    check_return_exit_code,
    check_single_qubit_gate_op,
    check_two_qubit_gate_op,
)


def test_basic_adaptive_profile_compliance():
    """Test basic adaptive profile requirements are met."""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    
    qubit[2] q;
    bit[2] c;
    
    h q[0];
    c[0] = measure q[0];
    
    if (c[0]) {
        x q[1];
    }
    
    c[1] = measure q[1];
    """

    result = qasm3_to_qir(qasm3_string, profile="adaptive")
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 2, 2)
    check_adaptive_profile_compliance(generated_qir)
    check_measure_op(generated_qir, 2, [0, 1], [0, 1])
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")


def test_conditional_execution_with_if_result():
    """Test conditional execution using if_result function."""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    
    qubit[3] q;
    bit[3] c;
    
    h q[0];
    c[0] = measure q[0];
    
    if (c[0]) {
        x q[1];
        h q[2];
    }
    
    c[1] = measure q[1];
    c[2] = measure q[2];
    """

    result = qasm3_to_qir(qasm3_string, profile="adaptive")
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 3, 3)
    check_conditional_branching(generated_qir, 2)  # if and else branches
    check_measure_op(generated_qir, 3, [0, 1, 2], [0, 1, 2])


def test_qubit_reuse_after_measurement():
    """Test that qubits can be reused after measurement."""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    
    qubit[2] q;
    bit[2] c;
    
    h q[0];
    c[0] = measure q[0];
    
    // Reuse qubit after measurement
    reset q[0];
    x q[0];
    
    c[1] = measure q[0];
    """

    result = qasm3_to_qir(qasm3_string, profile="adaptive")
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 2, 2)
    check_qubit_reuse_after_measurement(generated_qir, [0])
    check_resets(generated_qir, 1, [0])
    check_measure_op(generated_qir, 2, [0, 0], [0, 1])


def test_measurement_state_tracking():
    """Test measurement state tracking functionality."""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    
    qubit[3] q;
    bit[3] c;
    
    h q[0];
    c[0] = measure q[0];
    reset q[0];
    
    h q[1];
    c[1] = measure q[1];
    
    x q[2];
    c[2] = measure q[2];
    """

    result = qasm3_to_qir(qasm3_string, profile="adaptive")
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 3, 3)
    check_measurement_state_tracking(generated_qir, 4)  # 3 measurements + 1 reset
    check_resets(generated_qir, 1, [0])


def test_register_grouped_output():
    """Test that output recording preserves register structure."""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    
    qubit[2] q1;
    qubit[3] q2;
    bit[2] c1;
    bit[3] c2;
    
    h q1[0];
    h q2[0];
    
    c1[0] = measure q1[0];
    c1[1] = measure q1[1];
    c2[0] = measure q2[0];
    c2[1] = measure q2[1];
    c2[2] = measure q2[2];
    """

    result = qasm3_to_qir(qasm3_string, profile="adaptive")
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 5, 5)


def test_nested_conditional_execution():
    """Test nested conditional statements."""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    
    qubit[3] q;
    bit[3] c;
    
    h q[0];
    c[0] = measure q[0];
    
    if (c[0]) {
        h q[1];
        c[1] = measure q[1];
        
        if (c[1]) {
            x q[2];
        }
    }
    
    c[2] = measure q[2];
    """

    result = qasm3_to_qir(qasm3_string, profile="adaptive")
    generated_qir = str(result).splitlines()

    check_attributes(generated_qir, 3, 3)
    check_conditional_branching(generated_qir, 4)  # Multiple branches for nested ifs
    check_no_backward_jumps(generated_qir)


def test_adaptive_gate_set_compliance():
    """Test that only adaptive profile supported gates are used."""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    
    qubit[4] q;
    bit[4] c;
    
    h q[0];
    x q[1];
    y q[2];
    z q[3];
    s q[0];
    t q[1];
    cx q[0], q[1];
    cz q[2], q[3];
    
    c[0] = measure q[0];
    c[1] = measure q[1];
    c[2] = measure q[2];
    c[3] = measure q[3];
    """

    result = qasm3_to_qir(qasm3_string, profile="adaptive")
    generated_qir = str(result).splitlines()

    check_adaptive_gate_set(generated_qir)
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")
    check_single_qubit_gate_op(generated_qir, 1, [1], "x")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")


def test_parameterized_gates_constants_only():
    """Test that parameterized gates use constants only."""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    
    qubit[3] q;
    bit[3] c;
    
    rx(pi/2) q[0];
    ry(pi/4) q[1];
    rz(pi) q[2];
    
    c[0] = measure q[0];
    c[1] = measure q[1];
    c[2] = measure q[2];
    """

    result = qasm3_to_qir(qasm3_string, profile="adaptive")
    generated_qir = str(result).splitlines()

    check_parameter_constants_only(generated_qir)
    check_measure_op(generated_qir, 3, [0, 1, 2], [0, 1, 2])


def test_full_barrier_coverage():
    """Test that barriers cover all qubits (no partial barriers)."""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    
    qubit[3] q;
    bit[3] c;
    
    h q[0];
    barrier q;  // Full barrier covering all qubits
    x q[1];
    barrier q;  // Another full barrier
    
    c[0] = measure q[0];
    c[1] = measure q[1];
    c[2] = measure q[2];
    """

    result = qasm3_to_qir(qasm3_string, profile="adaptive")
    generated_qir = str(result).splitlines()

    check_full_barrier_coverage(generated_qir, 3)
    check_barrier(generated_qir, 2)


def test_return_exit_code():
    """Test that return instruction has proper exit code."""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    
    qubit[2] q;
    bit[2] c;
    
    h q[0];
    c[0] = measure q[0];
    c[1] = measure q[1];
    """

    result = qasm3_to_qir(qasm3_string, profile="adaptive")
    generated_qir = str(result).splitlines()

    check_return_exit_code(generated_qir)


def test_complex_adaptive_circuit():
    """Test a complex adaptive circuit with multiple features."""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    
    qubit[4] q;
    bit[4] c;
    
    // Initialize with Hadamard
    h q[0];
    
    // First measurement and conditional
    c[0] = measure q[0];
    if (c[0]) {
        x q[1];
        cx q[1], q[2];
    }
    
    // Reset and reuse qubit
    reset q[0];
    ry(pi/2) q[0];
    
    // Second measurement with nested conditional
    c[1] = measure q[1];
    if (c[1]) {
        h q[2];
        c[2] = measure q[2];
        
        if (c[2]) {
            z q[3];
        }
    }
    
    // Final measurements
    c[3] = measure q[3];
    
    // Barrier before final operations
    barrier q;
    """

    result = qasm3_to_qir(qasm3_string, profile="adaptive")
    generated_qir = str(result).splitlines()

    # Comprehensive checks
    check_attributes(generated_qir, 4, 4)
    check_adaptive_profile_compliance(generated_qir)
    check_qubit_reuse_after_measurement(generated_qir, [0])
    check_conditional_branching(generated_qir, 4)
    check_measurement_state_tracking(generated_qir, 5)  # 4 measurements + 1 reset
    check_no_backward_jumps(generated_qir)
    check_return_exit_code(generated_qir)
    check_full_barrier_coverage(generated_qir, 4)


def test_measurement_based_loops_forbidden():
    """Test that backward jumps (loops) are forbidden."""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    
    qubit[2] q;
    bit[2] c;
    
    h q[0];
    c[0] = measure q[0];
    c[1] = measure q[1];
    """

    result = qasm3_to_qir(qasm3_string, profile="adaptive")
    generated_qir = str(result).splitlines()

    # Should not contain backward jumps
    check_no_backward_jumps(generated_qir)


def test_read_result_functionality():
    """Test read_result function usage for accessing measurement outcomes."""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    
    qubit[2] q;
    bit[2] c;
    
    h q[0];
    c[0] = measure q[0];
    
    // Read result for conditional logic
    if (c[0]) {
        x q[1];
    }
    
    c[1] = measure q[1];
    """

    result = qasm3_to_qir(qasm3_string, profile="adaptive")
    generated_qir = str(result).splitlines()

    check_read_result_calls(generated_qir, 1, [0])
