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
Module containing unit tests for Cirq to QIR conversion functions.

"""
import cirq
import pytest

from qbraid_qir.cirq.conversions import cirq_to_qir
from qbraid_qir.exceptions import QirConversionError


@pytest.fixture
def cirq_bell() -> cirq.Circuit:
    """Returns a Cirq bell circuit with measurement over two qubits."""
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1), cirq.measure(q0, q1))
    return circuit


@pytest.fixture
def qir_bell() -> str:
    """Returns a QIR bell circuit with measurement over two qubits."""
    raise NotImplementedError


@pytest.mark.skip(reason="Not implemented yet")
def test_convert_bell(cirq_bell, qir_bell):
    """Test converting Cirq bell circuit to QIR."""
    assert cirq_to_qir(cirq_bell) == qir_bell


def test_cirq_to_qir_type_error():
    """Test raising exception for bad input type."""
    with pytest.raises(TypeError):
        cirq_to_qir(None)


def test_cirq_to_qir_conversion_error():
    """Test raising exception for conversion error."""
    circuit = cirq.Circuit()
    with pytest.raises(QirConversionError):
        cirq_to_qir(circuit)
