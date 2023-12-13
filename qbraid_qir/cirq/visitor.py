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
# isort: skip_file

import logging
from abc import ABCMeta, abstractmethod
from typing import FrozenSet, List

import cirq
import pyqir.rt as rt
import pyqir
from pyqir import (
    BasicBlock,
    Builder,
    Constant,
    IntType,
    PointerType,
    const,
    entry_point,
)

from qbraid_qir.cirq.elements import CirqModule

_log = logging.getLogger(name=__name__)


class CircuitElementVisitor(metaclass=ABCMeta):
    @abstractmethod
    def visit_register(self, register):
        raise NotImplementedError

    @abstractmethod
    def visit_operation(self, operation):
        raise NotImplementedError


# NOTE: lots of boiler plate used from qiskit-qir that still needs to be worked through


class BasicQisVisitor(CircuitElementVisitor):
    def __init__(self, profile: str = "AdaptiveExecution", **kwargs):
        self._module = None
        self._builder = None
        self._entry_point = None
        self._qubit_labels = {}
        self._profile = profile
        self._capabilities = self._map_profile_to_capabilities(profile)
        self._measured_qubits = {}
        self._record_output = kwargs.get("record_output", True)

    def visit_cirq_module(self, module: CirqModule):
        _log.debug(f"Visiting Cirq module '{module.name}' ({module.num_qubits})")
        self._module = module.module
        context = self._module.context
        entry = entry_point(self._module, module.name, module.num_qubits)

        self._entry_point = entry.name
        self._builder = Builder(context)
        self._builder.insert_at_end(BasicBlock(context, "entry", entry))

        i8p = PointerType(IntType(context, 8))
        nullptr = Constant.null(i8p)
        rt.initialize(self._builder, nullptr)

    @property
    def entry_point(self) -> str:
        return self._entry_point

    def finalize(self):
        self._builder.ret(None)

    def record_output(self, module: CirqModule):
        if self._record_output == False:
            return

        i8p = PointerType(IntType(self._module.context, 8))

        # qiskit inverts the ordering of the results within each register
        # but keeps the overall register ordering
        # here we logically loop from n-1 to 0, decrementing in order to
        # invert the register output. The second parameter is an exclusive
        # range so we need to go to -1 instead of 0
        logical_id_base = 0
        for size in module.reg_sizes:
            rt.array_record_output(
                self._builder,
                const(IntType(self._module.context, 64), size),
                Constant.null(i8p),
            )
            for index in range(size - 1, -1, -1):
                result_ref = pyqir.result(self._module.context, logical_id_base + index)
                rt.result_record_output(self._builder, result_ref, Constant.null(i8p))
            logical_id_base += size

    def visit_register(self, qids: List[cirq.Qid]):
        _log.debug(f"Visiting qid '{str(qids)}'")
        if not isinstance(qids, list):
            raise TypeError("Parameter is not a list.")

        if not all(isinstance(x, cirq.Qid) for x in qids):
            raise TypeError("All elements in the list must be of type cirq.Qid.")
            # self._qubit_labels[qid] = len(self._qubit_labels)
        self._qubit_labels.update(
            {bit: n + len(self._qubit_labels) for n, bit in enumerate(qids)}
        )
        _log.debug(f"Added label for qubits {qids}")

    def process_composite_operation(self, operation: cirq.Operation):
        # e.g. operation.gate.sub_gate, this functionality might exist elsewhere.
        raise NotImplementedError

    def visit_operation(self, operation: cirq.Operation, qids: FrozenSet[cirq.Qid]):
        qlabels = [self._qubit_labels.get(bit) for bit in qids]
        qubits = [pyqir.qubit(self._module.context, n) for n in qlabels]
        results = [pyqir.result(self._module.context, n) for n in qlabels]
        # call some function that depends on qubits and results

    def ir(self) -> str:
        return str(self._module)

    def bitcode(self) -> bytes:
        return self._module.bitcode()
