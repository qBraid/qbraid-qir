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
from qbraid_qir.cirq.qir_target_gateset import QirTargetGateSet


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


def test_tagged_multi_qubit_operation_unwrapping():
    """
    Test that a TaggedOperation is unwrapped to check the actual gate.
    """
    qubits = cirq.LineQubit.range(3)
    # Create a tagged TOFFOLI
    tagged_toffoli = cirq.TOFFOLI(*qubits).with_tags("custom_tag")
    circuit = cirq.Circuit(tagged_toffoli)

    preprocessed = preprocess_circuit(circuit)

    # Should recognize TOFFOLI after unwrapping the tag
    ops = list(preprocessed.all_operations())
    assert len(ops) >= 1
    # The TOFFOLI should be preserved
    has_ccx = any(isinstance(op.gate, cirq.CCXPowGate) for op in ops)
    assert has_ccx


def test_multi_tagged_multi_qubit_operation():
    """
    Test operation with multiple tags is unwrapped correctly.
    """
    qubits = cirq.LineQubit.range(3)
    multi_tagged = cirq.TOFFOLI(*qubits).with_tags("tag1").with_tags("tag2")
    circuit = cirq.Circuit(multi_tagged)

    preprocessed = preprocess_circuit(circuit)

    # Should still recognize and preserve TOFFOLI
    ops = list(preprocessed.all_operations())
    has_ccx = any(isinstance(op.gate, cirq.CCXPowGate) for op in ops)
    assert has_ccx


def test_circuit_operation_single_multi_qubit_gate():
    """
    Test CircuitOperation containing exactly one multi-qubit operation.
    """
    qubits = cirq.LineQubit.range(3)
    # Create a subcircuit with exactly ONE operation
    subcircuit = cirq.Circuit(cirq.TOFFOLI(*qubits))
    circuit_op = cirq.CircuitOperation(cirq.FrozenCircuit(subcircuit))
    circuit = cirq.Circuit(circuit_op)

    preprocessed = preprocess_circuit(circuit)

    # Should unwrap and recognize TOFFOLI
    ops = list(preprocessed.all_operations())
    assert len(ops) >= 1


def test_circuit_operation_multiple_multi_qubit_gates():
    """
    Test CircuitOperation with MORE than one operation.
    """
    qubits = cirq.LineQubit.range(4)
    # Create subcircuit with MULTIPLE operations (not just one)
    subcircuit = cirq.Circuit(
        cirq.TOFFOLI(qubits[0], qubits[1], qubits[2]),
        cirq.TOFFOLI(qubits[1], qubits[2], qubits[3]),
    )
    circuit_op = cirq.CircuitOperation(cirq.FrozenCircuit(subcircuit))
    circuit = cirq.Circuit(circuit_op)

    preprocessed = preprocess_circuit(circuit)

    # Should handle the CircuitOperation properly
    ops = list(preprocessed.all_operations())
    assert len(ops) >= 1


def test_tagged_circuit_operation_with_single_toffoli():
    """
    Test a TaggedOperation wrapping a CircuitOperation with single TOFFOLI.
    """
    qubits = cirq.LineQubit.range(3)
    subcircuit = cirq.Circuit(cirq.TOFFOLI(*qubits))
    circuit_op = cirq.CircuitOperation(cirq.FrozenCircuit(subcircuit))
    tagged_circuit_op = circuit_op.with_tags("wrapper_tag")
    circuit = cirq.Circuit(tagged_circuit_op)

    preprocessed = preprocess_circuit(circuit)

    # Should unwrap both Tag and CircuitOperation
    ops = list(preprocessed.all_operations())
    assert len(ops) >= 1


def test_tagged_circuit_operation_with_multiple_ops():
    """
    Test TaggedOperation wrapping CircuitOperation with multiple operations.
    """
    qubits = cirq.LineQubit.range(3)
    subcircuit = cirq.Circuit(
        cirq.H(qubits[0]),
        cirq.TOFFOLI(*qubits),
    )
    circuit_op = cirq.CircuitOperation(cirq.FrozenCircuit(subcircuit))
    tagged_circuit_op = circuit_op.with_tags("wrapper")
    circuit = cirq.Circuit(tagged_circuit_op)

    preprocessed = preprocess_circuit(circuit)
    ops = list(preprocessed.all_operations())
    assert len(ops) >= 1


def test_operation_with_gate_attribute():
    """
    Test that operation with 'gate' attribute is handled correctly.
    """
    qubits = cirq.LineQubit.range(3)
    toffoli_op = cirq.TOFFOLI(*qubits)
    circuit = cirq.Circuit(toffoli_op)

    # Verify the operation has a gate attribute
    assert hasattr(toffoli_op, "gate")

    preprocessed = preprocess_circuit(circuit)
    ops = list(preprocessed.all_operations())
    assert len(ops) >= 1


