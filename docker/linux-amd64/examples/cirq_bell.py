"""
Example of running a Cirq circuit on the QIR bytecode runner.

"""

import cirq
from qbraid.runtime import QirRunner

from qbraid_qir.cirq import cirq_to_qir

q0, q1 = cirq.LineQubit.range(2)
circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1), cirq.measure(q0, q1))

print(f"Cirq Circuit: \n{circuit}")

module = cirq_to_qir(circuit, name="bell")

sim = QirRunner()

print(f"\nRunning on: {repr(sim)}")

result = sim.run(module.bitcode, shots=10)

print(f"\nResult: {result}")
