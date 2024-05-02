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
from typing import Optional, Union

from openqasm3.ast import BitType, ClassicalDeclaration, Program, QubitDeclaration, Statement
from pyqir import Context as qirContext
from pyqir import Module


def generate_module_id() -> str:
    """
    Generates a QIR module ID from a given openqasm3 program.

    """
    # TODO: Consider a better approach of generating a unique identifier.
    generated_id = uuid.uuid1()
    return f"program-{generated_id}"


class Context(Enum):
    """
    Enum for the different contexts in QIR.

    """

    GLOBAL = "global"
    IF = "if"
    LOOP = "loop"
    FUNCTION = "function"


class InversionOp(Enum):
    NO_OP = 1
    INVERT_ROTATION = 2


class Variable:
    """
    Class representing an openqasm variable.

    Args:
        name (str): Name of the variable.
        base_type (Any): Base type of the variable.
        base_size (int): Base size of the variable.
        dims (List[int]): Dimensions of the variable.
        value (Optional[Union[int, float, list]]): Value of the variable.
        is_constant (bool): Flag indicating if the variable is constant.

    """

    def __init__(self, name, base_type, base_size, dims, value, is_constant=False):
        self.name = name
        self.base_type = base_type
        self.base_size = base_size
        self.dims = dims
        self.value = value
        self.is_constant = is_constant


class _ProgramElement(metaclass=ABCMeta):
    @classmethod
    def from_element_list(cls, elements):
        return [cls(elem) for elem in elements]

    @abstractmethod
    def accept(self, visitor):
        pass


class _Register(_ProgramElement):
    def __init__(self, register: Union[QubitDeclaration, ClassicalDeclaration]):
        self._register: Union[QubitDeclaration, ClassicalDeclaration] = register

    def accept(self, visitor):
        visitor.visit_register(self._register)

    def __str__(self) -> str:
        return f"Register({self._register})"


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

    # pylint: disable-next=too-many-arguments
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
        elements = []

        num_qubits = 0
        num_clbits = 0
        for statement in program.statements:
            if isinstance(statement, QubitDeclaration):
                size = 1 if statement.size is None else statement.size.value
                num_qubits += size
                elements.append(_Register(statement))

            elif isinstance(statement, ClassicalDeclaration) and isinstance(
                statement.type, BitType
            ):
                size = 1 if statement.type.size is None else statement.type.size.value
                num_clbits += size
                elements.append(_Register(statement))
                # as bit arrays are just 0 / 1 values, we can treat them as
                # classical variables too. Thus, need to add them to normal
                # statements too.
                elements.append(_Statement(statement))
            else:
                elements.append(_Statement(statement))

        if module is None:
            # pylint: disable-next=too-many-function-args
            module = Module(qirContext(), generate_module_id(program))

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