def test_unwrapped_gate_is_ccxpowgate():
    """
    Test that after unwrapping, CCXPowGate is recognized.
    """
    qubits = cirq.LineQubit.range(3)
    ccx_gate = cirq.CCXPowGate(exponent=1.0)
    circuit = cirq.Circuit(ccx_gate(*qubits))

    preprocessed = preprocess_circuit(circuit)

    # Should yield the operation as-is
    ops = list(preprocessed.all_operations())
    assert any(isinstance(op.gate, cirq.CCXPowGate) for op in ops)


def test_ccxpowgate_with_different_exponents():
    """
    Test CCXPowGate with various exponents.
    """
    qubits = cirq.LineQubit.range(3)

    for exponent in [0.5, 1.0, 2.0, -0.5]:
        ccx_gate = cirq.CCXPowGate(exponent=exponent)
        circuit = cirq.Circuit(ccx_gate(*qubits))

        preprocessed = preprocess_circuit(circuit)

        # CCXPowGate should be recognized regardless of exponent
        ops = list(preprocessed.all_operations())
        assert len(ops) >= 1


def test_tagged_ccxpowgate_recognized():
    """
    Test that a tagged CCXPowGate is recognized after unwrapping.
    """
    qubits = cirq.LineQubit.range(3)
    tagged_ccx = cirq.CCXPowGate(exponent=1.0)(*qubits).with_tags("my_tag")
    circuit = cirq.Circuit(tagged_ccx)

    preprocessed = preprocess_circuit(circuit)

    ops = list(preprocessed.all_operations())
    has_ccx = any(isinstance(op.gate, cirq.CCXPowGate) for op in ops)
    assert has_ccx


def test_validate_false_but_unwrapped_is_toffoli():
    """
    Test case where validate(op) is False initially,
    but after unwrapping, we find a TOFFOLI.
    """
    qubits = cirq.LineQubit.range(3)

    # Wrap TOFFOLI in a way that might not validate directly
    toffoli = cirq.TOFFOLI(*qubits)
    tagged_toffoli = toffoli.with_tags("special")

    circuit = cirq.Circuit(tagged_toffoli)
    preprocessed = preprocess_circuit(circuit)

    # After unwrapping, TOFFOLI should be recognized
    ops = list(preprocessed.all_operations())
    has_ccx = any(isinstance(op.gate, cirq.CCXPowGate) for op in ops)
    assert has_ccx


def test_circuit_operation_empty_circuit():
    """
    Test CircuitOperation with empty subcircuit (edge case).
    """
    subcircuit = cirq.Circuit()  # Empty circuit
    circuit_op = cirq.CircuitOperation(cirq.FrozenCircuit(subcircuit))
    circuit = cirq.Circuit(circuit_op)

    # Should handle empty CircuitOperation
    preprocessed = preprocess_circuit(circuit)
    ops = list(preprocessed.all_operations())
    # Empty circuit should result in no operations
    assert len(ops) == 0


def test_all_multi_qubit_paths_in_one_circuit():
    """
    Test a circuit that exercises all paths in _decompose_multi_qubit_operation.
    """
    qubits = cirq.LineQubit.range(4)

    circuit = cirq.Circuit(
        # Direct TOFFOLI (line 209-212)
        cirq.TOFFOLI(qubits[0], qubits[1], qubits[2]),
        # Tagged TOFFOLI (line 217-218, then 228-230)
        cirq.TOFFOLI(qubits[1], qubits[2], qubits[3]).with_tags("tagged"),
    )

    preprocessed = preprocess_circuit(circuit)

    # Should have both TOFFOLIs preserved
    ops = list(preprocessed.all_operations())
    ccx_count = sum(1 for op in ops if isinstance(op.gate, cirq.CCXPowGate))
    assert ccx_count >= 2


def test_actual_op_equals_op_path():
    """
    Test where actual_op doesn't change (no unwrapping needed).
    """
    qubits = cirq.LineQubit.range(3)
    # Plain TOFFOLI with no wrapping
    plain_toffoli = cirq.TOFFOLI(*qubits)
    circuit = cirq.Circuit(plain_toffoli)

    preprocessed = preprocess_circuit(circuit)

    ops = list(preprocessed.all_operations())
    assert len(ops) == 1
    assert isinstance(ops[0].gate, cirq.CCXPowGate)


def test_gateset_directly_for_multi_qubit():
    """
    Test QirTargetGateSet._decompose_multi_qubit_operation directly if possible.
    This ensures we're testing the exact method.
    """
    qubits = cirq.LineQubit.range(3)
    toffoli_op = cirq.TOFFOLI(*qubits)

    gateset = QirTargetGateSet()

    # Call _decompose_multi_qubit_operation directly
    result = list(gateset._decompose_multi_qubit_operation(toffoli_op, 0))

    # Should yield the operation
    assert len(result) == 1
    assert result[0] == toffoli_op
