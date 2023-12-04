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
Module containing PyQIR circuit fixtures for unit tests.

"""
import pytest
from pyqir import BasicQisBuilder, SimpleModule


@pytest.fixture
def pyqir_bell() -> SimpleModule:
    """Returns a QIR bell circuit with measurement over two qubits."""
    bell = SimpleModule("test_qir_bell", num_qubits=2, num_results=2)
    qis = BasicQisBuilder(bell.builder)

    qis.h(bell.qubits[0])
    qis.cx(bell.qubits[0], bell.qubits[1])
    qis.mz(bell.qubits[0], bell.results[0])
    qis.mz(bell.qubits[1], bell.results[1])

    return bell
