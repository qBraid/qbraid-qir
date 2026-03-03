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

# This module is derived from microsoft/qiskit-qir (MIT License).
# Original code: Copyright (c) Microsoft Corporation.
# See NOTICE.md for attribution details.

"""
Module defining Qiskit circuit elements for QIR conversion.

"""

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Optional, Union

from pyqir import Module
from qiskit import ClassicalRegister, QuantumRegister
from qiskit.circuit import Clbit, Qubit
from qiskit.circuit.quantumcircuit import QuantumCircuit

if TYPE_CHECKING:
    from qiskit.circuit.instruction import Instruction


class _QuantumCircuitElement(metaclass=ABCMeta):
    """Abstract base class for quantum circuit elements."""

    @classmethod
    def from_element_list(cls, elements):
        """Create a list of circuit elements from a list of raw elements."""
        return [cls(elem) for elem in elements]

    @abstractmethod
    def accept(self, visitor):
        """Accept a visitor to process this element."""


class _Register(_QuantumCircuitElement):
    """Wrapper for a Qiskit register element."""

    def __init__(self, register: Union[QuantumRegister, ClassicalRegister]):
        self._register: Union[QuantumRegister, ClassicalRegister] = register

    def accept(self, visitor):
        """Accept a visitor to process this register."""
        visitor.visit_register(self._register)


class _Instruction(_QuantumCircuitElement):
    """Wrapper for a Qiskit instruction element."""

    def __init__(
        self,
        instruction: "Instruction",
        qargs: tuple[Qubit, ...],
        cargs: tuple[Clbit, ...],
    ):
        self._instruction: "Instruction" = instruction
        self._qargs = qargs
        self._cargs = cargs

    def accept(self, visitor):
        """Accept a visitor to process this instruction."""
        visitor.visit_instruction(self._instruction, self._qargs, self._cargs)


def generate_module_id(circuit: QuantumCircuit) -> str:
    """Generate a unique module ID for a circuit."""
    return circuit.name if circuit.name else "main"


class QiskitModule:
    """Represents a Qiskit quantum circuit prepared for QIR conversion.

    Attributes:
        circuit: The original Qiskit QuantumCircuit.
        name: The name of the module.
        module: The PyQIR Module being built.
        num_qubits: Number of qubits in the circuit.
        num_clbits: Number of classical bits in the circuit.
        reg_sizes: List of sizes for each classical register.
    """

    def __init__(
        self,
        circuit: QuantumCircuit,
        name: str,
        module: Module,
        num_qubits: int,
        num_clbits: int,
        reg_sizes: list[int],
        elements: list[_QuantumCircuitElement],
    ):
        self._circuit = circuit
        self._name = name
        self._module = module
        self._elements = elements
        self._num_qubits = num_qubits
        self._num_clbits = num_clbits
        self.reg_sizes = reg_sizes

    @property
    def circuit(self) -> QuantumCircuit:
        """Return the underlying Qiskit circuit."""
        return self._circuit

    @property
    def name(self) -> str:
        """Return the module name."""
        return self._name

    @property
    def module(self) -> Module:
        """Return the PyQIR module."""
        return self._module

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits."""
        return self._num_qubits

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits."""
        return self._num_clbits

    @classmethod
    def from_circuit(
        cls, circuit: QuantumCircuit, module: Optional[Module] = None
    ) -> "QiskitModule":
        """Create a new QiskitModule from a Qiskit QuantumCircuit.

        Args:
            circuit: The Qiskit QuantumCircuit to convert.
            module: An optional existing PyQIR Module to use.

        Returns:
            A new QiskitModule instance.
        """
        elements: list[_QuantumCircuitElement] = []
        reg_sizes = [len(creg) for creg in circuit.cregs]

        # Add registers
        elements.extend(_Register.from_element_list(circuit.qregs))
        elements.extend(_Register.from_element_list(circuit.cregs))

        # Add instructions (updated for qiskit 2.x)
        for circuit_instruction in circuit.data:
            instruction = circuit_instruction.operation
            qargs = circuit_instruction.qubits
            cargs = circuit_instruction.clbits
            elements.append(_Instruction(instruction, qargs, cargs))

        name = generate_module_id(circuit)

        return cls(
            circuit=circuit,
            name=name,
            module=module,
            num_qubits=circuit.num_qubits,
            num_clbits=circuit.num_clbits,
            reg_sizes=reg_sizes,
            elements=elements,
        )

    def accept(self, visitor):
        """Accept a visitor to process this module.

        Args:
            visitor: The visitor to accept.
        """
        visitor.visit_qiskit_module(self)
        for element in self._elements:
            element.accept(visitor)
        visitor.record_output(self)
        visitor.finalize()
