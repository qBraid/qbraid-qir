# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=too-many-arguments

"""
Module defining Qasm3 Converter elements.

"""

import uuid

from pyqasm.elements import Qasm3Module
from pyqir import Module as qirModule


def generate_module_id() -> str:
    """
    Generates a QIR module ID from a given openqasm3 program.

    """
    # TODO: Consider a better approach of generating a unique identifier.
    generated_id = uuid.uuid1()
    return f"program-{generated_id}"


class QasmQIRModule:
    """
    A module representing an openqasm3 quantum program using QIR.

    Args:
        name (str): Name of the module.
        qasm_module (pyqasm.elements.Qasm3Module): The pyqasm qasm3 module.
        llvm_module (pyqir.Module): The QIR module.
    """

    def __init__(
        self,
        name: str,
        qasm_module: Qasm3Module,
        llvm_module: qirModule,
    ):
        self._name = name
        self._llvm_module = llvm_module
        self._qasm_program = qasm_module

    @property
    def name(self) -> str:
        """Returns the name of the module."""
        return self._name

    @property
    def llvm_module(self) -> qirModule:
        """Returns the QIR Module instance."""
        return self._llvm_module

    @property
    def qasm_program(self) -> Qasm3Module:
        """Returns the QASM3 program."""
        return self._qasm_program

    def accept(self, visitor):
        visitor.visit_qasm3_module(self)
        statements = self.qasm_program.unrolled_ast.statements
        for statement in statements:
            visitor.visit_statement(statement)
        visitor.record_output(self)
        visitor.finalize()
