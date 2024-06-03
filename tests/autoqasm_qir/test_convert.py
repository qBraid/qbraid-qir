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


@aq.main(num_qubits=3)
def every_operation():
    ins.ccnot(0, 1, 2)
    ins.cnot(0, 1)
    # ins.cphaseshift(0, 1, np.pi / 2)
    # ins.cphaseshift00(0, 1, np.pi / 2)
    # ins.cphaseshift01(0, 1, np.pi / 2)
    # ins.cphaseshift10(0, 1, np.pi / 2)
    # ins.cswap(0, 1, 2)
    # ins.cv(0, 1)
    # ins.cy(0, 1)
    ins.cz(0, 1)
    # ins.ecr(0, 1)
    # ins.gphase(np.pi / 2)
    # ins.gpi(0, np.pi / 2)
    # ins.gpi2(0, np.pi / 2)
    ins.h(0)
    ins.i(0)
    ins.iswap(0, 1)
    # ins.ms(0, 1, 0, np.pi / 2, np.pi)
    # ins.phaseshift(0, np.pi / 2)
    # ins.pswap(0, 1, np.pi / 2)
    ins.rx(1, np.pi / 2)
    ins.ry(0, np.pi)
    ins.rz(0, np.pi / 4)
    ins.s(0)
    ins.si(0)
    ins.swap(0, 1)
    ins.t(0)
    ins.ti(0)
    ins.u(0, np.pi / 2, np.pi, np.pi / 2)
    ins.v(0)
    # ins.vi(0)
    ins.x(0)
    # ins.xx(0, 1, np.pi / 2)
    # ins.xy(0, 1, np.pi / 2)
    ins.y(0)
    # ins.yy(0, 1, np.pi / 2)
    ins.z(0)
    # ins.zz(0, 1, np.pi / 2)
    return ins.measure([0, 1, 2])


def test_bell_autoqasm_to_qir():
    """Test converting bell state autoqasm to qir."""
    qasm = autoqasm_to_qir(every_operation)
    print(qasm)
    assert isinstance(qasm, Module)


@aq.subroutine
def bell(q0: int, q1: int):
    ins.h(q0)
    ins.cnot(q0, q1)


@aq.main(num_qubits=4)
def two_bell():
    bell(0, 1)
    bell(2, 3)


@pytest.mark.skipif(True, reason="Subroutines are not currently supported.")
def test_two_bell_autoqasm_to_qir():
    """Test converting two bell state autoqasm to qir."""
    qasm = autoqasm_to_qir(two_bell)
    assert isinstance(qasm, Module)
