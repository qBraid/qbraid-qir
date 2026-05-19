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
Tests for complex Qiskit circuits, transpilation support, and edge cases.

"""

import math

import pytest
from pyqir import is_entry_point, required_num_qubits, required_num_results
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit import Gate, Parameter
from qiskit.circuit.random import random_circuit

from qbraid_qir.qiskit import qiskit_to_qir
from qbraid_qir.qiskit.exceptions import QiskitConversionError


def _get_body(module):
    func = next(filter(is_entry_point, module.functions))
    lines = str(func).splitlines()[2:-1]
    return [line.strip() for line in lines]


def _gate_ops(module):
    """Return only qis__ gate call lines from the body."""
    return [l for l in _get_body(module) if "qis__" in l]


# ---------------------------------------------------------------------------
# Complex circuit tests
# ---------------------------------------------------------------------------


class TestQuantumTeleportation:
    """Test quantum teleportation circuit."""

    def test_teleportation_circuit(self):
        qr = QuantumRegister(3, "q")
        cr = ClassicalRegister(2, "c")
        circuit = QuantumCircuit(qr, cr)

        # Create Bell pair between q1 and q2
        circuit.h(1)
        circuit.cx(1, 2)

        # Alice's operations
        circuit.cx(0, 1)
        circuit.h(0)

        # Measure
        circuit.measure(0, 0)
        circuit.measure(1, 1)

        module = qiskit_to_qir(circuit)
        func = next(filter(is_entry_point, module.functions))
        assert required_num_qubits(func) == 3
        assert required_num_results(func) == 2

        ops = _gate_ops(module)
        gate_names = []
        for op in ops:
            if "qis__h__body" in op:
                gate_names.append("h")
            elif "qis__cnot__body" in op:
                gate_names.append("cnot")
            elif "qis__mz__body" in op:
                gate_names.append("mz")

        # H, CX, CX, H, MZ, MZ
        assert gate_names == ["h", "cnot", "cnot", "h", "mz", "mz"]


class TestGroverTwoQubit:
    """Test 2-qubit Grover's algorithm circuit."""

    def test_grover_circuit(self):
        circuit = QuantumCircuit(2, 2)

        # Initialize superposition
        circuit.h(0)
        circuit.h(1)

        # Oracle (mark |11>)
        circuit.cz(0, 1)

        # Diffusion operator
        circuit.h(0)
        circuit.h(1)
        circuit.x(0)
        circuit.x(1)
        circuit.cz(0, 1)
        circuit.x(0)
        circuit.x(1)
        circuit.h(0)
        circuit.h(1)

        circuit.measure([0, 1], [0, 1])

        module = qiskit_to_qir(circuit)
        ops = _gate_ops(module)
        assert len(ops) == 14  # 2H + CZ + 2H + 2X + CZ + 2X + 2H + 2MZ


class TestParameterizedCircuits:
    """Test parameterized circuits with bound parameters."""

    def test_bound_parameter(self):
        theta = Parameter("theta")
        circuit = QuantumCircuit(1)
        circuit.rx(theta, 0)
        bound = circuit.assign_parameters({theta: math.pi / 4})

        module = qiskit_to_qir(bound)
        ops = _gate_ops(module)
        assert len(ops) == 1
        assert "qis__rx__body" in ops[0]
        assert "double" in ops[0]

    def test_multiple_bound_parameters(self):
        a = Parameter("a")
        b = Parameter("b")
        circuit = QuantumCircuit(1)
        circuit.rx(a, 0)
        circuit.ry(b, 0)
        bound = circuit.assign_parameters({a: 0.5, b: 1.0})

        module = qiskit_to_qir(bound)
        ops = _gate_ops(module)
        assert len(ops) == 2
        assert "qis__rx__body" in ops[0]
        assert "qis__ry__body" in ops[1]


class TestCustomGates:
    """Test custom (composite) gate decomposition."""

    def test_simple_custom_gate(self):
        """Custom gate that decomposes to H + CX."""
        sub = QuantumCircuit(2, name="my_bell")
        sub.h(0)
        sub.cx(0, 1)
        bell_gate = sub.to_gate()

        circuit = QuantumCircuit(2)
        circuit.append(bell_gate, [0, 1])

        module = qiskit_to_qir(circuit)
        ops = _gate_ops(module)
        assert len(ops) == 2
        assert "qis__h__body" in ops[0]
        assert "qis__cnot__body" in ops[1]

    def test_nested_custom_gate(self):
        """Custom gate containing another custom gate."""
        inner = QuantumCircuit(1, name="inner_gate")
        inner.h(0)
        inner.z(0)
        inner_gate = inner.to_gate()

        outer = QuantumCircuit(2, name="outer_gate")
        outer.append(inner_gate, [0])
        outer.cx(0, 1)
        outer_gate = outer.to_gate()

        circuit = QuantumCircuit(2)
        circuit.append(outer_gate, [0, 1])

        module = qiskit_to_qir(circuit)
        ops = _gate_ops(module)
        assert len(ops) == 3
        assert "qis__h__body" in ops[0]
        assert "qis__z__body" in ops[1]
        assert "qis__cnot__body" in ops[2]


