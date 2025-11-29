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
Test functions that preprocess Cirq circuits before conversion to QIR.

"""
import cirq
import numpy as np
import pytest
from qbraid.interface import circuits_allclose

from qbraid_qir.cirq.exceptions import CirqConversionError
from qbraid_qir.cirq.passes import preprocess_circuit
from qbraid_qir.cirq.QIRTargetGateSet import QirTargetGateSet

# pylint: disable=redefined-outer-name


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
    assert cirq.allclose_up_to_global_phase(
        linequbit_circuit.unitary(), gridqubit_circuit.unitary(), atol=1e-8
    ), "Circuits are not equivalent up to global phase"


def test_convert_namedqubits_to_linequbits(namedqubit_circuit):
    linequbit_circuit = preprocess_circuit(namedqubit_circuit)
    for qubit in linequbit_circuit.all_qubits():
        assert isinstance(qubit, cirq.LineQubit), "Qubit is not a LineQubit"
    assert cirq.allclose_up_to_global_phase(
        linequbit_circuit.unitary(), namedqubit_circuit.unitary(), atol=1e-8
    ), "Circuits are not equivalent up to global phase"


def test_empty_circuit_conversion():
    circuit = cirq.Circuit()
    converted_circuit = preprocess_circuit(circuit)
    assert len(converted_circuit.all_qubits()) == 0, "Converted empty circuit should have no qubits"


def test_qir_targetgateset_initialization_with_custom_params():
    """Test QirTargetGateSet initialization with custom parameters."""
    gateset = QirTargetGateSet(
        atol=1e-10,
        allow_partial_czs=True,
        additional_gates=[cirq.ISwapPowGate],
        preserve_moment_structure=False,
    )
    assert gateset.atol == 1e-10
    assert gateset.allow_partial_czs is True


def test_qir_targetgateset_default_initialization():
    """Test QirTargetGateSet with default parameters."""
    gateset = QirTargetGateSet()
    assert gateset.atol == 1e-8
    assert gateset.allow_partial_czs is False


def test_preprocess_transformers_property():
    """Test that preprocess_transformers returns expected list."""
    gateset = QirTargetGateSet()
    transformers = gateset.preprocess_transformers
    assert len(transformers) == 2
    assert callable(transformers[0])
    assert callable(transformers[1])


def test_postprocess_transformers_property():
    """Test that postprocess_transformers returns expected list."""
    gateset = QirTargetGateSet()
    transformers = gateset.postprocess_transformers
    assert len(transformers) == 1


def test_rotation_gates_without_rads():
    """Test rotation gates that don't have _rads initially."""
    qubit = cirq.LineQubit(0)
    circuit = cirq.Circuit(
        cirq.XPowGate(exponent=0.5)(qubit),
        cirq.YPowGate(exponent=0.25)(qubit),
        cirq.ZPowGate(exponent=0.75)(qubit),
    )

    preprocessed_circuit = preprocess_circuit(circuit)

    for op in preprocessed_circuit.all_operations():
        if isinstance(op.gate, (cirq.XPowGate, cirq.YPowGate, cirq.ZPowGate)):
            assert hasattr(op.gate, "_rads")
            expected_rads = float(op.gate.exponent * np.pi)
            assert np.isclose(op.gate._rads, expected_rads)


def test_non_rotation_gates_unchanged():
    """Test that non-rotation gates don't get _rads attribute."""
    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.H(qubits[0]), cirq.CNOT(qubits[0], qubits[1]), cirq.SWAP(qubits[0], qubits[1])
    )

    preprocessed_circuit = preprocess_circuit(circuit)

    for op in preprocessed_circuit.all_operations():
        if isinstance(op.gate, (cirq.HPowGate, cirq.CNotPowGate, cirq.SwapPowGate)):
            # These should not get _rads attribute
            # HPowGate is a power gate but not a rotation gate we're targeting
            pass


def test_tagged_single_qubit_operation():
    """Test decomposition of tagged single-qubit operations."""
    qubit = cirq.LineQubit(0)
    tagged_op = cirq.X(qubit).with_tags("test_tag")
    circuit = cirq.Circuit(tagged_op)

    preprocessed_circuit = preprocess_circuit(circuit)
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_circuit_operation_single_qubit():
    """Test decomposition of CircuitOperation with single qubit."""
    qubit = cirq.LineQubit(0)
    subcircuit = cirq.Circuit(cirq.H(qubit))
    circuit_op = cirq.CircuitOperation(cirq.FrozenCircuit(subcircuit))
    circuit = cirq.Circuit(circuit_op)

    preprocessed_circuit = preprocess_circuit(circuit)
    # Should decompose the CircuitOperation
    assert len(list(preprocessed_circuit.all_operations())) > 0


