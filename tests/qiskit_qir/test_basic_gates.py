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
Unit tests for basic Qiskit gate conversions to QIR with sequential equivalence checks.

"""

import math

import pytest
from pyqir import is_entry_point, required_num_qubits, required_num_results
from qiskit import QuantumCircuit

from qbraid_qir._pyqir_compat import pyqir_uses_opaque_pointers
from qbraid_qir.qiskit import qiskit_to_qir

_OPAQUE = pyqir_uses_opaque_pointers()


def _get_body(module):
    """Extract the entry point body as a list of stripped instruction lines."""
    func = next(filter(is_entry_point, module.functions))
    lines = str(func).splitlines()[2:-1]
    return [line.strip() for line in lines]


def _get_entry_point(module):
    """Get the entry point function from a module."""
    return next(filter(is_entry_point, module.functions))


def _qubit_ref(n):
    """Return the QIR qubit reference string for qubit index *n*."""
    if _OPAQUE:
        return "ptr null" if n == 0 else f"ptr inttoptr (i64 {n} to ptr)"
    return "%Qubit* null" if n == 0 else f"%Qubit* inttoptr (i64 {n} to %Qubit*)"


def _result_ref(n):
    """Return the QIR result reference string for result index *n*."""
    if _OPAQUE:
        return "ptr null" if n == 0 else f"ptr inttoptr (i64 {n} to ptr)"
    return "%Result* null" if n == 0 else f"%Result* inttoptr (i64 {n} to %Result*)"


def _op_call(name, qubit=0):
    """Generate expected single-qubit gate call string."""
    return f"call void @__quantum__qis__{name}__body({_qubit_ref(qubit)})"


def _adj_call(name, qubit=0):
    """Generate expected adjoint gate call string."""
    return f"call void @__quantum__qis__{name}__adj({_qubit_ref(qubit)})"


def _rot_call(name, angle, qubit=0):
    """Generate expected rotation gate call string."""
    return f"call void @__quantum__qis__{name}__body(double {angle:#e}, {_qubit_ref(qubit)})"


def _two_qubit_call(name, qb1=0, qb2=1):
    """Generate expected two-qubit gate call string."""
    return f"call void @__quantum__qis__{name}__body({_qubit_ref(qb1)}, {_qubit_ref(qb2)})"


def _three_qubit_call(name, qb1=0, qb2=1, qb3=2):
    """Generate expected three-qubit gate call string."""
    qubits = ", ".join(_qubit_ref(q) for q in [qb1, qb2, qb3])
    return f"call void @__quantum__qis__{name}__body({qubits})"


def _mz_call(qubit=0, result=0):
    """Generate expected measurement call string."""
    return f"call void @__quantum__qis__mz__body({_qubit_ref(qubit)}, {_result_ref(result)})"


def _assert_body_ops(module, expected_ops):
    """Assert that the QIR body contains exactly the expected operations in order.

    Args:
        module: PyQIR Module.
        expected_ops: List of expected QIR instruction strings.
    """
    body = _get_body(module)

    # Filter to only "call" lines and "ret" for comparison
    gate_lines = [l for l in body if l.startswith("call void @__quantum__qis__")]

    expected_str = "\n  ".join(expected_ops)
    actual_str = "\n  ".join(gate_lines)
    assert len(gate_lines) == len(expected_ops), (
        f"Expected {len(expected_ops)} gate ops, got {len(gate_lines)}.\n"
        f"Expected:\n  {expected_str}\n"
        f"Got:\n  {actual_str}"
    )
    for i, (actual, expected) in enumerate(zip(gate_lines, expected_ops)):
        assert (
            actual == expected
        ), f"Op mismatch at index {i}:\n  expected: {expected}\n  actual:   {actual}"


# ---------------------------------------------------------------------------
# Single-qubit gates
# ---------------------------------------------------------------------------


class TestSingleQubitGates:
    """Tests for single qubit gate conversions with sequential equivalence."""

    # Gate name maps to itself for single-qubit gates
    GATES = {"h", "x", "y", "z", "s", "t", "reset"}

    @pytest.mark.parametrize("gate_name", GATES)
    def test_single_qubit_gate(self, gate_name):
        circuit = QuantumCircuit(1)
        getattr(circuit, gate_name)(0)

        module = qiskit_to_qir(circuit)
        func = _get_entry_point(module)
        assert required_num_qubits(func) == 1
        assert required_num_results(func) == 0

        _assert_body_ops(module, [_op_call(gate_name, 0)])

    @pytest.mark.parametrize("gate_name", GATES)
    def test_single_qubit_gate_on_qubit_1(self, gate_name):
        """Test gate applied to qubit index 1 (not 0)."""
        circuit = QuantumCircuit(2)
        getattr(circuit, gate_name)(1)

        module = qiskit_to_qir(circuit)
        _assert_body_ops(module, [_op_call(gate_name, 1)])


class TestAdjointGates:
    """Tests for adjoint gate conversions with sequential equivalence."""

    GATES = {"sdg": "s", "tdg": "t"}

    @pytest.mark.parametrize("gate_name,qir_name", GATES.items())
    def test_adjoint_gate(self, gate_name, qir_name):
        circuit = QuantumCircuit(1)
        getattr(circuit, gate_name)(0)

        module = qiskit_to_qir(circuit)
        func = _get_entry_point(module)
        assert required_num_qubits(func) == 1
        assert required_num_results(func) == 0

        _assert_body_ops(module, [_adj_call(qir_name, 0)])


class TestIdentityGate:
    """Tests for identity gate (should be a no-op)."""

    def test_identity_is_noop(self):
        circuit = QuantumCircuit(1)
        circuit.id(0)

        module = qiskit_to_qir(circuit)
        _assert_body_ops(module, [])

    def test_identity_between_gates(self):
        """Identity between real gates should not affect the sequence."""
        circuit = QuantumCircuit(1)
        circuit.h(0)
        circuit.id(0)
        circuit.x(0)

        module = qiskit_to_qir(circuit)
        _assert_body_ops(module, [_op_call("h", 0), _op_call("x", 0)])


# ---------------------------------------------------------------------------
# Rotation gates
# ---------------------------------------------------------------------------


class TestRotationGates:
    """Tests for rotation gate conversions with sequential equivalence."""

    @pytest.mark.parametrize("gate_name", ["rx", "ry", "rz"])
    def test_rotation_gate(self, gate_name):
        circuit = QuantumCircuit(1)
        getattr(circuit, gate_name)(0.5, 0)

        module = qiskit_to_qir(circuit)
        func = _get_entry_point(module)
        assert required_num_qubits(func) == 1
        assert required_num_results(func) == 0

        _assert_body_ops(module, [_rot_call(gate_name, 0.5, 0)])

    @pytest.mark.parametrize("angle", [0.0, math.pi, 2 * math.pi, -math.pi / 4])
    def test_rotation_edge_angles(self, angle):
        """Test rotation gates with edge-case angles."""
        circuit = QuantumCircuit(1)
        circuit.rx(angle, 0)

        module = qiskit_to_qir(circuit)
        body = _get_body(module)
        gate_ops = [l for l in body if "qis__" in l]
        assert len(gate_ops) == 1
        assert "qis__rx__body" in gate_ops[0]

    def test_rotation_sequence(self):
        """Test a sequence of different rotation gates on the same qubit."""
        circuit = QuantumCircuit(1)
        circuit.rx(0.5, 0)
        circuit.ry(1.0, 0)
        circuit.rz(1.5, 0)

        module = qiskit_to_qir(circuit)
        _assert_body_ops(
            module,
            [
                _rot_call("rx", 0.5, 0),
                _rot_call("ry", 1.0, 0),
                _rot_call("rz", 1.5, 0),
            ],
        )


# ---------------------------------------------------------------------------
# Two-qubit gates
# ---------------------------------------------------------------------------


class TestTwoQubitGates:
    """Tests for two qubit gate conversions with sequential equivalence."""

    GATES = {"cx": "cnot", "cz": "cz", "swap": "swap"}

    @pytest.mark.parametrize("gate_name,qir_name", GATES.items())
    def test_two_qubit_gate(self, gate_name, qir_name):
        circuit = QuantumCircuit(2)
        getattr(circuit, gate_name)(0, 1)

        module = qiskit_to_qir(circuit)
        func = _get_entry_point(module)
        assert required_num_qubits(func) == 2
        assert required_num_results(func) == 0

        _assert_body_ops(module, [_two_qubit_call(qir_name, 0, 1)])

    @pytest.mark.parametrize("gate_name,qir_name", GATES.items())
    def test_two_qubit_gate_reversed(self, gate_name, qir_name):
        """Test two-qubit gate with reversed qubit order."""
        circuit = QuantumCircuit(2)
        getattr(circuit, gate_name)(1, 0)

        module = qiskit_to_qir(circuit)
        _assert_body_ops(module, [_two_qubit_call(qir_name, 1, 0)])

    def test_two_qubit_sequence(self):
        """All two-qubit gates in sequence."""
        circuit = QuantumCircuit(2)
        circuit.cx(0, 1)
        circuit.cz(0, 1)
        circuit.swap(0, 1)

        module = qiskit_to_qir(circuit)
        _assert_body_ops(
            module,
            [
                _two_qubit_call("cnot", 0, 1),
                _two_qubit_call("cz", 0, 1),
                _two_qubit_call("swap", 0, 1),
            ],
        )


# ---------------------------------------------------------------------------
# Three-qubit gates
# ---------------------------------------------------------------------------


class TestThreeQubitGates:
    """Tests for three qubit gate conversions with sequential equivalence."""

    def test_ccx_gate(self):
        circuit = QuantumCircuit(3)
        circuit.ccx(0, 1, 2)

        module = qiskit_to_qir(circuit)
        func = _get_entry_point(module)
        assert required_num_qubits(func) == 3
        assert required_num_results(func) == 0

        _assert_body_ops(module, [_three_qubit_call("ccx", 0, 1, 2)])

    def test_ccx_different_qubits(self):
        """CCX with non-sequential qubit ordering."""
        circuit = QuantumCircuit(4)
        circuit.ccx(3, 1, 0)

        module = qiskit_to_qir(circuit)
        _assert_body_ops(module, [_three_qubit_call("ccx", 3, 1, 0)])


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------


class TestMeasurement:
    """Tests for measurement operations with sequential equivalence."""

    def test_single_measurement(self):
        circuit = QuantumCircuit(1, 1)
        circuit.measure(0, 0)

        module = qiskit_to_qir(circuit)
        func = _get_entry_point(module)
        assert required_num_qubits(func) == 1
        assert required_num_results(func) == 1

        _assert_body_ops(module, [_mz_call(0, 0)])

    def test_multiple_measurements(self):
        circuit = QuantumCircuit(3, 3)
        circuit.measure([0, 1, 2], [0, 1, 2])

        module = qiskit_to_qir(circuit)
        func = _get_entry_point(module)
        assert required_num_qubits(func) == 3
        assert required_num_results(func) == 3

        _assert_body_ops(
            module,
            [
                _mz_call(0, 0),
                _mz_call(1, 1),
                _mz_call(2, 2),
            ],
        )

    def test_gates_then_measurement(self):
        """H gate then measurement — verify ordering."""
        circuit = QuantumCircuit(1, 1)
        circuit.h(0)
        circuit.measure(0, 0)

        module = qiskit_to_qir(circuit)
        _assert_body_ops(module, [_op_call("h", 0), _mz_call(0, 0)])


# ---------------------------------------------------------------------------
# Output recording
# ---------------------------------------------------------------------------


class TestOutputRecording:
    """Tests for output recording functionality."""

    def test_output_recording_single_register(self):
        circuit = QuantumCircuit(2, 2)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.measure([0, 1], [0, 1])

        module = qiskit_to_qir(circuit)
        body = _get_body(module)

        rt_calls = [l for l in body if "__quantum__rt__" in l]
        # init + array_record_output + 2 result_record_output
        assert any("array_record_output" in l for l in rt_calls)
        assert sum("result_record_output" in l for l in rt_calls) == 2

    def test_output_recording_disabled(self):
        circuit = QuantumCircuit(2, 2)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.measure([0, 1], [0, 1])

        module = qiskit_to_qir(circuit, record_output=False)
        ir = str(module)
        assert "__quantum__rt__array_record_output" not in ir
        assert "__quantum__rt__result_record_output" not in ir


# ---------------------------------------------------------------------------
# Barrier and delay
# ---------------------------------------------------------------------------


class TestBarrierAndDelay:
    """Tests for barrier and delay instruction handling."""

    def test_barrier_not_emitted_by_default(self):
        circuit = QuantumCircuit(2)
        circuit.h(0)
        circuit.barrier()
        circuit.cx(0, 1)

        module = qiskit_to_qir(circuit)
        _assert_body_ops(
            module,
            [
                _op_call("h", 0),
                _two_qubit_call("cnot", 0, 1),
            ],
        )

    def test_barrier_emitted_when_enabled(self):
        circuit = QuantumCircuit(2)
        circuit.h(0)
        circuit.barrier()
        circuit.cx(0, 1)

        module = qiskit_to_qir(circuit, emit_barrier_calls=True)
        body = _get_body(module)
        gate_and_barrier = [l for l in body if l.startswith("call void @__quantum__qis__")]

        assert len(gate_and_barrier) == 3
        assert "barrier" in gate_and_barrier[1]

    def test_delay_ignored(self):
        circuit = QuantumCircuit(1)
        circuit.h(0)
        circuit.delay(100, 0, "ns")
        circuit.x(0)

        module = qiskit_to_qir(circuit)
        _assert_body_ops(module, [_op_call("h", 0), _op_call("x", 0)])


# ---------------------------------------------------------------------------
# Multi-gate sequences (sequential equivalence)
# ---------------------------------------------------------------------------


class TestMultiGateSequences:
    """Tests that verify exact gate ordering in multi-gate circuits."""

    def test_bell_state_preparation(self):
        """H then CX — canonical Bell state prep."""
        circuit = QuantumCircuit(2)
        circuit.h(0)
        circuit.cx(0, 1)

        module = qiskit_to_qir(circuit)
        _assert_body_ops(
            module,
            [
                _op_call("h", 0),
                _two_qubit_call("cnot", 0, 1),
            ],
        )

    def test_all_single_qubit_gates_sequence(self):
        """All single-qubit gates in a defined order."""
        circuit = QuantumCircuit(1)
        circuit.h(0)
        circuit.x(0)
        circuit.y(0)
        circuit.z(0)
        circuit.s(0)
        circuit.sdg(0)
        circuit.t(0)
        circuit.tdg(0)

        module = qiskit_to_qir(circuit)
        _assert_body_ops(
            module,
            [
                _op_call("h", 0),
                _op_call("x", 0),
                _op_call("y", 0),
                _op_call("z", 0),
                _op_call("s", 0),
                _adj_call("s", 0),
                _op_call("t", 0),
                _adj_call("t", 0),
            ],
        )

    def test_mixed_single_and_two_qubit(self):
        """Interleaved single and two-qubit gates."""
        circuit = QuantumCircuit(3)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.h(2)
        circuit.cz(1, 2)

        module = qiskit_to_qir(circuit)
        _assert_body_ops(
            module,
            [
                _op_call("h", 0),
                _two_qubit_call("cnot", 0, 1),
                _op_call("h", 2),
                _two_qubit_call("cz", 1, 2),
            ],
        )

    def test_gates_interleaved_with_measurements(self):
        """Gates and measurements interleaved."""
        circuit = QuantumCircuit(2, 2)
        circuit.h(0)
        circuit.measure(0, 0)
        circuit.h(1)
        circuit.measure(1, 1)

        module = qiskit_to_qir(circuit)
        _assert_body_ops(
            module,
            [
                _op_call("h", 0),
                _mz_call(0, 0),
                _op_call("h", 1),
                _mz_call(1, 1),
            ],
        )
