# Copyright 2026 qBraid
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
Unit tests for Qiskit to QIR conversion — integration, error handling, API contract.

"""

import pyqir
import pytest
from pyqir import (
    Context,
    is_entry_point,
    qir_module,
    required_num_qubits,
    required_num_results,
)
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit import Gate

from qbraid_qir.qiskit import BasicQiskitVisitor, QiskitModule, qiskit_to_qir
from qbraid_qir.qiskit.exceptions import QiskitConversionError
from qbraid_qir.qiskit.maps import map_qiskit_op_to_pyqir_callable


def _get_body(module):
    func = next(filter(is_entry_point, module.functions))
    lines = str(func).splitlines()[2:-1]
    return [line.strip() for line in lines]


def _get_entry_point(module):
    return next(filter(is_entry_point, module.functions))


# ---------------------------------------------------------------------------
# Integration tests using fixtures
# ---------------------------------------------------------------------------


class TestQiskitToQir:
    """Tests for the qiskit_to_qir function with sequential verification."""

    def test_bell_circuit(self, bell_circuit):
        module = qiskit_to_qir(bell_circuit)
        func = _get_entry_point(module)
        assert required_num_qubits(func) == 2
        assert required_num_results(func) == 2

        body = _get_body(module)
        gate_ops = [l for l in body if "qis__" in l]
        assert "qis__h__body" in gate_ops[0]
        assert "qis__cnot__body" in gate_ops[1]
        assert "qis__mz__body" in gate_ops[2]
        assert "qis__mz__body" in gate_ops[3]

    def test_ghz_circuit(self, ghz_circuit):
        module = qiskit_to_qir(ghz_circuit)
        func = _get_entry_point(module)
        assert required_num_qubits(func) == 3
        assert required_num_results(func) == 3

        body = _get_body(module)
        gate_ops = [l for l in body if "qis__" in l]
        # H, CX, CX, MZ, MZ, MZ
        assert len(gate_ops) == 6
        assert "qis__h__body" in gate_ops[0]
        assert "qis__cnot__body" in gate_ops[1]
        assert "qis__cnot__body" in gate_ops[2]

    def test_single_qubit_gates(self, single_qubit_gates_circuit):
        module = qiskit_to_qir(single_qubit_gates_circuit)
        body = _get_body(module)
        gate_ops = [l for l in body if "qis__" in l]

        expected_gates = ["h", "x", "y", "z", "s", "s__adj", "t", "t__adj"]
        assert len(gate_ops) == len(expected_gates)
        for op, gate in zip(gate_ops, expected_gates):
            assert f"qis__{gate}" in op

    def test_rotation_gates(self, rotation_gates_circuit):
        module = qiskit_to_qir(rotation_gates_circuit)
        body = _get_body(module)
        gate_ops = [l for l in body if "qis__" in l]
        assert len(gate_ops) == 3
        assert "qis__rx__body" in gate_ops[0]
        assert "qis__ry__body" in gate_ops[1]
        assert "qis__rz__body" in gate_ops[2]

    def test_two_qubit_gates(self, two_qubit_gates_circuit):
        module = qiskit_to_qir(two_qubit_gates_circuit)
        body = _get_body(module)
        gate_ops = [l for l in body if "qis__" in l]
        assert len(gate_ops) == 3
        assert "qis__cnot__body" in gate_ops[0]
        assert "qis__cz__body" in gate_ops[1]
        assert "qis__swap__body" in gate_ops[2]

    def test_three_qubit_gates(self, three_qubit_gates_circuit):
        module = qiskit_to_qir(three_qubit_gates_circuit)
        body = _get_body(module)
        gate_ops = [l for l in body if "qis__" in l]
        assert len(gate_ops) == 1
        assert "qis__ccx__body" in gate_ops[0]

    def test_reset_gate(self, reset_circuit):
        module = qiskit_to_qir(reset_circuit)
        body = _get_body(module)
        gate_ops = [l for l in body if "qis__" in l]
        assert len(gate_ops) == 2
        assert "qis__reset__body" in gate_ops[0]
        assert "qis__h__body" in gate_ops[1]

    def test_identity_gate(self, identity_circuit):
        """Identity gate is now a true no-op."""
        module = qiskit_to_qir(identity_circuit)
        body = _get_body(module)
        gate_ops = [l for l in body if "qis__" in l]
        assert len(gate_ops) == 0

    def test_barrier_not_emitted_by_default(self, barrier_circuit):
        module = qiskit_to_qir(barrier_circuit)
        body = _get_body(module)
        gate_ops = [l for l in body if "qis__" in l]
        assert not any("barrier" in l for l in gate_ops)

    def test_barrier_emitted_when_enabled(self, barrier_circuit):
        module = qiskit_to_qir(barrier_circuit, emit_barrier_calls=True)
        body = _get_body(module)
        gate_ops = [l for l in body if "qis__" in l]
        assert any("barrier" in l for l in gate_ops)

    def test_delay_ignored(self, delay_circuit):
        module = qiskit_to_qir(delay_circuit)
        ir = str(module)
        assert "delay" not in ir.lower()
        body = _get_body(module)
        gate_ops = [l for l in body if "qis__" in l]
        assert len(gate_ops) == 2
        assert "qis__h__body" in gate_ops[0]
        assert "qis__x__body" in gate_ops[1]

    def test_named_registers(self, named_registers_circuit):
        module = qiskit_to_qir(named_registers_circuit, name="test_named")
        ir = str(module)
        assert "test_named" in ir

    def test_multiple_registers(self, multiple_registers_circuit):
        module = qiskit_to_qir(multiple_registers_circuit)
        func = _get_entry_point(module)
        assert required_num_qubits(func) == 3
        assert required_num_results(func) == 3

        body = _get_body(module)
        # Check output recording has two array_record_output calls (2 classical registers)
        array_records = [l for l in body if "array_record_output" in l]
        assert len(array_records) == 2

    def test_composite_gate(self, composite_gate_circuit):
        """Composite gate should be decomposed into primitive gates."""
        module = qiskit_to_qir(composite_gate_circuit)
        body = _get_body(module)
        gate_ops = [l for l in body if "qis__" in l]

        # bell_prep decomposes to H + CX, then measure
        gate_names = []
        for op in gate_ops:
            if "qis__h__body" in op:
                gate_names.append("h")
            elif "qis__cnot__body" in op:
                gate_names.append("cnot")
            elif "qis__mz__body" in op:
                gate_names.append("mz")

        assert "h" in gate_names
        assert "cnot" in gate_names
        assert "mz" in gate_names

    def test_custom_name(self, bell_circuit):
        module = qiskit_to_qir(bell_circuit, name="custom_bell")
        ir = str(module)
        assert "custom_bell" in ir

    def test_no_runtime_init(self, bell_circuit):
        module = qiskit_to_qir(bell_circuit, initialize_runtime=False)
        ir = str(module)
        assert "__quantum__rt__initialize" not in ir

    def test_no_output_recording(self, bell_circuit):
        module = qiskit_to_qir(bell_circuit, record_output=False)
        ir = str(module)
        assert "__quantum__rt__result_record_output" not in ir
        assert "__quantum__rt__array_record_output" not in ir


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestQiskitToQirErrors:
    """Tests for error handling in qiskit_to_qir."""

    def test_invalid_input_type(self):
        with pytest.raises(TypeError, match="must be of type qiskit.QuantumCircuit"):
            qiskit_to_qir("not a circuit")

    def test_empty_circuit(self):
        circuit = QuantumCircuit(1)
        with pytest.raises(ValueError, match="at least one operation"):
            qiskit_to_qir(circuit)

    def test_unsupported_gate_no_definition(self):
        """Gate with no decomposition should raise QiskitConversionError."""

        class NoDefGate(Gate):
            def __init__(self):
                super().__init__("no_def_gate", 1, [])

        circuit = QuantumCircuit(1)
        circuit.append(NoDefGate(), [0])
        with pytest.raises(QiskitConversionError, match="not supported"):
            qiskit_to_qir(circuit)


# ---------------------------------------------------------------------------
# QiskitModule
# ---------------------------------------------------------------------------


class TestQiskitModule:
    """Tests for QiskitModule class."""

    def test_from_circuit(self, bell_circuit):
        module = QiskitModule.from_circuit(bell_circuit, None)
        assert module.num_qubits == 2
        assert module.num_clbits == 2
        assert module.name in (bell_circuit.name, "main")

    def test_circuit_property(self, bell_circuit):
        module = QiskitModule.from_circuit(bell_circuit, None)
        assert module.circuit is bell_circuit

    def test_reg_sizes(self):
        """Test reg_sizes for multiple classical registers."""
        qr = QuantumRegister(3)
        cr1 = ClassicalRegister(2)
        cr2 = ClassicalRegister(1)
        circuit = QuantumCircuit(qr, cr1, cr2)
        circuit.h(0)

        module = QiskitModule.from_circuit(circuit, None)
        assert module.reg_sizes == [2, 1]


# ---------------------------------------------------------------------------
# BasicQiskitVisitor
# ---------------------------------------------------------------------------


class TestBasicQiskitVisitor:
    """Tests for BasicQiskitVisitor class."""

    def test_visitor_entry_point(self, bell_circuit):
        llvm_module = qir_module(Context(), "test")
        qiskit_module = QiskitModule.from_circuit(bell_circuit, llvm_module)

        visitor = BasicQiskitVisitor()
        qiskit_module.accept(visitor)

        assert visitor.entry_point is not None
        assert len(visitor.entry_point) > 0

    def test_visitor_ir_output(self, bell_circuit):
        llvm_module = qir_module(Context(), "test")
        qiskit_module = QiskitModule.from_circuit(bell_circuit, llvm_module)

        visitor = BasicQiskitVisitor()
        qiskit_module.accept(visitor)

        ir = visitor.ir()
        assert len(ir) > 0
        assert "__quantum__qis__h__body" in ir

    def test_visitor_bitcode_output(self, bell_circuit):
        llvm_module = qir_module(Context(), "test")
        qiskit_module = QiskitModule.from_circuit(bell_circuit, llvm_module)

        visitor = BasicQiskitVisitor()
        qiskit_module.accept(visitor)

        bitcode = visitor.bitcode()
        assert isinstance(bitcode, bytes)
        assert len(bitcode) > 0


# ---------------------------------------------------------------------------
# SDK API contract
# ---------------------------------------------------------------------------


class TestMaps:
    """Tests for the maps module utility function."""

    def test_map_one_qubit_op(self):
        func, num_qubits = map_qiskit_op_to_pyqir_callable("h")
        assert num_qubits == 1
        assert func is not None

    def test_map_rotation_op(self):
        func, num_qubits = map_qiskit_op_to_pyqir_callable("rx")
        assert num_qubits == 1
        assert func is not None

    def test_map_two_qubit_op(self):
        func, num_qubits = map_qiskit_op_to_pyqir_callable("cx")
        assert num_qubits == 2
        assert func is not None

    def test_map_three_qubit_op(self):
        func, num_qubits = map_qiskit_op_to_pyqir_callable("ccx")
        assert num_qubits == 3
        assert func is not None

    def test_map_unsupported_op(self):
        with pytest.raises(QiskitConversionError, match="Unsupported"):
            map_qiskit_op_to_pyqir_callable("nonexistent_gate")

    def test_map_case_insensitive(self):
        fn1, n1 = map_qiskit_op_to_pyqir_callable("H")
        fn2, n2 = map_qiskit_op_to_pyqir_callable("h")
        assert fn1 == fn2
        assert n1 == n2


class TestSdkApiContract:
    """Verify the API matches what qBraid SDK PR #1132 expects."""

    def test_qiskit_to_qir_returns_module(self):
        circuit = QuantumCircuit(2, 2)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.measure([0, 1], [0, 1])
        module = qiskit_to_qir(circuit)
        assert isinstance(module, pyqir.Module)

    def test_function_accepts_circuit_only(self):
        """SDK calls qiskit_to_qir(circuit) with no extra args."""
        circuit = QuantumCircuit(1)
        circuit.h(0)
        module = qiskit_to_qir(circuit)
        assert module is not None