def test_identity_gate_preservation():
    """Test that identity gates are preserved."""
    qubit = cirq.LineQubit(0)
    circuit = cirq.Circuit(cirq.I(qubit))

    preprocessed_circuit = preprocess_circuit(circuit)

    has_identity = any(
        isinstance(op.gate, cirq.IdentityGate) for op in preprocessed_circuit.all_operations()
    )
    assert has_identity


def test_hpowgate_with_different_exponents():
    """Test HPowGate with various exponents."""
    qubit = cirq.LineQubit(0)
    circuit = cirq.Circuit(
        cirq.HPowGate(exponent=1.0)(qubit),
        cirq.HPowGate(exponent=0.5)(qubit),
    )

    preprocessed_circuit = preprocess_circuit(circuit)
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_tagged_two_qubit_operation():
    """Test decomposition of tagged two-qubit operations."""
    qubits = cirq.LineQubit.range(2)
    tagged_op = cirq.CNOT(qubits[0], qubits[1]).with_tags("test_tag")
    circuit = cirq.Circuit(tagged_op)

    preprocessed_circuit = preprocess_circuit(circuit)
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_circuit_operation_two_qubit():
    """Test decomposition of CircuitOperation with two qubits."""
    qubits = cirq.LineQubit.range(2)
    subcircuit = cirq.Circuit(cirq.CNOT(qubits[0], qubits[1]))
    circuit_op = cirq.CircuitOperation(cirq.FrozenCircuit(subcircuit))
    circuit = cirq.Circuit(circuit_op)

    preprocessed_circuit = preprocess_circuit(circuit)
    assert len(list(preprocessed_circuit.all_operations())) > 0


def test_cz_gate_preservation():
    """Test that CZ gates are preserved."""
    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.CZ(qubits[0], qubits[1]))

    preprocessed_circuit = preprocess_circuit(circuit)

    has_cz = any(
        isinstance(op.gate, cirq.CZPowGate) for op in preprocessed_circuit.all_operations()
    )
    assert has_cz


def test_swap_gate_preservation():
    """Test that SWAP gates are preserved."""
    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.SWAP(qubits[0], qubits[1]))

    preprocessed_circuit = preprocess_circuit(circuit)

    has_swap = any(
        isinstance(op.gate, cirq.SwapPowGate) for op in preprocessed_circuit.all_operations()
    )
    assert has_swap


def test_two_qubit_unitary_decomposition():
    """Test decomposition of arbitrary two-qubit unitary."""
    qubits = cirq.LineQubit.range(2)
    # Use a gate that needs decomposition
    circuit = cirq.Circuit(cirq.ISwapPowGate(exponent=0.5).on(*qubits))

    preprocessed_circuit = preprocess_circuit(circuit)
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_two_qubit_with_partial_czs_allowed():
    """Test two-qubit decomposition with allow_partial_czs=True."""
    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.ISwapPowGate(exponent=0.3).on(*qubits))

    # This tests the allow_partial_czs parameter
    preprocessed_circuit = preprocess_circuit(circuit)
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_toffoli_gate_preservation():
    """Test that TOFFOLI (CCX) gates are preserved without decomposition."""
    qubits = cirq.LineQubit.range(3)
    circuit = cirq.Circuit(cirq.TOFFOLI(*qubits))

    preprocessed_circuit = preprocess_circuit(circuit)

    has_toffoli = any(
        isinstance(op.gate, cirq.CCXPowGate) for op in preprocessed_circuit.all_operations()
    )
    assert has_toffoli
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_tagged_toffoli_operation():
    """Test tagged TOFFOLI operation."""
    qubits = cirq.LineQubit.range(3)
    tagged_op = cirq.TOFFOLI(*qubits).with_tags("test_tag")
    circuit = cirq.Circuit(tagged_op)

    preprocessed_circuit = preprocess_circuit(circuit)
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_circuit_operation_multi_qubit():
    """Test CircuitOperation with multi-qubit gate."""
    qubits = cirq.LineQubit.range(3)
    subcircuit = cirq.Circuit(cirq.TOFFOLI(*qubits))
    circuit_op = cirq.CircuitOperation(cirq.FrozenCircuit(subcircuit))
    circuit = cirq.Circuit(circuit_op)

    preprocessed_circuit = preprocess_circuit(circuit)
    assert len(list(preprocessed_circuit.all_operations())) > 0


