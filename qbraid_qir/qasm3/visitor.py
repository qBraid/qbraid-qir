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
Module defining Qasm3 Visitor.

"""
import logging
from abc import ABCMeta, abstractmethod

import pyqir
import pyqir._native
import pyqir.rt
from pyqir import BasicBlock, Builder, Constant, IntType, PointerType

from qbraid_qir.qasm3.elements import Qasm3Module

_log = logging.getLogger(name=__name__)


class CircuitElementVisitor(metaclass=ABCMeta):
    @abstractmethod
    def visit_register(self, register):
        pass

    @abstractmethod
    def visit_operation(self, operation):
        pass


class BasicQisVisitor(CircuitElementVisitor):
    """A visitor for QIS (Quantum Instruction Set) basic elements.

    This class is designed to traverse and interact with elements in a quantum circuit.

    Args:
        initialize_runtime (bool): If True, quantum runtime will be initialized. Defaults to True.
        record_output (bool): If True, output of the circuit will be recorded. Defaults to True.
    """

    def __init__(self, initialize_runtime: bool = True, record_output: bool = True):
        self._module = None
        self._builder = None
        self._entry_point = None
        self._qubit_labels = {}
        self._measured_qubits = {}
        self._initialize_runtime = initialize_runtime
        self._record_output = record_output

    def visit_qasm3_module(self, module: Qasm3Module) -> None:
        _log.debug("Visiting Qasm3 module '%s' (%d)", module.name, module.num_qubits)
        self._module = module.module
        context = self._module.context
        entry = pyqir.entry_point(
            self._module, module.name, module.num_qubits, module.num_clbits
        )

        self._entry_point = entry.name
        self._builder = Builder(context)
        self._builder.insert_at_end(BasicBlock(context, "entry", entry))

        if self._initialize_runtime is True:
            i8p = PointerType(IntType(context, 8))
            nullptr = Constant.null(i8p)
            pyqir.rt.initialize(self._builder, nullptr)

    @property
    def entry_point(self) -> str:
        return self._entry_point

    def finalize(self) -> None:
        self._builder.ret(None)

    def record_output(self, module: Qasm3Module) -> None:
        if self._record_output is False:
            return

        i8p = PointerType(IntType(self._module.context, 8))

        for i in range(module.num_qubits):
            result_ref = pyqir.result(self._module.context, i)
            pyqir.rt.result_record_output(self._builder, result_ref, Constant.null(i8p))

    def visit_register(self, **kwargs) -> None:
        raise NotImplementedError

    def visit_statement(self, **kwargs) -> None:
        raise NotImplementedError

    def ir(self) -> str:
        return str(self._module)

    def bitcode(self) -> bytes:
        return self._module.bitcode()
