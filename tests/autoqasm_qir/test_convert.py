# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Tests the convert module of autoqasm to qir

"""
import autoqasm as aq
import autoqasm.instructions as ins
import numpy as np
import pytest
from pyqir import Module

from qbraid_qir.autoqasm.convert import autoqasm_to_qir


@aq.main(num_qubits=1)
def one_qubit_gates():
    ins.h(0)
    ins.i(0)
    ins.s(0)
    ins.si(0)
    ins.t(0)
    ins.ti(0)
    ins.x(0)
    ins.y(0)
    ins.z(0)
    ins.v(0)
    ins.vi(0)
    return ins.measure(0)


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


@pytest.mark.skipif(True, reason="pswap not currently supported")
def test_swap_gates():
    """Test converting swap gate autoqasm to qir."""
    qasm = autoqasm_to_qir(swap_gates)
    assert isinstance(qasm, Module)


def test_controlled_three_qubit_gates():
    """Test converting controlled three qubit gate autoqasm to qir."""
    qasm = autoqasm_to_qir(controlled_three_qubit_gates)
    assert isinstance(qasm, Module)

@pytest.mark.skipif(True, reason="phaserx not currently supported")
def test_phase_shift_gates():
    """Test converting phase shift gate autoqasm to qir."""
    qasm = autoqasm_to_qir(phase_shift_gates)
    assert isinstance(qasm, Module)


def test_controlled_phase_shift_gates():
    """Test converting controlled phase shift gate autoqasm to qir."""
    qasm = autoqasm_to_qir(controlled_phase_shift_gates)
    assert isinstance(qasm, Module)


@pytest.mark.skipif(True, reason="not sure if necessary")
def test_global_phase_gates():
    """Test converting global phase gate autoqasm to qir."""
    qasm = autoqasm_to_qir(global_phase_gates)
    assert isinstance(qasm, Module)


@pytest.mark.skipif(True, reason="gpi, gpi2, and ms not currently supported")
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
