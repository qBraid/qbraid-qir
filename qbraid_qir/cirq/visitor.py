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
Module defining CirqVisitor.

"""
import logging
from abc import ABCMeta, abstractmethod
from typing import List

import cirq
import numpy as np
import pyqir
import pyqir._native
import pyqir.rt
from pyqir import BasicBlock, Builder, Constant, IntType, PointerType

from qbraid_qir.cirq.elements import CirqModule
from qbraid_qir.cirq.opsets import map_cirq_op_to_pyqir_callable

_log = logging.getLogger(name=__name__)


class CircuitElementVisitor(metaclass=ABCMeta):
    @abstractmethod
    def visit_register(self, qids):
        pass

    @abstractmethod
    def visit_operation(self, operation):
        pass


class BasicQisVisitor(CircuitElementVisitor):
    def __init__(self, profile: str = "AdaptiveExecution", **kwargs):
        self._module = None
        self._builder = None
        self._entry_point = None
        self._qubit_labels = {}
        self._profile = profile
        self._measured_qubits = {}
        self._record_output = kwargs.get("record_output", True)

    def visit_cirq_module(self, module: CirqModule):
        _log.debug("Visiting Cirq module '%s' (%d)", module.name, module.num_qubits)
        self._module = module.module
        context = self._module.context
        entry = pyqir.entry_point(
            self._module, module.name, module.num_qubits, module.num_clbits
        )

        self._entry_point = entry.name
        self._builder = Builder(context)
        self._builder.insert_at_end(BasicBlock(context, "entry", entry))

        i8p = PointerType(IntType(context, 8))
        nullptr = Constant.null(i8p)
        pyqir.rt.initialize(self._builder, nullptr)

    @property
    def entry_point(self) -> str:
        return self._entry_point

    def finalize(self) -> None:
        self._builder.ret(None)

    def record_output(self, module: CirqModule) -> None:
        if self._record_output is False:
            return

        i8p = PointerType(IntType(self._module.context, 8))

        for i in range(module.num_qubits):
            result_ref = pyqir.result(self._module.context, i)
            pyqir.rt.result_record_output(self._builder, result_ref, Constant.null(i8p))

    def visit_register(self, qids: List[cirq.Qid]) -> None:
        _log.debug("Visiting qids '%s'", str(qids))

        if not isinstance(qids, list):
            raise TypeError("Parameter is not a list.")

        if not all(isinstance(x, cirq.Qid) for x in qids):
            raise TypeError("All elements in the list must be of type cirq.Qid.")

        self._qubit_labels.update(
            {bit: n + len(self._qubit_labels) for n, bit in enumerate(qids)}
        )
        _log.debug("Added labels for qubits %s", str(qids))

    def visit_operation(self, operation: cirq.Operation):
        qlabels = [self._qubit_labels.get(bit) for bit in operation.qubits]
        qubits = [pyqir.qubit(self._module.context, n) for n in qlabels]
        results = [pyqir.result(self._module.context, n) for n in qlabels]

        pyqir_func, op_str = map_cirq_op_to_pyqir_callable(operation)

        if op_str == "MEASURE":
            # TODO: naive implementation, revisit and test
            _log.debug("Visiting measurement operation '%s'", str(operation))
            pyqir_func(self._builder, *qubits, *results)
        elif op_str in ["Rx", "Ry", "Rz"]:
            angle = operation.gate._rads * np.pi
            pyqir_func(self._builder, angle, *qubits)
        else:
            pyqir_func(self._builder, *qubits)

    def ir(self) -> str:
        return str(self._module)

    def bitcode(self) -> bytes:
        return self._module.bitcode()
