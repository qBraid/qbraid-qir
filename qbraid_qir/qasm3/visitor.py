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
# pylint: disable=line-too-long
import copy
import logging
from abc import ABCMeta, abstractmethod
from typing import Any, List, Optional, Tuple, Union

import pyqir
import pyqir._native
import pyqir.rt
from openqasm3.ast import (
    BinaryExpression,
    BooleanLiteral,
    BranchingStatement,
    ClassicalDeclaration,
    DurationLiteral,
    FloatLiteral,
    FloatType,
    Identifier,
    ImaginaryLiteral,
    IndexedIdentifier,
    IndexExpression,
    IntegerLiteral,
)
from openqasm3.ast import IntType as qasm3IntType
from openqasm3.ast import (
    QuantumBarrier,
    QuantumGate,
    QuantumGateDefinition,
    QuantumMeasurementStatement,
    QuantumReset,
    RangeDefinition,
    Statement,
    UintType,
    UnaryExpression,
)
from pyqir import BasicBlock, Builder, Constant
from pyqir import IntType as qirIntType
from pyqir import PointerType

from qbraid_qir.qasm3.elements import Context, Qasm3Module, Scope
from qbraid_qir.qasm3.oq3_maps import map_qasm_op_to_pyqir_callable, qasm3_expression_op_map

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
        self._scope = Scope.GLOBAL
        self._context = Context.GLOBAL
        self._qubit_labels = {}
        self._clbit_labels = {}
        self._qreg_size_map = {}
        self._creg_size_map = {}
        self._custom_gates = {}
        self._measured_qubits = {}
        self._initialize_runtime = initialize_runtime
        self._record_output = record_output

    def visit_qasm3_module(self, module: Qasm3Module) -> None:
        """
        Visit a Qasm3 module.

        Args:
            module (Qasm3Module): The module to visit.

        Returns:
            None
        """
        _log.debug("Visiting Qasm3 module '%s' (%d)", module.name, module.num_qubits)
        self._module = module.module
        context = self._module.context
        entry = pyqir.entry_point(self._module, module.name, module.num_qubits, module.num_clbits)

        self._entry_point = entry.name
        self._builder = Builder(context)
        self._builder.insert_at_end(BasicBlock(context, "entry", entry))

        if self._initialize_runtime is True:
            i8p = PointerType(qirIntType(context, 8))
            nullptr = Constant.null(i8p)
            pyqir.rt.initialize(self._builder, nullptr)

    @property
    def entry_point(self) -> str:
        return self._entry_point

    def finalize(self) -> None:
        self._builder.ret(None)

    def _set_scope(self, scope: Scope) -> None:
        self._scope = scope

    def _in_gate(self) -> bool:
        return self._scope == Scope.GATE

    def _in_global_scope(self) -> bool:
        return self._scope == Scope.GLOBAL and self._context == Context.GLOBAL

    def _in_function(self) -> bool:
        return self._scope == Scope.FUNCTION

    def _set_context(self, context: Context) -> None:
        self._context = context

    def _in_loop(self) -> bool:
        return self._context == Context.LOOP

    def _in_ifblock(self) -> bool:
        return self._context == Context.IF

    def record_output(self, module: Qasm3Module) -> None:
        if self._record_output is False:
            return

        i8p = PointerType(qirIntType(self._module.context, 8))

        for i in range(module.num_qubits):
            result_ref = pyqir.result(self._module.context, i)
            pyqir.rt.result_record_output(self._builder, result_ref, Constant.null(i8p))

    def visit_register(self, register: Tuple[str, Optional[int]], is_qubit: bool) -> None:
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

    def _validate_index(self, index: Union[int, None], size: int, qubit: bool = False) -> None:
        """Validate the index for a register.

        Args:
            index (int): The index to validate.
            size (int): The size of the register.
            qubit (bool): Whether the register is a qubit register.
        """
        # nothing to validate if index is None
        if index is None:
            return True
        if index < 0 or index >= size:
            raise ValueError(
                f"Index {index} out of range for register of size {size} in {'qubit' if qubit else 'clbit'}"
            )

    def _get_op_qubits(self, operation: Any, qir_form: bool = True) -> List[pyqir.qubit]:
        """Get the qubits for the operation.

        Args:
            operation (Any): The operation to get qubits for.

        Returns:
            List[pyqir.qubit]: The qubits for the operation.
        """
        qir_qubits = []
        openqasm_qubits = []
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
                        0 if qubit.indices[0][0].start is None else qubit.indices[0][0].start.value
                    )
                    end_qid = (
                        qreg_size
                        if qubit.indices[0][0].end is None
                        else qubit.indices[0][0].end.value
                    )
                    self._validate_index(start_qid, qreg_size, qubit=True)
                    self._validate_index(end_qid - 1, qreg_size, qubit=True)
                    qreg_qids = [
                        self._qubit_labels[f"{qreg_name}_{i}"] for i in range(start_qid, end_qid)
                    ]
                    openqasm_qubits.extend(
                        [
                            IndexedIdentifier(Identifier(qreg_name), [[IntegerLiteral(i)]])
                            for i in range(start_qid, end_qid)
                        ]
                    )
                else:
                    qid = qubit.indices[0][0].value
                    self._validate_index(qid, qreg_size, qubit=True)
                    qreg_qids = [self._qubit_labels[f"{qreg_name}_{qid}"]]
                    openqasm_qubits.append(qubit)
            else:
                # or we have a single qreg name, which means all of qubits in that register
                qreg_name = qubit.name
                if qreg_name not in self._qreg_size_map:
                    raise ValueError(
                        f"Missing register declaration for {qreg_name} in operation {operation}"
                    )
                qreg_size = self._qreg_size_map[qreg_name]
                openqasm_qubits.extend(
                    [
                        IndexedIdentifier(Identifier(qreg_name), [[IntegerLiteral(i)]])
                        for i in range(qreg_size)
                    ]
                )
                qreg_qids = [self._qubit_labels[f"{qreg_name}_{i}"] for i in range(qreg_size)]
            for qid in qreg_qids:
                if qid in visited_qubits:
                    raise ValueError(f"Duplicate qubit {qreg_name}[{qid}] argument")
                visited_qubits.add(qid)
            qir_qubits.extend([pyqir.qubit(self._module.context, n) for n in qreg_qids])

        if not qir_form:
            return openqasm_qubits

        return qir_qubits

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

        source_name = source.name
        if isinstance(source, IndexedIdentifier):
            source_name = source.name.name
            if isinstance(source.indices[0][0], RangeDefinition):
                raise ValueError(f"Range based measurement {statement} not supported at the moment")
            source_id = source.indices[0][0].value

        target_name = target.name
        if isinstance(target, IndexedIdentifier):
            target_name = target.name.name
            if isinstance(target.indices[0][0], RangeDefinition):
                raise ValueError(f"Range based measurement {statement} not supported at the moment")
            target_id = target.indices[0][0].value

        if source_name not in self._qreg_size_map:
            raise ValueError(
                f"Missing register declaration for {source_name} in measurement operation {statement}"
            )
        if target_name not in self._creg_size_map:
            raise ValueError(
                f"Missing register declaration for {target_name} in measurement operation {statement}"
            )

        def _build_qir_measurement(
            src_name: str, src_id: Union[int, None], target_name: str, target_id: Union[int, None]
        ):
            if src_id is None:
                src_id = 0
            if target_id is None:
                target_id = 0

            source_qubit = pyqir.qubit(
                self._module.context, self._qubit_labels[f"{src_name}_{src_id}"]
            )
            result = pyqir.result(
                self._module.context, self._clbit_labels[f"{target_name}_{target_id}"]
            )
            pyqir._native.mz(self._builder, source_qubit, result)

        if source_id is None and target_id is None:
            if self._qreg_size_map[source_name] != self._creg_size_map[target_name]:
                raise ValueError(
                    f"Register sizes of {source_name} and {target_name} do not match for measurement operation"
                )
            for i in range(self._qreg_size_map[source_name]):
                _build_qir_measurement(source_name, i, target_name, i)
        else:
            self._validate_index(source_id, self._qreg_size_map[source_name], qubit=True)
            self._validate_index(target_id, self._creg_size_map[target_name], qubit=False)
            _build_qir_measurement(source_name, source_id, target_name, target_id)

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
            qubit_ids = [self._qubit_labels[f"{qreg_name}_{i}"] for i in range(qreg_size)]

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
        """Get the parameters for the operation.

        Args:
            operation (QuantumGate): The operation to get parameters for.

        Returns:
            List[float]: The parameters for the operation.
        """
        param_list = []
        for param in operation.arguments:
            param_value = self._evaluate_expression(param)
            param_list.append(param_value)

        if len(param_list) > 1:
            raise ValueError(f"Parameterized gate {operation} with > 1 params not supported")

        return param_list

    def _visit_gate_definition(self, definition: QuantumGateDefinition) -> None:
        """Visit a gate definition element.

        Args:
            definition (QuantumGateDefinition): The gate definition to visit.

        Returns:
            None
        """
        gate_name = definition.name.name
        if gate_name in self._custom_gates:
            raise ValueError(f"Duplicate gate definition for {gate_name}")
        self._custom_gates[gate_name] = definition

    def _visit_basic_gate_operation(self, operation: QuantumGate) -> None:
        """Visit a gate operation element.

        Args:
            operation (QuantumGate): The gate operation to visit.

        Returns:
            None
        """

        _log.debug("Visiting basic gate operation '%s'", str(operation))
        op_name: str = operation.name.name
        op_qubits = self._get_op_qubits(operation)
        qir_func, op_qubit_count = map_qasm_op_to_pyqir_callable(op_name)
        op_parameters = None

        if len(op_qubits) % op_qubit_count != 0:
            raise ValueError(f"Invalid number of qubits {len(op_qubits)} for operation {operation}")

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

    def _transform_gate_qubits(self, gate_op, qubit_map):
        """Transform the qubits of a gate operation with a qubit map.

        Args:
            gate_op (QuantumGate): The gate operation to transform.
            qubit_map (Dict[str, IndexedIdentifier]): The qubit map to use for transformation.

        Returns:
            None
        """
        for i, qubit in enumerate(gate_op.qubits):
            if isinstance(qubit, IndexedIdentifier):
                raise ValueError(f"Indexing {qubit} not supported in gate definition")
            gate_op.qubits[i] = qubit_map[qubit.name]

    def _transform_gate_params(self, gate_op, param_map):
        """Transform the parameters of a gate operation with a parameter map.

        Args:
            gate_op (QuantumGate): The gate operation to transform.
            param_map (Dict[str, Union[FloatLiteral, IntegerLiteral]]): The parameter map to use for transformation.

        Returns:
            None
        """
        for i, param in enumerate(gate_op.arguments):
            if isinstance(param, Identifier):
                gate_op.arguments[i] = param_map[param.name]

    def _visit_custom_gate_operation(self, operation: QuantumGate) -> None:
        """Visit a custom gate operation element.

        Args:
            operation (QuantumGate): The gate operation to visit.

        Returns:in computation
        """
        _log.debug("Visiting custom gate operation '%s'", str(operation))
        gate_name: str = operation.name.name
        gate_definition: QuantumGateDefinition = self._custom_gates[gate_name]

        if len(operation.arguments) != len(gate_definition.arguments):
            raise ValueError(
                f"""Parameter count mismatch for gate {gate_name}. Expected \
{len(gate_definition.arguments)} but got {len(operation.arguments)} in operation"""
            )

        op_qubits = self._get_op_qubits(operation, qir_form=False)

        if len(op_qubits) != len(gate_definition.qubits):
            raise ValueError(
                f"""Qubit count mismatch for gate {gate_name}. Expected \
{len(gate_definition.qubits)} but got {len(op_qubits)} in operation"""
            )

        # we need this because the gates applied inside a gate definition use the
        # VARIABLE names and not the qubits

        # so we need to update the arguments of these gate applications with the actual
        # qubit identifiers and then RECURSIVELY call the visit_generic_gate_operation
        qubit_map = {
            formal_arg.name: actual_arg
            for formal_arg, actual_arg in zip(gate_definition.qubits, op_qubits)
        }
        param_map = {
            formal_arg.name: actual_arg
            for formal_arg, actual_arg in zip(gate_definition.arguments, operation.arguments)
        }

        for gate_op in gate_definition.body:
            # necessary to avoid modifying the original gate definition
            # in case the gate is reapplied
            gate_op_copy = copy.deepcopy(gate_op)
            if isinstance(gate_op, QuantumGate):
                # transform the gate_op with the actual qubit identifiers
                # and the actual parameters
                self._transform_gate_params(gate_op_copy, param_map)
                self._transform_gate_qubits(gate_op_copy, qubit_map)
                self._visit_generic_gate_operation(gate_op_copy)
            # can't have non-gate operations inside a gate definition
            elif isinstance(gate_op, QuantumMeasurementStatement):
                raise ValueError(
                    f"Unsupported measurement statement in gate definition {gate_definition}"
                )
            elif isinstance(gate_op, QuantumReset):
                raise ValueError(
                    f"Unsupported reset statement in gate definition {gate_definition}"
                )
            else:
                # TODO : add control flow support
                raise ValueError(
                    f"Unsupported gate definition statement{ gate_op} in {gate_definition}"
                )

    def _visit_generic_gate_operation(self, operation: QuantumGate) -> None:
        """Visit a gate operation element.

        Args:
            operation (QuantumGate): The gate operation to visit.

        Returns:
            None
        """
        if operation.name.name in self._custom_gates:
            self._visit_custom_gate_operation(operation)
        else:
            self._visit_basic_gate_operation(operation)

    def _visit_classical_operation(self, statement: ClassicalDeclaration) -> None:
        """Visit a classical operation element.

        Args:
            statement (ClassicalType): The classical operation to visit.

        Returns:
            None
        """
        decl_type = statement.type

        if isinstance(decl_type, (qasm3IntType, UintType, FloatType)):
            size = decl_type.size if decl_type.size is not None else 1

            # we only support static integer sizes
            if isinstance(size, IntegerLiteral):
                value = size.value
            else:
                raise ValueError(f"Unsupported integer size {size} in {statement}")
            var_name = statement.identifier.name

            # how to add this in the QIR???
        else:
            raise ValueError(f"Unsupported classical type {decl_type} in {statement}")

    def _evaluate_expression(self, expression: Any) -> bool:
        """Evaluate an expression.

        Args:
            expression (Any): The expression to evaluate.

        Returns:
            bool: The result of the evaluation.
        """
        if isinstance(expression, (ImaginaryLiteral, DurationLiteral)):
            raise ValueError(f"Unsupported expression type {type(expression)}")
        elif isinstance(expression, (Identifier, IndexedIdentifier)):
            # we need to check our scope and context to get the value of the identifier
            # if it is a classical register, we can directly get the value
            # how to get the value of the identifier in the QIR??
            # TO DO : extend this
            # we only support classical register values in computation
            raise ValueError(f"Unsupported expression type {type(expression)}")

        elif isinstance(expression, BooleanLiteral):
            return expression.value
        elif isinstance(expression, (IntegerLiteral, FloatLiteral)):
            print("here")
            return expression.value
        elif isinstance(expression, UnaryExpression):
            op = expression.op.name  # can be '!', '~' or '-'
            if op == "!":
                return not self._evaluate_expression(expression.expression)
            elif op == "-":
                return -1 * self._evaluate_expression(expression.expression)
            elif op == "~":
                value = self._evaluate_expression(expression.expression)
                if not isinstance(value, int):
                    raise ValueError(f"Unsupported expression type {type(value)} in ~ operation")
        elif isinstance(expression, BinaryExpression):
            lhs = self._evaluate_expression(expression.lhs)
            op = expression.op.name
            rhs = self._evaluate_expression(expression.rhs)
            return qasm3_expression_op_map(op, lhs, rhs)
        else:
            raise ValueError(f"Unsupported expression type {type(expression)}")

    def _validate_branch_condition(self, condition) -> None:
        # What about binary expressions ?
        # Other types of expressions ?
        if not isinstance(condition, IndexExpression):
            raise ValueError(
                f"Unsupported expression type {type(condition)} in if condition. Can only be a simple comparison"
            )

    def _visit_branching_statement(self, statement: BranchingStatement) -> None:
        """Visit a branching statement element.

        Args:
            statement (BranchingStatement): The branching statement to visit.

        Returns:
            None
        """
        condition = statement.condition
        self._validate_branch_condition(condition)

        if_block = statement.if_block
        # if block should be present for sure
        if not statement.if_block:
            raise ValueError(f"Missing if block in {statement}")
        else_block = statement.else_block

        reg_id = None
        reg_name = None

        reg_name = condition.collection.name
        reg_id = condition.index[0].value
        if reg_name not in self._creg_size_map:
            raise ValueError(f"Missing register declaration for {reg_name} in {condition}")
        self._validate_index(reg_id, self._creg_size_map[reg_name], qubit=False)

        def _visit_statement_block(block):
            for stmt in block:
                self.visit_statement(stmt)

        # if the condition is true, we visit the if block
        pyqir._native.if_result(
            self._builder,
            pyqir.result(self._module.context, self._clbit_labels[f"{reg_name}_{reg_id}"]),
            zero=lambda: _visit_statement_block(else_block),
            one=lambda: _visit_statement_block(if_block),
        )

    def visit_contextual_statement(self, statement: Statement) -> None:
        pass

    def visit_scoped_statement(self, statement: Statement) -> None:
        pass

    def visit_statement(self, statement: Statement) -> None:
        """Visit a statement element.

        Args:
            statement (Statement): The statement to visit.

        Returns:
            None
        """
        _log.debug("Visiting statement '%s'", str(statement))

        if isinstance(statement, QuantumMeasurementStatement):
            self._visit_measurement(statement)
        elif isinstance(statement, QuantumReset):
            self._visit_reset(statement)
        elif isinstance(statement, QuantumBarrier):
            self._visit_barrier(statement)
        elif isinstance(statement, QuantumGateDefinition):
            self._visit_gate_definition(statement)
        elif isinstance(statement, QuantumGate):
            self._visit_generic_gate_operation(statement)
        elif isinstance(statement, ClassicalDeclaration):
            self._visit_classical_operation(statement)
        elif isinstance(statement, BranchingStatement):
            self._visit_branching_statement(statement)

    def ir(self) -> str:
        return str(self._module)

    def bitcode(self) -> bytes:
        return self._module.bitcode()
