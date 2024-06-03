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
from autoqasm.instructions import cnot, h, measure
from pyqir import Module

from qbraid_qir.autoqasm.convert import autoqasm_to_qir


@aq.main
def bell_state():
    h(0)
    cnot(0, 1)
    return measure([0, 1])


def test_bell_autoqasm_to_qir():
    """Test converting bell state autoqasm to qir."""
    qasm = autoqasm_to_qir(bell_state)
    assert isinstance(qasm, Module)
