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
Unit tests for qir-runner Python simulator wrapper.

"""
import random
import shutil
from typing import Optional

import cirq
import numpy as np
import pytest

from qbraid_qir import dumps
from qbraid_qir.cirq import cirq_to_qir
from qbraid_qir.runner.result import Result
from qbraid_qir.runner.simulator import Simulator, _is_valid_semantic_version

skip_runner_tests = shutil.which("qir-runner") is None
REASON = "qir-runner executable not available"

# pylint: disable=redefined-outer-name


def _is_uniform_comput_basis(array: np.ndarray) -> bool:
    """
    Check if each measurement (row) in the array represents a uniform computational basis
    state, i.e., for each shot, that qubit measurements are either all |0⟩s or all |1⟩s.

    Args:
        array (np.ndarray): A 2D numpy array where each row represents a measurement shot,
                            and each column represents a qubit's state in that shot.

    Returns:
        bool: True if every measurement is in a uniform computational basis state
              (all |0⟩s or all |1⟩s). False otherwise.

    Raises:
        ValueError: If the given array is not 2D.
    """
    if array.ndim != 2:
        raise ValueError("The input array must be 2D.")

    for shot in array:
        # Check if all qubits in the shot are measured as |0⟩ or all as |1⟩
        if not (np.all(shot == 0) or np.all(shot == 1)):
            return False
    return True


def _sparse_circuit(num_qubits: Optional[int] = None) -> cirq.Circuit:
    """
    Generates a quantum circuit designed to benchmark the performance of a sparse simulator.

    This circuit is structured to maintain a level of sparsity in the system's state vector, making
    it a good candidate for testing sparse quantum simulators. Sparse simulators excel in
    simulating circuits where the state vector remains sparse, i.e., most of its elements are zero
    or can be efficiently represented.

    Args:
        num_qubits (optional, int): The number of qubits to use in the circuit. If not provided,
                                    a random number of qubits between 10 and 20 will be used.

    Returns:
        cirq.Circuit: The constructed circuit for benchmarking
    """
    num_qubits = num_qubits or random.randint(10, 20)
    # Create a circuit
    circuit = cirq.Circuit()

    # Create qubits
    qubits = cirq.LineQubit.range(num_qubits)

    # Apply Hadamard gates to the first half of the qubits
    for qubit in qubits[: num_qubits // 2]:
        circuit.append(cirq.H(qubit))

    # Apply a CNOT ladder
    for i in range(num_qubits - 1):
        circuit.append(cirq.CNOT(qubits[i], qubits[i + 1]))

    # Apply Z gates to randomly selected qubits
    for qubit in random.sample(qubits, k=num_qubits // 2):
        circuit.append(cirq.Z(qubit))

    # Measurement (optional)
    circuit.append(cirq.measure(*qubits, key="result"))

    return circuit


@pytest.fixture
def cirq_sparse():
    """Cirq circuit used for testing."""
    yield _sparse_circuit


@pytest.mark.skipif(skip_runner_tests, reason=REASON)
def test_sparse_simulator(cirq_sparse):
    """Test qir-runner sparse simulator python wrapper(s)."""
    circuit = cirq_sparse()
    num_qubits = len(circuit.all_qubits())

    file_prefix = "sparse_simulator_test"
    module = cirq_to_qir(circuit, name=file_prefix)
    dumps(module)
    simulator = Simulator()

    shots = random.randint(500, 1000)
    result = simulator.run(f"{file_prefix}.bc", shots=shots)
    assert isinstance(result, Result)

    counts = result.measurement_counts()
    probabilities = result.measurement_probabilities()
    assert len(counts) == len(probabilities) == 2
    assert sum(probabilities.values()) == 1.0

    metadata = result.metadata()
    assert metadata["num_shots"] == shots
    assert metadata["num_qubits"] == num_qubits
    assert isinstance(metadata["execution_duration"], float)

    measurements = result.measurements
    assert _is_uniform_comput_basis(measurements)


@pytest.mark.parametrize(
    "version_str, expected",
    [
        ("1.0.0", True),
        ("0.1.2", True),
        ("2.0.0-rc.1", True),
        ("1.0.0-alpha+001", True),
        ("1.2.3+meta-valid", True),
        ("+invalid", False),  # no major, minor or patch version
        ("-invalid", False),  # no major, minor or patch version
        ("1.0.0-", False),  # pre-release info cannot be empty if hyphen is present
        ("1.0.0+", False),  # build metadata cannot be empty if plus is present
        ("1.0.0+meta/valid", False),  # build metadata contains invalid characters
        ("1.0.0-alpha", True),
        ("1.1.2+meta-123", True),
        ("1.1.2+meta.123", True),
    ],
)
def test_is_valid_semantic_version(version_str, expected):
    """Test the _is_valid_semantic_version function used to verify qir-runner setup."""
    assert _is_valid_semantic_version(version_str) == expected
