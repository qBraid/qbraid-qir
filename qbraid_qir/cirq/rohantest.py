import cirq
from qbraid_qir.cirq.convert import cirq_to_qir
from qbraid_qir.cirq.passes import _decompose_gate_op, _decompose_unsupported_gates, preprocess_circuit

qubits = [cirq.LineQubit(i) for i in range(3)]
circuit = cirq.Circuit()

circuit.append([cirq.H(qubits[0]), cirq.H(qubits[1])])

circuit.append(cirq.measure(qubits[0]))
circuit.append(cirq.measure(qubits[1]))

sub_operation = cirq.Z(qubits[2])

# This X gate on qubit 2 will only be executed if the measurement on 0th qubit is True
controlled_op = cirq.ClassicallyControlledOperation(sub_operation, conditions=["0"])

circuit.append(controlled_op)
print(circuit)

new_circuit = cirq_to_qir(circuit)
print(new_circuit)

# # Extract sub-operation from controlled operation
# regular_op = controlled_op.without_classical_controls()

# print(regular_op)  # X(q(2))
# print(regular_op.gate)  # X