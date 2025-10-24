# # Copyright 2025 qBraid
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #     http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.

# """
# Test functions that decompose unsupported Cirq gates before conversion to QIR.

# """

# import cirq
# import numpy as np
# from qbraid.interface import circuits_allclose

# from qbraid_qir.cirq.passes import _decompose_unsupported_gates


# def test_only_supported_gates():
#     qubits = cirq.LineQubit.range(2)
#     circuit = cirq.Circuit(cirq.H(qubits[0]), cirq.CNOT(qubits[0], qubits[1]))
#     decomposed_circuit = _decompose_unsupported_gates(circuit)
#     assert decomposed_circuit == circuit
#     assert circuits_allclose(decomposed_circuit, circuit)


# def test_contains_unsupported_gates():
#     qubits = cirq.LineQubit.range(2)
#     circuit = cirq.Circuit(
#         cirq.ops.ISwapPowGate(exponent=np.pi).on(*qubits),
#     )
#     decomposed_circuit = _decompose_unsupported_gates(circuit)
#     assert decomposed_circuit != circuit
#     assert circuits_allclose(decomposed_circuit, circuit)


# def test_empty_circuit():
#     circuit = cirq.Circuit()
#     decomposed_circuit = _decompose_unsupported_gates(circuit)
#     assert decomposed_circuit == circuit
#     assert circuits_allclose(decomposed_circuit, circuit)


# def test_custom_gate():
#     class CustomGate(cirq.Gate):  # pylint: disable=abstract-method
#         def _num_qubits_(self):
#             return 1

#         def _decompose_(self, qubits):
#             yield cirq.X(qubits[0])

#     custom_gate = CustomGate()
#     qubit = cirq.LineQubit(0)
#     circuit = cirq.Circuit(custom_gate.on(qubit))
#     decomposed_circuit = _decompose_unsupported_gates(circuit)
#     assert decomposed_circuit != circuit
#     assert (
#         any(isinstance(op.gate, CustomGate) for moment in decomposed_circuit for op in moment)
#         is False
#     )
#     assert circuits_allclose(decomposed_circuit, circuit)


# def test_multiple_decomposes():
#     class CustomGate(cirq.Gate):  # pylint: disable=abstract-method
#         def _num_qubits_(self):
#             return 1

#         def _decompose_(self, qubits):
#             class InnerCustomGate(cirq.Gate):  # pylint: disable=abstract-method
#                 def _num_qubits_(self):
#                     return 1

#                 def _decompose_(self, qubits):
#                     yield cirq.X(qubits[0])

#             inner_custom_gate = InnerCustomGate()
#             yield inner_custom_gate(qubits[0])

#     custom_gate = CustomGate()
#     qubit = cirq.LineQubit(0)
#     circuit = cirq.Circuit(custom_gate.on(qubit))
#     decomposed_circuit = _decompose_unsupported_gates(circuit)
#     assert decomposed_circuit != circuit
#     assert (
#         any(isinstance(op.gate, CustomGate) for moment in decomposed_circuit for op in moment)
#         is False
#     )
#     assert circuits_allclose(decomposed_circuit, circuit)
