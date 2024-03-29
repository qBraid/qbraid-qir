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
import pyqir
import pyqir._native
import pyqir.rt
from pyqir import BasicBlock, Builder, Constant, IntType, PointerType

from .elements import CirqModule
from .opsets import map_cirq_op_to_pyqir_callable

_log = logging.getLogger(name=__name__)


class CircuitElementVisitor(metaclass=ABCMeta):
    @abstractmethod
    def visit_register(self, qids):
        pass

    @abstractmethod
    def visit_operation(self, operation):
        pass


class BasicCirqVisitor(CircuitElementVisitor):
    """A visitor for basic cirq.Circuit elements.

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

    def visit_cirq_module(self, module: CirqModule) -> None:
        _log.debug("Visiting Cirq module '%s' (%d)", module.name, module.num_qubits)
        self._module = module.module
        context = self._module.context
        entry = pyqir.entry_point(self._module, module.name, module.num_qubits, module.num_clbits)

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

        self._qubit_labels.update({bit: n + len(self._qubit_labels) for n, bit in enumerate(qids)})
        _log.debug("Added labels for qubits %s", str(qids))

    def visit_operation(self, operation: cirq.Operation) -> None:
        qlabels = [self._qubit_labels.get(bit) for bit in operation.qubits]
        qubits = [pyqir.qubit(self._module.context, n) for n in qlabels]
        results = [pyqir.result(self._module.context, n) for n in qlabels]

        def handle_measurement(pyqir_func):
            _log.debug("Visiting measurement operation '%s'", str(operation))
            for qubit, result in zip(qubits, results):
                self._measured_qubits[pyqir.qubit_id(qubit)] = True
                pyqir_func(self._builder, qubit, result)

        # dealing with conditional gates
        if isinstance(operation, cirq.ClassicallyControlledOperation):
            op_conds = operation._conditions  # list of measurement keys
            conditions = [
                pyqir.result(self._module.context, int(op_conds[i].keys[0].name))
                for i in range(len(op_conds))
            ]
            regular_op = operation.without_classical_controls()
            temp_pyqir_func, op_str = map_cirq_op_to_pyqir_callable(regular_op)

            # pylint: disable=unnecessary-lambda-assignment
            if op_str in ["Rx", "Ry", "Rz"]:
                pyqir_func = lambda: temp_pyqir_func(
                    self._builder, operation._sub_operation.gate._rads, *qubits
                )
            else:
                pyqir_func = lambda: temp_pyqir_func(self._builder, *qubits)

            def _branch(conds, pyqir_func):
                if len(conds) == 0:
                    temp_id, _ = map_cirq_op_to_pyqir_callable(cirq.I)
                    passable_identity = lambda: temp_id(self._builder, *qubits)
                    return passable_identity
                return pyqir._native.if_result(
                    self._builder,
                    conds[0],
                    zero=_branch(conds[1:], pyqir_func),
                    one=pyqir_func,
                )

            _branch(conditions, pyqir_func)
        else:
            pyqir_func, op_str = map_cirq_op_to_pyqir_callable(operation)

            if op_str == "MEASURE":
                handle_measurement(pyqir_func)
            elif op_str in ["Rx", "Ry", "Rz"]:
                pyqir_func(self._builder, operation.gate._rads, *qubits)
            else:
                pyqir_func(self._builder, *qubits)

    def ir(self) -> str:
        return str(self._module)

    def bitcode(self) -> bytes:
        return self._module.bitcode()
