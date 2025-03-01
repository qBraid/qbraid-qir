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
Module defining Cirq LLVM Module elements.
"""

import hashlib
from abc import ABCMeta, abstractmethod
from typing import Optional

import cirq
from pyqir import Context, Module


def generate_module_id(circuit: cirq.Circuit) -> str:
    """
    Generates a QIR module ID from a given Cirq circuit.

    This function serializes the Cirq circuit into a JSON string, computes its SHA-256 hash,
    and converts the hash into an alphanumeric string. The final name is a truncated version,
    prefixed with 'circuit-', to form a concise, semi-unique identifier.

    Args:
        circuit (cirq.Circuit): The Cirq circuit for which a unique name is to be generated.

    Returns:
        str: Alphanumeric module ID for the Cirq circuit

    """
    serialized_circuit = cirq.to_json(circuit)
    hash_object = hashlib.sha256(serialized_circuit.encode())
    hash_hex = hash_object.hexdigest()
    alphanumeric_hash = "".join(filter(str.isalnum, hash_hex))
    truncated_hash = alphanumeric_hash[:7]
    return f"circuit-{truncated_hash}"


class _CircuitElement(metaclass=ABCMeta):
    @abstractmethod
    def accept(self, visitor):
        pass


class _Register(_CircuitElement):
    def __init__(self, register: list[cirq.Qid]):
        self._register = register

    def accept(self, visitor):
        visitor.visit_register(self._register)


class _Operation(_CircuitElement):
    def __init__(self, operation: cirq.Operation):
        self._operation = operation

    def accept(self, visitor):
        visitor.visit_operation(self._operation)


class CirqModule:
    """
    A module representing a quantum circuit in Cirq using QIR.

    This class encapsulates a quantum circuit from Cirq and translates it into QIR format,
    maintaining information about quantum operations, qubits, and classical bits. It provides
    methods to interact with the underlying QIR module and circuit elements.

    Args:
        name (str): Name of the module.
        module (Module): QIR Module instance.
        num_qubits (int): Number of qubits in the circuit.
        elements (list[_CircuitElement]): list of circuit elements.

    Example:
        >>> circuit = cirq.Circuit()
        >>> cirq_module = CirqModule.from_circuit(circuit)
        >>> print(cirq_module.num_qubits)
    """

    def __init__(
        self,
        name: str,
        module: Module,
        num_qubits: int,
        elements: list[_CircuitElement],
    ):
        self._name = name
        self._module = module
        self._elements = elements
        self._num_qubits = num_qubits
        self._num_clbits = num_qubits  # create one classical bit for each qubit

    @property
    def name(self) -> str:
        """Returns the name of the module."""
        return self._name

    @property
    def module(self) -> Module:
        """Returns the QIR Module instance."""
        return self._module

    @property
    def num_qubits(self) -> int:
        """Returns the number of qubits in the circuit."""
        return self._num_qubits

    @property
    def num_clbits(self) -> int:
        """Returns the number of classical bits in the circuit."""
        return self._num_clbits

    @classmethod
    def from_circuit(cls, circuit: cirq.Circuit, module: Optional[Module] = None) -> "CirqModule":
        """Class method. Constructs a CirqModule from a given cirq.Circuit object
        and an optional QIR Module."""
        elements: list[_CircuitElement] = []

        # Register(s). Tentatively using cirq.Qid as input. Better approaches might exist tbd.
        elements.append(_Register(list(circuit.all_qubits())))

        # Operations
        for operation in circuit.all_operations():
            elements.append(_Operation(operation))

        if module is None:
            module = Module(Context(), generate_module_id(circuit))
        return cls(
            name="main",
            module=module,
            num_qubits=len(circuit.all_qubits()),
            elements=elements,
        )

    def accept(self, visitor):
        visitor.visit_cirq_module(self)
        for element in self._elements:
            element.accept(visitor)
        visitor.record_output(self)
        visitor.finalize()
