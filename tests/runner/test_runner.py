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
from typing import Optional

import cirq
import pytest

from qbraid_qir import dumps
from qbraid_qir.cirq import cirq_to_qir
from qbraid_qir.runner import Result, Simulator


def cirq_sparse(num_qubits: Optional[int] = None) -> cirq.Circuit:
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
        cirq.Circuit: The constructed circuit for benchmarking.
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


@pytest.mark.skip(reason="qir-runner not available via GitHub Actions.")
def test_sparse_simulator():
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