class TestLargeCircuits:
    """Test with larger circuits for regression."""

    def test_10_qubit_circuit(self):
        n = 10
        circuit = QuantumCircuit(n)
        for i in range(n):
            circuit.h(i)
        for i in range(n - 1):
            circuit.cx(i, i + 1)

        module = qiskit_to_qir(circuit)
        func = next(filter(is_entry_point, module.functions))
        assert required_num_qubits(func) == n

        ops = _gate_ops(module)
        h_count = sum(1 for l in ops if "qis__h__body" in l)
        cx_count = sum(1 for l in ops if "qis__cnot__body" in l)
        assert h_count == n
        assert cx_count == n - 1

    def test_20_qubit_ghz(self):
        n = 20
        circuit = QuantumCircuit(n, n)
        circuit.h(0)
        for i in range(n - 1):
            circuit.cx(i, i + 1)
        circuit.measure(range(n), range(n))

        module = qiskit_to_qir(circuit)
        func = next(filter(is_entry_point, module.functions))
        assert required_num_qubits(func) == n
        assert required_num_results(func) == n


class TestMultipleClassicalRegisters:
    """Test circuits with multiple classical registers."""

    def test_selective_measurement(self):
        """Measure only some qubits into specific registers."""
        qr = QuantumRegister(3, "q")
        cr1 = ClassicalRegister(1, "c1")
        cr2 = ClassicalRegister(2, "c2")
        circuit = QuantumCircuit(qr, cr1, cr2)
        circuit.h(0)
        circuit.h(1)
        circuit.h(2)
        circuit.measure(0, cr1[0])
        circuit.measure(1, cr2[0])
        circuit.measure(2, cr2[1])

        module = qiskit_to_qir(circuit)
        func = next(filter(is_entry_point, module.functions))
        assert required_num_qubits(func) == 3
        assert required_num_results(func) == 3

        body = _get_body(module)
        array_records = [l for l in body if "array_record_output" in l]
        assert len(array_records) == 2  # Two classical registers

    def test_three_classical_registers(self):
        qr = QuantumRegister(3)
        cr1 = ClassicalRegister(1, "a")
        cr2 = ClassicalRegister(1, "b")
        cr3 = ClassicalRegister(1, "c")
        circuit = QuantumCircuit(qr, cr1, cr2, cr3)
        circuit.h(0)
        circuit.h(1)
        circuit.h(2)
        circuit.measure(0, cr1[0])
        circuit.measure(1, cr2[0])
        circuit.measure(2, cr3[0])

        module = qiskit_to_qir(circuit)
        body = _get_body(module)
        array_records = [l for l in body if "array_record_output" in l]
        assert len(array_records) == 3


# ---------------------------------------------------------------------------
# Transpilation tests
# ---------------------------------------------------------------------------


