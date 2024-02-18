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
from typing import Any, List, Optional, Tuple, Union

import pyqir
import pyqir._native
import pyqir.rt
from openqasm3.ast import (FloatLiteral, Identifier, IndexedIdentifier, IntegerLiteral,
                           QuantumBarrier,QuantumGate, QuantumMeasurementStatement,
                           QuantumReset, RangeDefinition, Statement)
from pyqir import BasicBlock, Builder, Constant, IntType, PointerType

from qbraid_qir.qasm3.elements import Qasm3Module
from qbraid_qir.qasm3.oq3_maps import map_qasm_op_to_pyqir_callable

_log = logging.getLogger(name=__name__)


class CircuitElementVisitor(metaclass=ABCMeta):
    @abstractmethod
    def visit_register(self, register, is_qubit):
        pass

    @abstractmethod
    def visit_statement(self, statement):
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
        self._clbit_labels = {}
        self._qreg_size_map = {}
        self._creg_size_map = {}
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

    def visit_register(
        self, register: Tuple[str, Optional[int]], is_qubit: bool
    ) -> None:
        """Visit a register element.

        Args:
            register (Tuple[str, Optional[int]]): The register name and size.
            is_qubit (bool): Whether the register is a qubit register.

        Returns:
            None
        """
        _log.debug("Visiting register '%s'", str(register))
        current_size = len(self._qubit_labels) if is_qubit else len(self._clbit_labels)

        register_size = register[1] if register[1] else 1
        register_name = register[0]

        for i in range(register_size):
            # required if indices are not used while applying a gate or measurement
            if is_qubit:
                self._qreg_size_map[f"{register_name}"] = register_size
                self._qubit_labels[f"{register_name}_{i}"] = current_size + i
            else:
                self._creg_size_map[f"{register_name}"] = register_size
                self._clbit_labels[f"{register_name}_{i}"] = current_size + i
        _log.debug("Added labels for register '%s'", str(register))

    def _validate_index(self, index: int, size: int, qubit: bool = False):
        if index < 0 or index >= size:
            raise ValueError(
                f"Index {index} out of range for register of size {size} in {'qubit' if qubit else 'clbit'}"
            )

    def _get_op_qubits(self, operation: Any):
        op_qubits = []
        visited_qubits = set()
        for qubit in operation.qubits:
            if isinstance(qubit, IndexedIdentifier):
                qreg_name = qubit.name.name
                if qreg_name not in self._qreg_size_map:
                    raise ValueError(
                        f"Missing register declaration for {qreg_name} in operation {operation}"
                    )
                qreg_size = self._qreg_size_map[qreg_name]

                if isinstance(qubit.indices[0][0], RangeDefinition):
                    start_qid = (
                        0
                        if qubit.indices[0][0].start is None
                        else qubit.indices[0][0].start.value
                    )
                    end_qid = (
                        qreg_size
                        if qubit.indices[0][0].end is None
                        else qubit.indices[0][0].end.value
                    )
                    self._validate_index(start_qid, qreg_size, qubit=True)
                    self._validate_index(end_qid - 1, qreg_size, qubit=True)
                    qreg_qids = [
                        self._qubit_labels[f"{qreg_name}_{i}"]
                        for i in range(start_qid, end_qid)
                    ]
                else:
                    qid = qubit.indices[0][0].value
                    self._validate_index(qid, qreg_size, qubit=True)
                    qreg_qids = [self._qubit_labels[f"{qreg_name}_{qid}"]]
            else:
                # or we have a single qreg name, which means all of qubits in that register
                qreg_name = qubit.name
                if qreg_name not in self._qreg_size_map:
                    raise ValueError(
                        f"Missing register declaration for {qreg_name} in operation {operation}"
                    )
                qreg_size = self._qreg_size_map[qreg_name]
                qreg_qids = [
                    self._qubit_labels[f"{qreg_name}_{i}"] for i in range(qreg_size)
                ]
            for qid in qreg_qids:
                if qid in visited_qubits:
                    raise ValueError(f"Duplicate qubit {qreg_name}[{qid}] argument")
                visited_qubits.add(qid)
            op_qubits.extend([pyqir.qubit(self._module.context, n) for n in qreg_qids])
        return op_qubits

    def _visit_measurement(self, statement: QuantumMeasurementStatement) -> None:
        """Visit a measurement statement element.

        Args:
            statement (QuantumMeasurementStatement): The measurement statement to visit.

        Returns:
            None
        """
        _log.debug("Visiting measurement statement '%s'", str(statement))
        source = statement.measure.qubit
        target = statement.target
        source_id, target_id = None, None

        # handle measurement operation
        source_name = source.name
        if isinstance(source, IndexedIdentifier):
            source_name = source.name.name
            if isinstance(source.indices[0][0], RangeDefinition):
                raise ValueError(
                    f"Range based measurement {statement} not supported at the moment"
                )
            source_id = source.indices[0][0].value

        target_name = target.name
        if isinstance(target, IndexedIdentifier):
            target_name = target.name.name
            if isinstance(target.indices[0][0], RangeDefinition):
                raise ValueError(
                    f"Range based measurement {statement} not supported at the moment"
                )
            target_id = target.indices[0][0].value

        if source_name not in self._qreg_size_map:
            raise ValueError(
                f"Missing register declaration for {source_name} in measurement operation {statement}"
            )
        if target_name not in self._creg_size_map:
            raise ValueError(
                f"Missing register declaration for {target_name} in measurement operation {statement}"
            )

        def _build_qir_measurement(src_name, src_id, target_name, target_id):
            source_qubit = pyqir.qubit(
                self._module.context, self._qubit_labels[f"{src_name}_{src_id}"]
            )
            result = pyqir.result(
                self._module.context, self._clbit_labels[f"{target_name}_{target_id}"]
            )
            pyqir._native.mz(self._builder, source_qubit, result)

        if source_id is None and target_id is None:
            # sizes should match
            if self._qreg_size_map[source_name] != self._creg_size_map[target_name]:
                raise ValueError(
                    f"Register sizes of {source_name} and {target_name} do not match for measurement operation"
                )
            for i in range(self._qreg_size_map[source_name]):
                _build_qir_measurement(source_name, i, target_name, i)

        elif source_id is not None and target_id is not None:
            self._validate_index(
                source_id, self._qreg_size_map[source_name], qubit=True
            )
            self._validate_index(
                target_id, self._creg_size_map[target_name], qubit=False
            )
            _build_qir_measurement(source_name, source_id, target_name, target_id)
        elif source_id is not None and target_id is None:
            # is it fine to record qubit measurement in the first clbit? or should we throw an error?
            self._validate_index(
                source_id, self._qreg_size_map[source_name], qubit=True
            )
            _build_qir_measurement(source_name, source_id, target_name, 0)
        elif source_id is None and target_id is not None:
            # is it fine to just then record first measurement of source qubit?
            self._validate_index(
                target_id, self._creg_size_map[target_name], qubit=False
            )
            _build_qir_measurement(source_name, 0, target_name, target_id)

    def _visit_reset(self, statement: QuantumReset) -> None:
        """Visit a reset statement element.

        Args:
            statement (QuantumReset): The reset statement to visit.

        Returns:
            None
        """
        _log.debug("Visiting reset statement '%s'", str(statement))
        qubit_id = None
        qreg_name = statement.qubits.name
        if isinstance(qreg_name, Identifier):
            qreg_name = statement.qubits.name.name
            if isinstance(statement.qubits.indices[0][0], RangeDefinition):
                raise ValueError(
                    f"Range based reset operation in {statement} not supported at the moment."
                )
            qubit_id = statement.qubits.indices[0][0].value

        if qreg_name not in self._qreg_size_map:
            raise ValueError(
                f"Missing register declaration for {qreg_name} in reset operation {statement}"
            )

        if qubit_id is not None:
            if qubit_id >= self._qreg_size_map[qreg_name]:
                raise ValueError(
                    f"Qubit index {qubit_id} out of range for register {qreg_name} in reset operation {statement}"
                )
            qubit_ids = [self._qubit_labels[f"{qreg_name}_{qubit_id}"]]
        else:
            qreg_size = self._qreg_size_map[qreg_name]
            qubit_ids = [
                self._qubit_labels[f"{qreg_name}_{i}"] for i in range(qreg_size)
            ]

        # generate pyqir reset equivalent
        for qid in qubit_ids:
            pyqir._native.reset(self._builder, pyqir.qubit(self._module.context, qid))

    def _visit_barrier(self, barrier: QuantumBarrier) -> None:
        """Visit a barrier statement element.

        Args:
            statement (QuantumBarrier): The barrier statement to visit.

        Returns:
            None
        """
        # if barrier is applied to ALL qubits at once, we are fine
        barrier_qubits = self._get_op_qubits(barrier)
        total_qubit_count = sum(self._qreg_size_map.values())
        if len(barrier_qubits) == total_qubit_count:
            pyqir._native.barrier(self._builder)
        else:
            raise NotImplementedError(
                "Barrier operation on a qubit subset is not supported in pyqir"
            )

    def _is_parametric_gate(self, operation: QuantumGate) -> bool:
        return len(operation.arguments) > 0

    def _get_op_parameters(self, operation: QuantumGate) -> List[float]:
        param_list = []
        for param in operation.arguments:
            if not isinstance(param, (FloatLiteral, IntegerLiteral)):
                raise ValueError(
                    f"Unsupported parameter type {type(param)} for operation {operation}"
                )
            param_list.append(float(param.value))

        if len(param_list) > 1:
            raise ValueError(f"Parameterized gate {operation} with > 1 params not supported")
        
        return param_list
        

    def _visit_gate_operation(self, operation: QuantumGate) -> None:
        """Visit a gate operation element.

        Args:
            operation (QuantumGate): The gate operation to visit.

        Returns:
            None
        """

        # Currently handling the gates in the stdgates.inc file
        _log.debug("Visiting gate operation '%s'", str(operation))
        op_name = operation.name.name
        op_qubits = self._get_op_qubits(operation)
        qir_func, op_qubit_count = map_qasm_op_to_pyqir_callable(op_name)
        op_parameters = None

        if len(op_qubits) % op_qubit_count != 0:
            raise ValueError(
                f"Invalid number of qubits {op_qubits} for operation {operation}"
            )

        if self._is_parametric_gate(operation):
            op_parameters = self._get_op_parameters(operation)

        if op_parameters is not None:
            for i in range(0, len(op_qubits), op_qubit_count):
                qubit_subset = op_qubits[i : i + op_qubit_count]
                qir_func(self._builder, *op_parameters, *qubit_subset)
        else:
            # we have a linear application of the gate 
            # first act on the first op_qubit_count qubits, then the next op_qubit_count and so on
            for i in range(0, len(op_qubits), op_qubit_count):
                qubit_subset = op_qubits[i : i + op_qubit_count]
                qir_func(self._builder, *qubit_subset)


    def visit_statement(self, statement: Statement) -> None:
        """Visit a statement element.

        Args:
            statement (Statement): The statement to visit.

        Returns:
            None
        """
        _log.debug("Visiting statement '%s'", str(statement))
        # start simple, only handling measurement for now
        # print(statement, "\n")
        if isinstance(statement, QuantumMeasurementStatement):
            self._visit_measurement(statement)
        elif isinstance(statement, QuantumReset):
            self._visit_reset(statement)
        elif isinstance(statement, QuantumBarrier):
            self._visit_barrier(statement)
        # elif isinstance(statement, )
        elif isinstance(statement, QuantumGate):
            self._visit_gate_operation(statement)

    def ir(self) -> str:
        return str(self._module)

    def bitcode(self) -> bytes:
        return self._module.bitcode()
