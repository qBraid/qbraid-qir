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

# pylint: disable=too-many-arguments

"""
Module defining Qasm3 Converter elements.

"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from ..profiles.abstract import QIRModule

if TYPE_CHECKING:
    import pyqir
    from pyqasm.modules import QasmModule


def generate_module_id() -> str:
    """
    Generates a QIR module ID from a given openqasm3 program.

    """
    # TODO: Consider a better approach of generating a unique identifier.
    generated_id = uuid.uuid1()
    return f"program-{generated_id}"


class QasmQIRModule(QIRModule):
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
        qasm_module: "QasmModule",
        llvm_module: pyqir.Module,
    ):
        super().__init__(program=qasm_module)
        self._name = name
        self._llvm_module = llvm_module
        self._qasm_program = qasm_module

    @property
    def name(self) -> str:
        """Returns the name of the module."""
        return self._name

    @property
    def llvm_module(self) -> pyqir.Module:
        """Returns the QIR Module instance."""
        return self._llvm_module

    @property
    def qasm_program(self) -> "QasmModule":
        """Returns the QASM3 program."""
        return self._qasm_program

    @property
    def num_qubits(self) -> int:
        return self.qasm_program.num_qubits

    @property
    def num_clbits(self) -> int:
        return self.qasm_program.num_clbits

    def accept(self, visitor):
        visitor.visit_qasm3_module(self)
        statements = self.qasm_program.unrolled_ast.statements
        for statement in statements:
            visitor.visit_statement(statement)
        visitor.record_output(self)
        visitor.finalize()