class TestTranspilation:
    """Test the transpile=True flag for converting unsupported gates."""

    def test_ecr_gate_with_transpile(self):
        """ECR gate is not natively supported but can be transpiled."""
        circuit = QuantumCircuit(2)
        circuit.ecr(0, 1)

        module = qiskit_to_qir(circuit, transpile=True)
        ops = _gate_ops(module)
        assert len(ops) > 0
        # Should not contain ECR in the output
        assert not any("ecr" in l.lower() for l in ops)

    def test_u_gate_with_transpile(self):
        """U gate transpiled to basis gates."""
        circuit = QuantumCircuit(1)
        circuit.u(math.pi / 4, math.pi / 2, math.pi, 0)

        module = qiskit_to_qir(circuit, transpile=True)
        ops = _gate_ops(module)
        assert len(ops) > 0

    def test_cswap_with_transpile(self):
        """CSWAP (Fredkin) gate transpiled to basis gates."""
        circuit = QuantumCircuit(3)
        circuit.cswap(0, 1, 2)

        module = qiskit_to_qir(circuit, transpile=True)
        ops = _gate_ops(module)
        assert len(ops) > 0

    def test_transpile_preserves_simple_circuit(self):
        """Transpiling a circuit that's already in basis gates shouldn't break it."""
        circuit = QuantumCircuit(2, 2)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.measure([0, 1], [0, 1])

        module_no_transpile = qiskit_to_qir(circuit, transpile=False)
        module_transpile = qiskit_to_qir(circuit, transpile=True)

        ops_no = _gate_ops(module_no_transpile)
        ops_yes = _gate_ops(module_transpile)

        # Both should have the same gate types
        no_names = [l.split("qis__")[1].split("__")[0] for l in ops_no]
        yes_names = [l.split("qis__")[1].split("__")[0] for l in ops_yes]
        assert set(no_names) == set(yes_names)

    def test_ecr_without_transpile_uses_decomposition(self):
        """ECR without transpile should still work via composite decomposition."""
        circuit = QuantumCircuit(2)
        circuit.ecr(0, 1)

        # Should work because ECR has a definition (decomposition)
        module = qiskit_to_qir(circuit, transpile=False)
        ops = _gate_ops(module)
        assert len(ops) > 0

    def test_unsupported_gate_no_definition_without_transpile(self):
        """Gate with no decomposition and transpile=False should raise."""

        class BadGate(Gate):
            def __init__(self):
                super().__init__("bad_gate", 1, [])

        circuit = QuantumCircuit(1)
        circuit.append(BadGate(), [0])

        with pytest.raises(QiskitConversionError, match="not supported"):
            qiskit_to_qir(circuit, transpile=False)

    def test_circuit_with_barrier_and_transpile(self):
        """Barriers should be preserved through transpilation."""
        circuit = QuantumCircuit(2)
        circuit.h(0)
        circuit.barrier()
        circuit.ecr(0, 1)

        module = qiskit_to_qir(circuit, transpile=True, emit_barrier_calls=True)
        body = _get_body(module)
        assert any("barrier" in l for l in body)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge case tests."""

    def test_single_gate_circuit(self):
        """Minimal circuit with exactly one gate."""
        circuit = QuantumCircuit(1)
        circuit.h(0)
        module = qiskit_to_qir(circuit)
        ops = _gate_ops(module)
        assert len(ops) == 1

    def test_measurement_only_circuit(self):
        """Circuit with only measurements."""
        circuit = QuantumCircuit(1, 1)
        circuit.measure(0, 0)
        module = qiskit_to_qir(circuit)
        ops = _gate_ops(module)
        assert len(ops) == 1
        assert "mz" in ops[0]

    def test_reset_then_gate(self):
        """Reset followed by a gate."""
        circuit = QuantumCircuit(1)
        circuit.reset(0)
        circuit.h(0)
        module = qiskit_to_qir(circuit)
        ops = _gate_ops(module)
        assert len(ops) == 2
        assert "reset" in ops[0]
        assert "h" in ops[1]

    def test_many_identity_gates(self):
        """Multiple identity gates should all be no-ops."""
        circuit = QuantumCircuit(1)
        circuit.id(0)
        circuit.id(0)
        circuit.id(0)
        circuit.h(0)
        module = qiskit_to_qir(circuit)
        ops = _gate_ops(module)
        assert len(ops) == 1
        assert "h" in ops[0]

    def test_all_runtime_options_disabled(self):
        """No init, no output recording, no barrier emission."""
        circuit = QuantumCircuit(2, 2)
        circuit.h(0)
        circuit.barrier()
        circuit.cx(0, 1)
        circuit.measure([0, 1], [0, 1])

        module = qiskit_to_qir(
            circuit, initialize_runtime=False, record_output=False, emit_barrier_calls=False
        )
        body = _get_body(module)

        assert not any("rt__initialize" in l for l in body)
        assert not any("array_record_output" in l for l in body)
        assert not any("result_record_output" in l for l in body)
        assert not any("barrier" in l for l in body)

    def test_circuit_with_no_classical_bits(self):
        """Circuit without classical bits should have no measurement output."""
        circuit = QuantumCircuit(2)
        circuit.h(0)
        circuit.cx(0, 1)
        module = qiskit_to_qir(circuit)
        func = next(filter(is_entry_point, module.functions))
        assert required_num_results(func) == 0


# ---------------------------------------------------------------------------
# Random circuit tests
# ---------------------------------------------------------------------------


class TestRandomCircuits:
    """Test conversion of randomly generated Qiskit circuits."""

    @pytest.mark.parametrize("seed", range(10))
    def test_random_circuit_with_transpile(self, seed):
        """Generate a random circuit and convert to QIR using transpile=True.

        Random circuits may contain gates outside the supported set,
        so transpilation is used to decompose them first.
        """
        num_qubits = (seed % 4) + 2  # 2..5 qubits
        depth = (seed % 3) + 2  # 2..4 depth

        circuit = random_circuit(num_qubits, depth, seed=seed, measure=True)

        module = qiskit_to_qir(circuit, transpile=True)

        func = next(filter(is_entry_point, module.functions))
        assert required_num_qubits(func) == num_qubits
        assert required_num_results(func) == num_qubits

        ops = _gate_ops(module)
        assert len(ops) > 0

        ir = str(module)
        assert len(ir) > 0