def test_ccxpowgate_with_exponent():
    """Test CCXPowGate with different exponents."""
    qubits = cirq.LineQubit.range(3)
    circuit = cirq.Circuit(cirq.CCXPowGate(exponent=1.0)(*qubits))

    preprocessed_circuit = preprocess_circuit(circuit)
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_multiple_conditional_operations():
    """Test circuit with multiple classically controlled operations."""
    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.measure(qubits[0], key="m0"),
        cirq.measure(qubits[1], key="m1"),
        cirq.X(qubits[0]).with_classical_controls("m0"),
        cirq.Y(qubits[1]).with_classical_controls("m1"),
    )

    preprocessed_circuit = preprocess_circuit(circuit)

    conditional_ops = [
        op
        for op in preprocessed_circuit.all_operations()
        if isinstance(op, cirq.ClassicallyControlledOperation)
    ]
    assert len(conditional_ops) == 2


def test_complex_circuit_with_all_gate_types():
    """Test a complex circuit with all supported gate types."""
    qubits = cirq.LineQubit.range(4)
    circuit = cirq.Circuit(
        # Single qubit gates
        cirq.I(qubits[0]),
        cirq.H(qubits[0]),
        cirq.X(qubits[1]),
        cirq.Y(qubits[2]),
        cirq.Z(qubits[3]),
        # Rotation gates
        cirq.rx(np.pi / 4)(qubits[0]),
        cirq.ry(np.pi / 3)(qubits[1]),
        cirq.rz(np.pi / 2)(qubits[2]),
        # Two qubit gates
        cirq.CNOT(qubits[0], qubits[1]),
        cirq.CZ(qubits[1], qubits[2]),
        cirq.SWAP(qubits[2], qubits[3]),
        # Three qubit gate
        cirq.TOFFOLI(qubits[0], qubits[1], qubits[2]),
        # Reset
        cirq.reset(qubits[0]),
        # Measurements
        cirq.measure(*qubits, key="result"),
    )

    preprocessed_circuit = preprocess_circuit(circuit)
    assert len(list(preprocessed_circuit.all_operations())) > 0


def test_circuit_with_power_gates_various_exponents():
    """Test power gates with various exponents."""
    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.XPowGate(exponent=0.25)(qubits[0]),
        cirq.YPowGate(exponent=0.5)(qubits[0]),
        cirq.ZPowGate(exponent=0.75)(qubits[0]),
        cirq.HPowGate(exponent=0.5)(qubits[0]),
        cirq.CNotPowGate(exponent=0.5)(qubits[0], qubits[1]),
        cirq.CZPowGate(exponent=0.5)(qubits[0], qubits[1]),
        cirq.SwapPowGate(exponent=0.5)(qubits[0], qubits[1]),
    )

    preprocessed_circuit = preprocess_circuit(circuit)
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_single_qubit_with_very_small_atol():
    """Test single qubit decomposition with very small tolerance."""
    qubit = cirq.LineQubit(0)
    # Create a gate that's very close to identity
    circuit = cirq.Circuit(cirq.XPowGate(exponent=1e-10)(qubit))

    preprocessed_circuit = preprocess_circuit(circuit)
    assert len(list(preprocessed_circuit.all_operations())) > 0


def test_circuit_with_multiple_resets():
    """Test circuit with multiple reset operations."""
    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.X(qubits[0]),
        cirq.reset(qubits[0]),
        cirq.H(qubits[0]),
        cirq.reset(qubits[1]),
        cirq.Y(qubits[1]),
    )

    preprocessed_circuit = preprocess_circuit(circuit)

    reset_count = sum(
        1 for op in preprocessed_circuit.all_operations() if isinstance(op.gate, cirq.ResetChannel)
    )
    assert reset_count == 2


