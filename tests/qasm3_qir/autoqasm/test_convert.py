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
Tests the convert module of autoqasm to qir

"""

import re
from typing import TYPE_CHECKING

import pytest

pytest.importorskip("autoqasm")

import autoqasm as aq
import autoqasm.instructions as ins
import numpy as np
from pyqir import Module
from qbraid.passes.qasm.compat import add_stdgates_include, insert_gate_def

from qbraid_qir.qasm3 import qasm3_to_qir

if TYPE_CHECKING:
    from autoqasm.program import MainProgram


def _process_qasm(qasm: str) -> str:
    """
    Convert OpenQASM 3 string to a format that
    will be accepted by the qbraid-qir converter.

    Args:
        qasm (str): The input QASM string to process.

    Returns:
        The processed QASM string.

    """
    # Regular expression to remove initialization to zeros
    pattern = r'(bit\[\d+\] +__bit_\d+__)\s+=\s+"[0]+"(;)'

    # Transform each line, removing zero initializations
    transformed_lines = [re.sub(pattern, r"\1\2", line) for line in qasm.split("\n")]

    # Rejoin the transformed lines back into a single string
    qasm = "\n".join(transformed_lines)

    # Replace specific keywords with comments in a single step to avoid multiple replacements
    qasm = re.sub(r"^(output|return_value =)", r"// \1", qasm, flags=re.MULTILINE)

    # Insert and replace various gate definitions for compatibility
    qasm = add_stdgates_include(qasm)
    qasm = insert_gate_def(qasm, "iswap")
    qasm = insert_gate_def(qasm, "sxdg")
    return qasm


def autoqasm_to_qir(program: "MainProgram", **kwargs) -> "Module":
    """
    Converts an AutoQASM program to a PyQIR module.

    Args:
        program (cirq.Circuit): The Cirq circuit to convert.

    Returns:
        The QIR ``pyqir.Module`` representation of the input AutoQASM program.

    """
    qasm = program.build().to_ir()

    processed_qasm = _process_qasm(qasm)

    return qasm3_to_qir(processed_qasm, **kwargs)


@aq.main(num_qubits=1)
def one_qubit_gates():
    ins.h(0)
    ins.s(0)
    ins.si(0)
    ins.t(0)
    ins.ti(0)
    ins.x(0)
    ins.y(0)
    ins.z(0)
    ins.v(0)
    ins.vi(0)
    # return ins.measure() # Reference : https://github.com/qBraid/pyqasm/issues/15


@aq.main(num_qubits=1)
def one_qubit_rotation_gates():
    ins.rx(0, np.pi / 2)
    ins.ry(0, np.pi / 2)
    ins.rz(0, np.pi / 2)
    ins.u(0, np.pi / 2, np.pi, np.pi / 2)


@aq.main(num_qubits=2)
def ising_coupling_gates():
    ins.xx(0, 1, np.pi / 2)
    ins.xy(0, 1, np.pi / 2)
    ins.yy(0, 1, np.pi / 2)
    ins.zz(0, 1, np.pi / 2)


@aq.main(num_qubits=2)
def controlled_two_qubit_gates():
    ins.cnot(0, 1)
    ins.cv(0, 1)
    ins.cy(0, 1)
    ins.cz(0, 1)


@aq.main(num_qubits=3)
def swap_gates():
    ins.swap(0, 1)
    ins.iswap(0, 1)
    ins.pswap(0, 1, np.pi / 2)


@aq.main(num_qubits=3)
def controlled_three_qubit_gates():
    ins.ccnot(0, 1, 2)
    ins.cswap(0, 1, 2)


@aq.main(num_qubits=1)
def phase_shift_gates():
    ins.phaseshift(0, np.pi / 2)
    ins.prx(0, np.pi / 2, np.pi / 2)


@aq.main(num_qubits=2)
def controlled_phase_shift_gates():
    ins.cphaseshift(0, 1, np.pi / 2)
    ins.cphaseshift00(0, 1, np.pi / 2)
    ins.cphaseshift01(0, 1, np.pi / 2)
    ins.cphaseshift10(0, 1, np.pi / 2)


@aq.main
def global_phase_gates():
    ins.gphase(np.pi / 2)


@aq.main(num_qubits=2)
def ionq_gates():
    ins.gpi(0, np.pi / 2)
    ins.gpi2(0, np.pi / 2)
    ins.ms(0, 1, 0, np.pi / 2, np.pi)


@aq.main(num_qubits=3)
def reset_example():
    ins.x(0)
    ins.reset(0)
    ins.h(1)
    ins.cnot(1, 2)


@aq.main(num_qubits=3)
def miscellaneous_gates():
    ins.ecr(0, 1)


def test_one_qubit_gates():
    """Test converting one qubti gate autoqasm to qir."""
    qasm = autoqasm_to_qir(one_qubit_gates)
    assert isinstance(qasm, Module)


def test_one_qubit_rotation_gates():
    """Test converting one qubit rotation gate autoqasm to qir."""
    qasm = autoqasm_to_qir(one_qubit_rotation_gates)
    assert isinstance(qasm, Module)


def test_ising_coupling_gates():
    """Test converting ising coupling gate autoqasm to qir."""
    qasm = autoqasm_to_qir(ising_coupling_gates)
    assert isinstance(qasm, Module)


def test_controlled_two_qubit_gates():
    """Test converting controlled two qubit gate autoqasm to qir."""
    qasm = autoqasm_to_qir(controlled_two_qubit_gates)
    assert isinstance(qasm, Module)


def test_swap_gates():
    """Test converting swap gate autoqasm to qir."""
    qasm = autoqasm_to_qir(swap_gates)
    assert isinstance(qasm, Module)


def test_controlled_three_qubit_gates():
    """Test converting controlled three qubit gate autoqasm to qir."""
    qasm = autoqasm_to_qir(controlled_three_qubit_gates)
    assert isinstance(qasm, Module)


def test_phase_shift_gates():
    """Test converting phase shift gate autoqasm to qir."""
    qasm = autoqasm_to_qir(phase_shift_gates)
    assert isinstance(qasm, Module)


def test_controlled_phase_shift_gates():
    """Test converting controlled phase shift gate autoqasm to qir."""
    qasm = autoqasm_to_qir(controlled_phase_shift_gates)
    assert isinstance(qasm, Module)


def test_ionq_gates():
    """Test converting ionq gate autoqasm to qir."""
    qasm = autoqasm_to_qir(ionq_gates)
    assert isinstance(qasm, Module)


def test_reset():
    """Test autoqasm reset usage to qir."""
    qasm = autoqasm_to_qir(reset_example)
    assert isinstance(qasm, Module)


def test_miscellaneous_gates():
    """Test converting miscellaneous gate autoqasm to qir."""
    qasm = autoqasm_to_qir(miscellaneous_gates)
    assert isinstance(qasm, Module)


@aq.subroutine
def bell_subroutine(q0: int, q1: int):
    ins.h(q0)
    ins.cnot(q0, q1)


@aq.main(num_qubits=4)
def two_bell():
    bell_subroutine(0, 1)
    bell_subroutine(2, 3)


@pytest.mark.skipif(True, reason="Subroutines are not currently supported.")
def test_subroutine_usage():
    """Test autoqasm subroutine usage to qir."""
    qasm = autoqasm_to_qir(two_bell)
    assert isinstance(qasm, Module)


@aq.gate
def my_gate(q0: aq.Qubit, q1: aq.Qubit):
    ins.h(q0)
    ins.cnot(q0, q1)


@aq.main(num_qubits=2)
def bell_gate():
    my_gate(0, 1)


def test_gate_usage():
    """Test autoqasm gate usage to qir."""
    qasm = autoqasm_to_qir(bell_gate)
    assert isinstance(qasm, Module)


@aq.main
def bell_state():
    with aq.verbatim():
        ins.h("$0")
        ins.cnot("$0", "$1")
    return ins.measure(["$0", "$1"])


@pytest.mark.skipif(True, reason="Pragma is not currently supported.")
def test_verbatim():
    """Test autoqasm verbatim usage to qir."""
    qasm = autoqasm_to_qir(bell_state)
    assert isinstance(qasm, Module)


@aq.main
def my_program():
    ins.h(0)
    ins.cnot(0, 1)
    result = ins.measure([0, 1])
    return result


@pytest.mark.skipif(True, reason="Measurement variable assignment is not currently supported.")
def test_measurement_variable():
    """Test autoqasm measurement variable assignment to qir."""
    qasm = autoqasm_to_qir(my_program)
    assert isinstance(qasm, Module)
