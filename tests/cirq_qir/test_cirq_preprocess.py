# Copyright (C) 2024 qBraid
#
# This file is part of qbraid-qir
#
# Qbraid-qir is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for qbraid-qir, as per Section 15 of the GPL v3.

"""
Test functions that preprocess Cirq circuits before conversion to QIR.

"""
import cirq
import numpy as np
import pytest

from qbraid_qir.cirq.exceptions import CirqConversionError
from qbraid_qir.cirq.passes import preprocess_circuit

# pylint: disable=redefined-outer-name

def _match_global_phase(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Matches the global phase of two numpy arrays.

    This function aligns the global phases of two matrices by applying a phase shift based
    on the position of the largest entry in one matrix. It computes and adjusts for the
    phase difference at this position, resulting in two phase-aligned matrices. The output,
    (a', b'), indicates that a' == b' is equivalent to a == b * exp(i * t) for some phase t.

    Args:
        a (np.ndarray): The first input matrix.
        b (np.ndarray): The second input matrix.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple of the two matrices `(a', b')`, adjusted for
                                       global phase. If shapes of `a` and `b` do not match or
                                       either is empty, returns copies of the original matrices.
    """
    if a.shape != b.shape or a.size == 0:
        return np.copy(a), np.copy(b)

    k = max(np.ndindex(*a.shape), key=lambda t: abs(b[t]))

    def dephase(v):
        r = np.real(v)
        i = np.imag(v)

        if i == 0:
            return -1 if r < 0 else 1
        if r == 0:
            return 1j if i < 0 else -1j

        return np.exp(-1j * np.arctan2(i, r))

    return a * dephase(a[k]), b * dephase(b[k])


def _assert_allclose_up_to_global_phase(a: np.ndarray, b: np.ndarray, atol: float, **kwargs) -> None:
    """
    Checks if two numpy arrays are equal up to a global phase, within
    a specified tolerance, i.e. if a ~= b * exp(i t) for some t.

    Args:
        a (np.ndarray): The first input array.
        b (np.ndarray): The second input array.
        atol (float): The absolute error tolerance.
        **kwargs: Additional keyword arguments to pass to `np.testing.assert_allclose`.

    Raises:
        AssertionError: The matrices aren't nearly equal up to global phase.

    """
    a, b = _match_global_phase(a, b)
    np.testing.assert_allclose(actual=a, desired=b, atol=atol, **kwargs)


@pytest.fixture
def gridqubit_circuit():
    qubits = [cirq.GridQubit(x, 0) for x in range(4)]
    circuit = cirq.Circuit(cirq.H(q) for q in qubits)
    yield circuit


@pytest.fixture
def namedqubit_circuit():
    qubits = [cirq.NamedQubit(f"q{i}") for i in range(4)]
    circuit = cirq.Circuit(cirq.H(q) for q in qubits)
    yield circuit


def test_convert_gridqubits_to_linequbits(gridqubit_circuit):
    linequbit_circuit = preprocess_circuit(gridqubit_circuit)
    for qubit in linequbit_circuit.all_qubits():
        assert isinstance(qubit, cirq.LineQubit), "Qubit is not a LineQubit"
    _assert_allclose_up_to_global_phase(
        linequbit_circuit.unitary(), gridqubit_circuit.unitary(), atol=1e-6
    ), "Circuits are not equal"


def test_convert_namedqubits_to_linequbits(namedqubit_circuit):
    linequbit_circuit = preprocess_circuit(namedqubit_circuit)
    for qubit in linequbit_circuit.all_qubits():
        assert isinstance(qubit, cirq.LineQubit), "Qubit is not a LineQubit"
    _assert_allclose_up_to_global_phase(
        linequbit_circuit.unitary(), namedqubit_circuit.unitary(), atol=1e-6
    ), "Circuits are not equal"


def test_empty_circuit_conversion():
    circuit = cirq.Circuit()
    converted_circuit = preprocess_circuit(circuit)
    assert len(converted_circuit.all_qubits()) == 0, "Converted empty circuit should have no qubits"


def test_multi_qubit_measurement_error():
    qubits = cirq.LineQubit.range(3)
    circuit = cirq.Circuit()
    ps = cirq.X(qubits[0]) * cirq.Y(qubits[1]) * cirq.X(qubits[2])
    meas_gates = cirq.measure_single_paulistring(ps)
    circuit.append(meas_gates)
    with pytest.raises(CirqConversionError):
        preprocess_circuit(circuit)
