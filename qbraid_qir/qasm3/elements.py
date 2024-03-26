# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining Qasm3 Converter elements.

"""

import uuid
from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import List, Optional, Tuple

from openqasm3.ast import BitType, ClassicalDeclaration, Program, QubitDeclaration, Statement
from pyqir import Context as qirContext
from pyqir import Module


def generate_module_id() -> str:
    """
    Generates a QIR module ID from a given openqasm3 program.
    """

    # TODO: Consider a better approach of generating a unique identifier.
    generated_id = uuid.uuid1()
    return f"circuit-{generated_id}"


class Scope(Enum):
    """
    Enum for the different scopes in QIR.
    """

    GLOBAL = "global"
    GATE = "gate"
    FUNCTION = "function"


class Context(Enum):
    """
    Enum for the different contexts in QIR.
    """

    GLOBAL = "global"
    IF = "if"
    LOOP = "loop"


class _ProgramElement(metaclass=ABCMeta):
    @classmethod
    def from_element_list(cls, elements):
        return [cls(elem) for elem in elements]

    @abstractmethod
    def accept(self, visitor):
        pass


class _Register(_ProgramElement):
    def __init__(self, register: Tuple[str, Optional[int]], is_qubit: bool = True):
        self._register = register
        self._is_qubit = is_qubit

    def accept(self, visitor):
        visitor.visit_register(self._register, self._is_qubit)

    def __str__(self) -> str:
        return f"Register({self._register}, is_qubit = {self._is_qubit})"


class _Statement(_ProgramElement):
    def __init__(self, statement: Statement):
        self._statement = statement

    def accept(self, visitor):
        visitor.visit_statement(self._statement)

    def __str__(self) -> str:
        return f"Statement({self._statement})"


class Qasm3Module:
    """
    A module representing an openqasm3 quantum program using QIR.

    Args:
        name (str): Name of the module.
        module (Module): QIR Module instance.
        num_qubits (int): Number of qubits in the circuit.
        num_clbits (int): Number of classical bits in the circuit.
        elements (List[Statement]): List of openqasm3 Statements.
    """

    def __init__(self, name: str, module: Module, num_qubits: int, num_clbits: int, elements):
        self._name = name
        self._module = module
        self._num_qubits = num_qubits
        self._num_clbits = num_clbits
        self._elements = elements

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
    def from_program(cls, program: Program, module: Optional[Module] = None):
        """
        Class method. Construct a Qasm3Module from a given openqasm3.ast.Program object
        and an optional QIR Module.
        """
        elements: List[Statement] = []

        num_qubits = 0
        num_clbits = 0
        for statement in program.statements:
            if isinstance(statement, QubitDeclaration):
                name = statement.qubit.name
                size = None if statement.size is None else statement.size.value
                num_qubits += 1 if size is None else size
                elements.append(_Register((name, size), True))

            elif isinstance(statement, ClassicalDeclaration) and isinstance(
                statement.type, BitType
            ):
                name = statement.identifier.name
                size = None if statement.type.size is None else statement.type.size.value
                num_clbits += 1 if size is None else size
                elements.append(_Register((name, size), False))
            else:
                elements.append(_Statement(statement))

        if module is None:
            module = Module(qirContext(), generate_module_id(program))

        # for element in elements:
        #     print(element,"\n")
        return cls(
            name="main",
            module=module,
            num_qubits=num_qubits,
            num_clbits=num_clbits,
            elements=elements,
        )

    def accept(self, visitor):
        visitor.visit_qasm3_module(self)
        for element in self._elements:
            element.accept(visitor)
        visitor.record_output(self)
        visitor.finalize()
