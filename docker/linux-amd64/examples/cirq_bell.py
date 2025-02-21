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