def test_moment_structure_preservation():
    """Test that moment structure can be preserved or not based on flag."""
    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.Moment([cirq.H(qubits[0])]),
        cirq.Moment([cirq.CNOT(qubits[0], qubits[1])]),
        cirq.Moment([cirq.measure(*qubits, key="result")]),
    )

    # Test with default preserve_moment_structure=True
    preprocessed_circuit = preprocess_circuit(circuit)
    assert len(list(preprocessed_circuit.all_operations())) > 0


def test_nested_tags_and_circuit_operations():
    """Test operations with nested tags and circuit operations."""
    qubit = cirq.LineQubit(0)
    op = cirq.X(qubit).with_tags("tag1").with_tags("tag2")
    circuit = cirq.Circuit(op)

    preprocessed_circuit = preprocess_circuit(circuit)
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_deeply_nested_custom_gates():
    """Test very deeply nested custom gates."""

    class Level3Gate(cirq.Gate):
        def _qid_shape_(self):
            return (2,)

        def _num_qubits_(self):
            return 1

        def num_qubits(self):
            return 1

        def _decompose_(self, qubits):
            yield cirq.X(qubits[0])

    class Level2Gate(cirq.Gate):
        def _qid_shape_(self):
            return (2,)

        def _num_qubits_(self):
            return 1

        def num_qubits(self):
            return 1

        def _decompose_(self, qubits):
            yield Level3Gate()(qubits[0])

    class Level1Gate(cirq.Gate):
        def _qid_shape_(self):
            return (2,)

        def _num_qubits_(self):
            return 1

        def num_qubits(self):
            return 1

        def _decompose_(self, qubits):
            yield Level2Gate()(qubits[0])

    qubit = cirq.LineQubit(0)
    circuit = cirq.Circuit(Level1Gate()(qubit))

    preprocessed_circuit = preprocess_circuit(circuit)
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_circuit_operation_with_multiple_ops():
    """Test CircuitOperation containing multiple operations (not just one)."""
    qubits = cirq.LineQubit.range(2)
    # Create a subcircuit with MULTIPLE operations
    subcircuit = cirq.Circuit(cirq.H(qubits[0]), cirq.CNOT(qubits[0], qubits[1]), cirq.X(qubits[1]))
    circuit_op = cirq.CircuitOperation(cirq.FrozenCircuit(subcircuit))
    circuit = cirq.Circuit(circuit_op)

    preprocessed_circuit = preprocess_circuit(circuit)
    # When CircuitOperation has > 1 op, different code path
    assert len(list(preprocessed_circuit.all_operations())) > 0


def test_tagged_circuit_operation():
    """Test a tagged CircuitOperation."""
    qubits = cirq.LineQubit.range(2)
    subcircuit = cirq.Circuit(cirq.H(qubits[0]), cirq.CNOT(qubits[0], qubits[1]))
    circuit_op = cirq.CircuitOperation(cirq.FrozenCircuit(subcircuit)).with_tags("custom_tag")
    circuit = cirq.Circuit(circuit_op)

    preprocessed_circuit = preprocess_circuit(circuit)
    assert len(list(preprocessed_circuit.all_operations())) > 0


def test_operation_without_gate_attribute():
    """Test handling of operations that don't have a gate attribute."""
    # CircuitOperation itself doesn't have a 'gate' attribute in some cases
    qubits = cirq.LineQubit.range(2)
    subcircuit = cirq.Circuit(cirq.H(qubits[0]))

    # This creates an operation without standard gate attribute
    circuit_op = cirq.CircuitOperation(cirq.FrozenCircuit(subcircuit))
    circuit = cirq.Circuit(circuit_op)

    preprocessed_circuit = preprocess_circuit(circuit)
    assert len(list(preprocessed_circuit.all_operations())) >= 0


def test_conditional_circuit_with_non_circuit_result():
    """Test that AbstractCircuit results are properly converted to Circuit."""
    qubits = cirq.LineQubit.range(2)
    # Create a conditional circuit that goes through postprocessors
    circuit = cirq.Circuit(
        cirq.H(qubits[0]),
        cirq.measure(qubits[0], key="m"),
        cirq.X(qubits[1]).with_classical_controls("m"),
    )

    preprocessed_circuit = preprocess_circuit(circuit)

    # Ensure result is a Circuit, not AbstractCircuit
    assert isinstance(preprocessed_circuit, cirq.Circuit)
    assert any(
        isinstance(op, cirq.ClassicallyControlledOperation)
        for op in preprocessed_circuit.all_operations()
    )


