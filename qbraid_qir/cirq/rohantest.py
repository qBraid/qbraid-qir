import cirq
import pyqir
import numpy as np
from qbraid_qir.cirq.elements import CirqModule, generate_module_id
from qbraid_qir.cirq.visitor import BasicQisVisitor
from qbraid_qir.exceptions import QirConversionError
from qbraid_qir.cirq.opsets import CIRQ_GATES, get_callable_from_pyqir_name
from qbraid_qir.cirq.convert import cirq_to_qir, generate_module_id



circuit = cirq.Circuit()
qubits = cirq.LineQubit.range(3)
# write a ghz gate
circuit.append(cirq.H(qubits[0]))
circuit.append(cirq.CNOT(qubits[0], qubits[1]))
circuit.append(cirq.CNOT(qubits[1], qubits[2]))


converted = cirq_to_qir(circuit)
print(converted)