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
from typing import FrozenSet

import cirq
import pyqir.rt as rt
from pyqir import BasicBlock, Builder, Constant, IntType, PointerType, entry_point

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
        raise NotImplementedError

    def visit_register(self, qid: cirq.Qid):
        _log.debug(f"Visiting qid '{str(qid)}'")
        if isinstance(qid, cirq.LineQubit):
            pass
        elif isinstance(qid, cirq.GridQubit):
            pass
        elif isinstance(qid, cirq.NamedQubit):
            pass
        else:
            raise ValueError(f"Qid of type {type(qid)} not supported.")

    def process_composite_operation(self, operation: cirq.Operation):
        # e.g. operation.gate.sub_gate
        raise NotImplementedError

    def visit_operation(self, operation: cirq.Operation, qids: FrozenSet[cirq.Qid]):
        raise NotImplementedError

    def ir(self) -> str:
        return str(self._module)

    def bitcode(self) -> bytes:
        return self._module.bitcode()

    def _map_profile_to_capabilities(self, profile: str):
        raise NotImplementedError
