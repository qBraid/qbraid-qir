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
Test functions for preprocessing Cirq circuits before conversion to QIR.
"""

# pylint: disable=duplicate-code

import cirq
import numpy as np
from qbraid.interface import circuits_allclose

from qbraid_qir.cirq.passes import preprocess_circuit


def test_only_supported_gates():
    """Test that circuits with only supported gates pass through correctly."""
    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.H(qubits[0]), cirq.CNOT(qubits[0], qubits[1]))

    preprocessed_circuit = preprocess_circuit(circuit)

    # Circuit should be equivalent
    assert circuits_allclose(preprocessed_circuit, circuit)

    # Check that all gates are in the target gateset
    for op in preprocessed_circuit.all_operations():
        gate = op.gate
        assert isinstance(
            gate,
            (
                cirq.IdentityGate,
                cirq.HPowGate,
                cirq.XPowGate,
                cirq.YPowGate,
                cirq.ZPowGate,
                cirq.SwapPowGate,
                cirq.CNotPowGate,
                cirq.CZPowGate,
                cirq.CCXPowGate,
                cirq.ResetChannel,
                cirq.MeasurementGate,
                cirq.PauliMeasurementGate,
            ),
        )


def test_contains_unsupported_gates():
    """Test that unsupported gates are decomposed into supported gates."""
    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.ops.ISwapPowGate(exponent=1.0).on(*qubits),
    )

    preprocessed_circuit = preprocess_circuit(circuit)

    # Circuit should not be the same (it was decomposed)
    assert preprocessed_circuit != circuit

    # But should be functionally equivalent
    assert circuits_allclose(preprocessed_circuit, circuit)

    # Should not contain ISwapPowGate anymore
    for op in preprocessed_circuit.all_operations():
        assert not isinstance(op.gate, cirq.ISwapPowGate)


def test_empty_circuit():
    """Test that empty circuits are handled correctly."""
    circuit = cirq.Circuit()

    preprocessed_circuit = preprocess_circuit(circuit)

    assert len(preprocessed_circuit) == 0
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_custom_gate_decomposition():
    """Test that custom gates are decomposed through their _decompose_ method."""

    class CustomGate(cirq.Gate):  # pylint: disable=abstract-method
        def _num_qubits_(self):
            return 1

        def _decompose_(self, qubits):
            yield cirq.X(qubits[0])

    custom_gate = CustomGate()
    qubit = cirq.LineQubit(0)
    circuit = cirq.Circuit(custom_gate.on(qubit))

    preprocessed_circuit = preprocess_circuit(circuit)

    # Circuit should be decomposed
    assert preprocessed_circuit != circuit

    # Should not contain CustomGate anymore
    assert not any(isinstance(op.gate, CustomGate) for op in preprocessed_circuit.all_operations())

    # Should be functionally equivalent
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_nested_custom_gates():
    """Test that nested custom gates are fully decomposed."""

    class InnerCustomGate(cirq.Gate):  # pylint: disable=abstract-method
        def _num_qubits_(self):
            return 1

        def _decompose_(self, qubits):
            yield cirq.X(qubits[0])

    class OuterCustomGate(cirq.Gate):  # pylint: disable=abstract-method
        def _num_qubits_(self):
            return 1

        def _decompose_(self, qubits):
            yield InnerCustomGate()(qubits[0])

    outer_gate = OuterCustomGate()
    qubit = cirq.LineQubit(0)
    circuit = cirq.Circuit(outer_gate.on(qubit))

    preprocessed_circuit = preprocess_circuit(circuit)

    # Circuit should be decomposed
    assert preprocessed_circuit != circuit

    # Should not contain either custom gate
    assert not any(
        isinstance(op.gate, (OuterCustomGate, InnerCustomGate))
        for op in preprocessed_circuit.all_operations()
    )

    # Should be functionally equivalent
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_toffoli_gate():
    """Test that TOFFOLI (CCX) gates are preserved."""
    qubits = cirq.LineQubit.range(3)
    circuit = cirq.Circuit(cirq.TOFFOLI(*qubits))

    preprocessed_circuit = preprocess_circuit(circuit)

    # Should contain a CCXPowGate (TOFFOLI)
    has_toffoli = any(
        isinstance(op.gate, cirq.CCXPowGate) for op in preprocessed_circuit.all_operations()
    )
    assert has_toffoli

    # Should be functionally equivalent
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_rotation_gates_with_rads_attribute():
    """Test that rotation gates get _rads attribute added."""
    qubit = cirq.LineQubit(0)
    circuit = cirq.Circuit(
        cirq.rx(np.pi / 4)(qubit),
        cirq.ry(np.pi / 3)(qubit),
        cirq.rz(np.pi / 2)(qubit),
    )

    preprocessed_circuit = preprocess_circuit(circuit)

    # Check that rotation gates have _rads attribute
    for op in preprocessed_circuit.all_operations():
        if isinstance(op.gate, (cirq.XPowGate, cirq.YPowGate, cirq.ZPowGate)):
            assert hasattr(op.gate, "_rads")
            # Verify _rads is calculated correctly (exponent * pi)
            expected_rads = float(op.gate.exponent * np.pi)
            assert np.isclose(op.gate._rads, expected_rads)


def test_measurement_gates():
    """Test that measurement gates are preserved."""
    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.H(qubits[0]), cirq.CNOT(qubits[0], qubits[1]), cirq.measure(*qubits, key="result")
    )

    preprocessed_circuit = preprocess_circuit(circuit)

    # Should contain a MeasurementGate
    has_measurement = any(
        isinstance(op.gate, cirq.MeasurementGate) for op in preprocessed_circuit.all_operations()
    )
    assert has_measurement


def test_conditionally_controlled_operations():
    """Test that classically controlled operations are handled specially."""
    qubit = cirq.LineQubit(0)
    circuit = cirq.Circuit(cirq.measure(qubit, key="m"), cirq.X(qubit).with_classical_controls("m"))

    # Should not raise an error
    preprocessed_circuit = preprocess_circuit(circuit)

    # Should still contain the ClassicallyControlledOperation
    has_conditional = any(
        isinstance(op, cirq.ClassicallyControlledOperation)
        for op in preprocessed_circuit.all_operations()
    )
    assert has_conditional


def test_mixed_gate_types():
    """Test a circuit with various gate types."""
    qubits = cirq.LineQubit.range(3)
    circuit = cirq.Circuit(
        cirq.H(qubits[0]),
        cirq.rx(np.pi / 4)(qubits[1]),
        cirq.CNOT(qubits[0], qubits[1]),
        cirq.CZ(qubits[1], qubits[2]),
        cirq.SWAP(qubits[0], qubits[2]),
        cirq.measure(*qubits, key="result"),
    )

    preprocessed_circuit = preprocess_circuit(circuit)

    # Should be functionally equivalent
    assert circuits_allclose(preprocessed_circuit, circuit)

    # All operations should be in the target gateset
    for op in preprocessed_circuit.all_operations():
        if hasattr(op, "gate"):
            gate = op.gate
            assert isinstance(
                gate,
                (
                    cirq.IdentityGate,
                    cirq.HPowGate,
                    cirq.XPowGate,
                    cirq.YPowGate,
                    cirq.ZPowGate,
                    cirq.SwapPowGate,
                    cirq.CNotPowGate,
                    cirq.CZPowGate,
                    cirq.MeasurementGate,
                ),
            )


def test_circuit_with_reset():
    """Test that reset operations are preserved."""
    qubit = cirq.LineQubit(0)
    circuit = cirq.Circuit(cirq.X(qubit), cirq.reset(qubit), cirq.H(qubit))

    preprocessed_circuit = preprocess_circuit(circuit)

    # Should contain a ResetChannel
    has_reset = any(
        isinstance(op.gate, cirq.ResetChannel) for op in preprocessed_circuit.all_operations()
    )
    assert has_reset
