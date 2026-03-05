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
Unit tests for Qiskit to QIR conversion.

"""

import pytest
from pyqir import Context, is_entry_point, qir_module, required_num_qubits, required_num_results
from qiskit import QuantumCircuit

from qbraid_qir.qiskit import BasicQiskitVisitor, QiskitModule, qiskit_to_qir


class TestQiskitToQir:
    """Tests for the qiskit_to_qir function."""

    def test_bell_circuit(self, bell_circuit):
        """Test conversion of a Bell state circuit."""
        module = qiskit_to_qir(bell_circuit)
        assert module is not None
        ir = str(module)
        assert "__quantum__qis__h__body" in ir
        assert "__quantum__qis__cnot__body" in ir
        assert "__quantum__qis__mz__body" in ir

    def test_ghz_circuit(self, ghz_circuit):
        """Test conversion of a GHZ state circuit."""
        module = qiskit_to_qir(ghz_circuit)
        assert module is not None
        # Verify the entry point has correct attributes
        func = next(filter(is_entry_point, module.functions))
        assert required_num_qubits(func) == 3
        assert required_num_results(func) == 3

    def test_single_qubit_gates(self, single_qubit_gates_circuit):
        """Test conversion of single-qubit gates."""
        module = qiskit_to_qir(single_qubit_gates_circuit)
        ir = str(module)
        assert "__quantum__qis__h__body" in ir
        assert "__quantum__qis__x__body" in ir
        assert "__quantum__qis__y__body" in ir
        assert "__quantum__qis__z__body" in ir
        assert "__quantum__qis__s__body" in ir
        assert "__quantum__qis__s__adj" in ir
        assert "__quantum__qis__t__body" in ir
        assert "__quantum__qis__t__adj" in ir

    def test_rotation_gates(self, rotation_gates_circuit):
        """Test conversion of rotation gates."""
        module = qiskit_to_qir(rotation_gates_circuit)
        ir = str(module)
        assert "__quantum__qis__rx__body" in ir
        assert "__quantum__qis__ry__body" in ir
        assert "__quantum__qis__rz__body" in ir

    def test_two_qubit_gates(self, two_qubit_gates_circuit):
        """Test conversion of two-qubit gates."""
        module = qiskit_to_qir(two_qubit_gates_circuit)
        ir = str(module)
        assert "__quantum__qis__cnot__body" in ir
        assert "__quantum__qis__cz__body" in ir
        assert "__quantum__qis__swap__body" in ir

    def test_three_qubit_gates(self, three_qubit_gates_circuit):
        """Test conversion of three-qubit gates (CCX/Toffoli)."""
        module = qiskit_to_qir(three_qubit_gates_circuit)
        ir = str(module)
        assert "__quantum__qis__ccx__body" in ir

    def test_reset_gate(self, reset_circuit):
        """Test conversion of reset gate."""
        module = qiskit_to_qir(reset_circuit)
        ir = str(module)
        assert "__quantum__qis__reset__body" in ir

    def test_identity_gate(self, identity_circuit):
        """Test conversion of identity gate (implemented as X.X)."""
        module = qiskit_to_qir(identity_circuit)
        ir = str(module)
        # Identity is implemented as two X gates (count calls, not declarations)
        assert ir.count("call void @__quantum__qis__x__body") == 2

    def test_barrier_not_emitted_by_default(self, barrier_circuit):
        """Test that barrier is not emitted by default."""
        module = qiskit_to_qir(barrier_circuit)
        ir = str(module)
        assert "__quantum__qis__barrier__body" not in ir

    def test_barrier_emitted_when_enabled(self, barrier_circuit):
        """Test that barrier is emitted when emit_barrier_calls=True."""
        module = qiskit_to_qir(barrier_circuit, emit_barrier_calls=True)
        ir = str(module)
        assert "__quantum__qis__barrier__body" in ir

    def test_delay_ignored(self, delay_circuit):
        """Test that delay instruction is ignored (no-op)."""
        module = qiskit_to_qir(delay_circuit)
        ir = str(module)
        # Delay should not produce any output
        assert "delay" not in ir.lower()
        # But the other gates should be present
        assert "__quantum__qis__h__body" in ir
        assert "__quantum__qis__x__body" in ir

    def test_named_registers(self, named_registers_circuit):
        """Test conversion with named quantum and classical registers."""
        module = qiskit_to_qir(named_registers_circuit, name="test_named")
        assert module is not None
        ir = str(module)
        assert "test_named" in ir or "@test_named" in ir

    def test_multiple_registers(self, multiple_registers_circuit):
        """Test conversion with multiple quantum and classical registers."""
        module = qiskit_to_qir(multiple_registers_circuit)
        func = next(filter(is_entry_point, module.functions))
        # Total: 2 + 1 = 3 qubits, 2 + 1 = 3 classical bits
        assert required_num_qubits(func) == 3
        assert required_num_results(func) == 3

    def test_composite_gate(self, composite_gate_circuit):
        """Test conversion of composite (custom) gates."""
        module = qiskit_to_qir(composite_gate_circuit)
        ir = str(module)
        # The composite gate should be decomposed
        assert "__quantum__qis__h__body" in ir
        assert "__quantum__qis__cnot__body" in ir
        assert "__quantum__qis__mz__body" in ir

    def test_custom_name(self, bell_circuit):
        """Test that custom module name is used."""
        module = qiskit_to_qir(bell_circuit, name="custom_bell")
        ir = str(module)
        assert "custom_bell" in ir or "@custom_bell" in ir

    def test_no_runtime_init(self, bell_circuit):
        """Test conversion without runtime initialization."""
        module = qiskit_to_qir(bell_circuit, initialize_runtime=False)
        ir = str(module)
        assert "__quantum__rt__initialize" not in ir

    def test_no_output_recording(self, bell_circuit):
        """Test conversion without output recording."""
        module = qiskit_to_qir(bell_circuit, record_output=False)
        ir = str(module)
        assert "__quantum__rt__result_record_output" not in ir
        assert "__quantum__rt__array_record_output" not in ir


class TestQiskitToQirErrors:
    """Tests for error handling in qiskit_to_qir."""

    def test_invalid_input_type(self):
        """Test that TypeError is raised for non-QuantumCircuit input."""
        with pytest.raises(TypeError, match="must be of type qiskit.QuantumCircuit"):
            qiskit_to_qir("not a circuit")

    def test_empty_circuit(self):
        """Test that ValueError is raised for empty circuit."""
        circuit = QuantumCircuit(1)
        with pytest.raises(ValueError, match="at least one operation"):
            qiskit_to_qir(circuit)

    @pytest.mark.skip(reason="Most gates in qiskit 2.x have decompositions to base gates")
    def test_unsupported_gate(self):
        """Test that QiskitConversionError is raised for unsupported gates."""
        # In qiskit 2.x, most gates have decompositions, so it's hard to find
        # a gate that will truly fail. This test is skipped for now.


class TestQiskitModule:
    """Tests for QiskitModule class."""

    def test_from_circuit(self, bell_circuit):
        """Test QiskitModule.from_circuit factory method."""
        module = QiskitModule.from_circuit(bell_circuit, None)
        assert module.num_qubits == 2
        assert module.num_clbits == 2
        assert module.name in (bell_circuit.name, "main")

    def test_circuit_property(self, bell_circuit):
        """Test that circuit property returns the original circuit."""
        module = QiskitModule.from_circuit(bell_circuit, None)
        assert module.circuit is bell_circuit


class TestBasicQiskitVisitor:
    """Tests for BasicQiskitVisitor class."""

    def test_visitor_entry_point(self, bell_circuit):
        """Test that visitor generates correct entry point."""
        llvm_module = qir_module(Context(), "test")
        qiskit_module = QiskitModule.from_circuit(bell_circuit, llvm_module)

        visitor = BasicQiskitVisitor()
        qiskit_module.accept(visitor)

        assert visitor.entry_point is not None
        assert len(visitor.entry_point) > 0

    def test_visitor_ir_output(self, bell_circuit):
        """Test that visitor can generate IR string."""
        llvm_module = qir_module(Context(), "test")
        qiskit_module = QiskitModule.from_circuit(bell_circuit, llvm_module)

        visitor = BasicQiskitVisitor()
        qiskit_module.accept(visitor)

        ir = visitor.ir()
        assert ir is not None
        assert len(ir) > 0
        assert "__quantum__qis__h__body" in ir