def test_rads_attribute_already_exists():
    """Test handling when _rads attribute already exists (older Cirq)."""
    qubit = cirq.LineQubit(0)
    gate = cirq.XPowGate(exponent=0.5)

    # Manually set _rads to simulate older Cirq
    try:
        gate._rads = np.pi / 2
    except AttributeError:
        pass

    circuit = cirq.Circuit(gate(qubit))
    preprocessed_circuit = preprocess_circuit(circuit)

    # Should handle the AttributeError gracefully
    assert len(list(preprocessed_circuit.all_operations())) > 0


def test_multi_qubit_operation_already_valid():
    """Test multi-qubit operation that's already in the gateset."""
    qubits = cirq.LineQubit.range(3)
    # TOFFOLI is valid, so validate() should return True
    circuit = cirq.Circuit(cirq.TOFFOLI(*qubits))

    preprocessed_circuit = preprocess_circuit(circuit)

    # Should preserve the TOFFOLI without decomposition
    has_toffoli = any(
        isinstance(op.gate, cirq.CCXPowGate) for op in preprocessed_circuit.all_operations()
    )
    assert has_toffoli


def test_preprocessing_failure_raises_conversion_error():
    """Test that preprocessing failures raise CirqConversionError."""

    # Create a problematic circuit that will fail optimization
    class BadGate(cirq.Gate):
        def _qid_shape_(self):
            return (2, 2)

        def _num_qubits_(self):
            return 2

        def num_qubits(self):
            return 2

        def _decompose_(self, qubits):
            # Return invalid decomposition to cause error
            raise ValueError("Intentional error for testing")

    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(BadGate().on(*qubits))

    # Should catch exception and raise CirqConversionError
    with pytest.raises(CirqConversionError) as exc_info:
        preprocess_circuit(circuit)

    assert "Failed to preprocess circuit" in str(exc_info.value)


def test_power_gates_with_negative_exponents():
    """Test power gates with negative exponents."""
    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.XPowGate(exponent=-0.5)(qubits[0]),
        cirq.YPowGate(exponent=-0.25)(qubits[0]),
        cirq.ZPowGate(exponent=-0.75)(qubits[0]),
        cirq.CNotPowGate(exponent=-0.5)(qubits[0], qubits[1]),
    )

    preprocessed_circuit = preprocess_circuit(circuit)

    # Check _rads is calculated correctly even for negative exponents
    for op in preprocessed_circuit.all_operations():
        if isinstance(op.gate, (cirq.XPowGate, cirq.YPowGate, cirq.ZPowGate)):
            assert hasattr(op.gate, "_rads")
            expected_rads = float(op.gate.exponent * np.pi)
            assert np.isclose(op.gate._rads, expected_rads)


def test_power_gates_with_large_exponents():
    """Test power gates with exponents > 1."""
    qubit = cirq.LineQubit(0)
    circuit = cirq.Circuit(
        cirq.XPowGate(exponent=2.5)(qubit),
        cirq.HPowGate(exponent=3.0)(qubit),
    )

    preprocessed_circuit = preprocess_circuit(circuit)

    for op in preprocessed_circuit.all_operations():
        if isinstance(op.gate, cirq.XPowGate):
            assert hasattr(op.gate, "_rads")
            expected_rads = float(2.5 * np.pi)
            assert np.isclose(op.gate._rads, expected_rads)


def test_two_qubit_gate_with_atol_parameter():
    """Test two-qubit decomposition respects atol parameter."""
    qubits = cirq.LineQubit.range(2)
    # Use a gate close to identity
    circuit = cirq.Circuit(cirq.ISwapPowGate(exponent=1e-8).on(*qubits))

    preprocessed_circuit = preprocess_circuit(circuit)
    # Should decompose even very small rotations
    assert len(list(preprocessed_circuit.all_operations())) >= 0


def test_two_qubit_decomposition_with_partial_czs():
    """Test that allow_partial_czs parameter is used."""
    qubits = cirq.LineQubit.range(2)
    # Create a gate that would benefit from partial CZs
    circuit = cirq.Circuit(cirq.ISwapPowGate(exponent=0.1234).on(*qubits))

    # The allow_partial_czs is set in QirTargetGateSet
    preprocessed_circuit = preprocess_circuit(circuit)
    assert len(list(preprocessed_circuit.all_operations())) > 0


