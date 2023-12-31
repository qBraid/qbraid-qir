import cirq
import pyqir
import numpy as np
from qbraid_qir.cirq.elements import CirqModule, generate_module_id
from qbraid_qir.cirq.visitor import BasicQisVisitor
from qbraid_qir.exceptions import QirConversionError
from qbraid_qir.cirq.convert import cirq_to_qir, generate_module_id
from pyqir import SimpleModule, BasicQisBuilder


def cirq_bell() -> cirq.Circuit:
    """Returns a Cirq bell circuit with measurement over two qubits."""
    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1), cirq.measure(q0, q1))
    # circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1))
    return circuit

def pyqir_bell() -> SimpleModule:
    """Returns a QIR bell circuit with measurement over two qubits."""
    bell = SimpleModule("test_qir_bell", num_qubits=2, num_results=2)
    qis = BasicQisBuilder(bell.builder)

    qis.h(bell.qubits[0])
    qis.cx(bell.qubits[0], bell.qubits[1])
    qis.mz(bell.qubits[0], bell.results[0])
    qis.mz(bell.qubits[1], bell.results[1])

    return bell

circuit = cirq_bell()
pyqir_bell = pyqir_bell()

converted = cirq_to_qir(circuit, "test_qir_bell")
print(converted)
# print(pyqir_bell.ir())