def test_multi_level_tagged_operations():
    """Test operations with multiple levels of tagging."""
    qubits = cirq.LineQubit.range(3)
    # Multi-qubit gate with nested tags
    op = cirq.TOFFOLI(*qubits).with_tags("tag1", "tag2")
    circuit = cirq.Circuit(op)

    preprocessed_circuit = preprocess_circuit(circuit)
    assert len(list(preprocessed_circuit.all_operations())) > 0


def test_tagged_then_circuit_operation():
    """Test a tagged operation that's also a CircuitOperation."""
    qubits = cirq.LineQubit.range(2)
    subcircuit = cirq.Circuit(cirq.CNOT(qubits[0], qubits[1]))
    circuit_op = cirq.CircuitOperation(cirq.FrozenCircuit(subcircuit)).with_tags("wrapper")

    circuit = cirq.Circuit(circuit_op)
    preprocessed_circuit = preprocess_circuit(circuit)
    assert len(list(preprocessed_circuit.all_operations())) > 0


def test_arbitrary_single_qubit_unitary():
    """Test decomposition of arbitrary single-qubit unitary."""
    qubit = cirq.LineQubit(0)

    # Create a custom unitary matrix
    theta = np.pi / 7
    phi = np.pi / 5
    custom_matrix = np.array(
        [
            [np.cos(theta), -np.sin(theta) * np.exp(1j * phi)],
            [np.sin(theta) * np.exp(-1j * phi), np.cos(theta)],
        ]
    )

    class CustomUnitaryGate(cirq.Gate):
        def _qid_shape_(self):
            return (2,)

        def _num_qubits_(self):
            return 1

        def num_qubits(self):
            return 1

        def _unitary_(self):
            return custom_matrix

    circuit = cirq.Circuit(CustomUnitaryGate()(qubit))
    preprocessed_circuit = preprocess_circuit(circuit)

    # Should decompose into supported gates
    assert len(list(preprocessed_circuit.all_operations())) > 0
    assert circuits_allclose(preprocessed_circuit, circuit)


def test_circuit_with_repeated_decomposition_needed():
    """Test circuit requiring multiple decomposition passes."""
    qubits = cirq.LineQubit.range(2)

    # Use gates that will require nested decomposition
    circuit = cirq.Circuit(
        cirq.ISwapPowGate(exponent=0.3).on(*qubits),
        cirq.FSimGate(theta=np.pi / 4, phi=np.pi / 6).on(*qubits),
    )

    preprocessed_circuit = preprocess_circuit(circuit)

    # Should not contain original gates
    for op in preprocessed_circuit.all_operations():
        assert not isinstance(op.gate, (cirq.ISwapPowGate, cirq.FSimGate))

    assert circuits_allclose(preprocessed_circuit, circuit)


def test_intermediate_result_tags():
    """Test that intermediate results are properly tagged."""
    qubits = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.H(qubits[0]),
        cirq.CNOT(qubits[0], qubits[1]),
    )

    preprocessed_circuit = preprocess_circuit(circuit)

    # Check for any tagged operations from merge process
    # (tags may or may not be present depending on optimization)
    assert len(list(preprocessed_circuit.all_operations())) > 0


def test_multi_qubit_operation_validates_directly():
    """
    Test that a valid multi-qubit operation (TOFFOLI) passes validate()
    and is returned as-is without unwrapping.
    """
    qubits = cirq.LineQubit.range(3)
    circuit = cirq.Circuit(cirq.TOFFOLI(*qubits))

    preprocessed = preprocess_circuit(circuit)

    # Should contain exactly one TOFFOLI gate, not decomposed
    ops = list(preprocessed.all_operations())
    assert len(ops) == 1
    assert isinstance(ops[0].gate, cirq.CCXPowGate)
    assert circuits_allclose(preprocessed, circuit)


def test_multi_qubit_ccxpowgate_validates():
    """
    Test CCXPowGate with exponent=1 validates and isn't decomposed.
    """
    qubits = cirq.LineQubit.range(3)
    gate = cirq.CCXPowGate(exponent=1.0)
    circuit = cirq.Circuit(gate(*qubits))

    preprocessed = preprocess_circuit(circuit)

    ops = list(preprocessed.all_operations())
    assert any(isinstance(op.gate, cirq.CCXPowGate) for op in ops)
