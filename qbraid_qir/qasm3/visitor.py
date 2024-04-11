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
# pylint: disable=too-many-instance-attributes
import copy
import logging
import sys
from abc import ABCMeta, abstractmethod
from typing import Any, List, Optional, Tuple, Union

import pyqir
import pyqir._native
import pyqir.rt
from openqasm3.ast import (
    AliasStatement,
    BinaryExpression,
    BooleanLiteral,
    BranchingStatement,
    ClassicalDeclaration,
    DurationLiteral,
    FloatLiteral,
    GateModifierName,
    Identifier,
    ImaginaryLiteral,
    Include,
    IndexedIdentifier,
    IndexExpression,
    IntegerLiteral,
    IODeclaration,
    QuantumBarrier,
    QuantumGate,
    QuantumGateDefinition,
    QuantumGateModifier,
    QuantumMeasurementStatement,
    QuantumReset,
    QubitDeclaration,
    RangeDefinition,
    Span,
    Statement,
    SubroutineDefinition,
    UnaryExpression,
)
from pyqir import BasicBlock, Builder, Constant
from pyqir import IntType as qirIntType
from pyqir import PointerType

from .elements import Context, InversionOp, Qasm3Module, Scope
from .exceptions import Qasm3ConversionError
from .oq3_maps import (
    map_qasm_inv_op_to_pyqir_callable,
    map_qasm_op_to_pyqir_callable,
    qasm3_constants_map,
    qasm3_expression_op_map,
)

_log = logging.getLogger(name=__name__)


class ProgramElementVisitor(metaclass=ABCMeta):
    @abstractmethod
    def visit_register(self, register):
        pass

    @abstractmethod
    def visit_statement(self, statement):
        pass


class BasicQasmVisitor(ProgramElementVisitor):
    """A visitor for basic OpenQASM program elements.

    This class is designed to traverse and interact with elements in an OpenQASM program.

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

    def visit_register(self, register: Union[QubitDeclaration, ClassicalDeclaration]) -> None:
        """Visit a register element.

        Args:
            register (Union[QubitDeclaration, ClassicalDeclaration]): The register name and size.

        Returns:
            None
        """
        _log.debug("Visiting register '%s'", str(register))
        is_qubit = isinstance(register, QubitDeclaration)

        current_size = len(self._qubit_labels) if is_qubit else len(self._clbit_labels)
        if is_qubit:
            register_size = 1 if register.size is None else register.size.value
        else:
            register_size = 1 if register.type.size is None else register.type.size.value
        register_name = register.qubit.name if is_qubit else register.identifier.name

        for i in range(register_size):
            # required if indices are not used while applying a gate or measurement
            if is_qubit:
                self._qreg_size_map[f"{register_name}"] = register_size
                self._qubit_labels[f"{register_name}_{i}"] = current_size + i
            else:
                self._creg_size_map[f"{register_name}"] = register_size
                self._clbit_labels[f"{register_name}_{i}"] = current_size + i
        _log.debug("Added labels for register '%s'", str(register))

    def _print_err_location(self, element: Span) -> str:
        print(
            f"Error at line {element.start_line}, column {element.start_column} in QASM file",
            file=sys.stderr,
        )

    def _validate_index(self, index: Optional[int], size: int, qubit: bool = False) -> None:
        """Validate the index for a register.

        Args:
            index (optional, int): The index to validate.
            size (int): The size of the register.
            qubit (bool): Whether the register is a qubit register.

        Raises:
            Qasm3ConversionError: If the index is out of range.
        """
        # nothing to validate if index is None
        if index is None:
            return

        if not 0 <= index < size:
            raise Qasm3ConversionError(
                f"Index {index} out of range for register of size {size} in "
                f"{'qubit' if qubit else 'clbit'}"
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
        qubit_list = operation.qubits if isinstance(operation.qubits, list) else [operation.qubits]
        for qubit in qubit_list:
            if isinstance(qubit, IndexedIdentifier):
                qreg_name = qubit.name.name
                if qreg_name not in self._qreg_size_map:
                    self._print_err_location(operation.span)
                    raise Qasm3ConversionError(
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
                    self._print_err_location(operation.span)
                    raise Qasm3ConversionError(
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
                    self._print_err_location(operation.span)
                    raise Qasm3ConversionError(f"Duplicate qubit {qreg_name}[{qid}] argument")
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
                self._print_err_location(statement.span)
                raise Qasm3ConversionError(
                    f"Range based measurement {statement} not supported at the moment"
                )
            source_id = source.indices[0][0].value

        target_name = target.name
        if isinstance(target, IndexedIdentifier):
            target_name = target.name.name
            if isinstance(target.indices[0][0], RangeDefinition):
                self._print_err_location(statement.span)
                raise Qasm3ConversionError(
                    f"Range based measurement {statement} not supported at the moment"
                )
            target_id = target.indices[0][0].value

        if source_name not in self._qreg_size_map:
            self._print_err_location(statement.span)
            raise Qasm3ConversionError(
                f"Missing register declaration for {source_name} in measurement "
                f"operation {statement}"
            )
        if target_name not in self._creg_size_map:
            self._print_err_location(statement.span)
            raise Qasm3ConversionError(
                f"Missing register declaration for {target_name} in measurement "
                f"operation {statement}"
            )

        def _build_qir_measurement(
            src_name: str, src_id: Union[int, None], target_name: str, target_id: Union[int, None]
        ):
            src_id = 0 if src_id is None else src_id
            target_id = 0 if target_id is None else target_id

            source_qubit = pyqir.qubit(
                self._module.context, self._qubit_labels[f"{src_name}_{src_id}"]
            )
            result = pyqir.result(
                self._module.context, self._clbit_labels[f"{target_name}_{target_id}"]
            )
            pyqir._native.mz(self._builder, source_qubit, result)

        if source_id is None and target_id is None:
            if self._qreg_size_map[source_name] != self._creg_size_map[target_name]:
                self._print_err_location(statement.span)
                raise Qasm3ConversionError(
                    f"Register sizes of {source_name} and {target_name} do not match "
                    "for measurement operation"
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
        qubit_ids = self._get_op_qubits(statement, True)
        for qid in qubit_ids:
            pyqir._native.reset(self._builder, qid)

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
            self._print_err_location(barrier.span)
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
            self._print_err_location(definition.span)
            raise Qasm3ConversionError(f"Duplicate gate definition for {gate_name}")
        self._custom_gates[gate_name] = definition

    def _visit_basic_gate_operation(self, operation: QuantumGate, inverse: bool = False) -> None:
        """Visit a gate operation element.

        Args:
            operation (QuantumGate): The gate operation to visit.
            inverse (bool): Whether the operation is an inverse operation. Defaults to False.

                          - if inverse is True, we apply check for different cases in the
                            map_qasm_inv_op_to_pyqir_callable method.

                          - Only rotation and S / T gates are affected by this inversion. For S/T
                            gates we map them to Sdg / Tdg and vice versa.

                          - For rotation gates, we map to the same gates but invert the rotation
                            angles.

        Returns:
            None

        Raises:
            Qasm3ConversionError: If the number of qubits is invalid.

        """

        _log.debug("Visiting basic gate operation '%s'", str(operation))
        op_name: str = operation.name.name
        op_qubits = self._get_op_qubits(operation)
        inverse_action = None
        if not inverse:
            qir_func, op_qubit_count = map_qasm_op_to_pyqir_callable(op_name)
        else:
            # in basic gates, inverse action only affects the rotation gates
            qir_func, op_qubit_count, inverse_action = map_qasm_inv_op_to_pyqir_callable(op_name)

        op_parameters = None

        if len(op_qubits) % op_qubit_count != 0:
            self._print_err_location(operation.span)
            raise Qasm3ConversionError(
                f"Invalid number of qubits {len(op_qubits)} for operation {operation.name.name}"
            )

        if self._is_parametric_gate(operation):
            op_parameters = self._get_op_parameters(operation)
            if inverse_action == InversionOp.INVERT_ROTATION:
                op_parameters = [-1 * param for param in op_parameters]

        for i in range(0, len(op_qubits), op_qubit_count):
            # we apply the gate on the qubit subset linearly
            qubit_subset = op_qubits[i : i + op_qubit_count]
            if op_parameters is not None:
                qir_func(self._builder, *op_parameters, *qubit_subset)
            else:
                qir_func(self._builder, *qubit_subset)

    def _transform_gate_qubits(self, gate_op: QuantumGate, qubit_map: dict) -> None:
        """Transform the qubits of a gate operation with a qubit map.

        Args:
            gate_op (QuantumGate): The gate operation to transform.
            qubit_map (Dict[str, IndexedIdentifier]): The qubit map to use for transformation.

        Returns:
            None
        """
        for i, qubit in enumerate(gate_op.qubits):
            if isinstance(qubit, IndexedIdentifier):
                self._print_err_location(qubit.span)
                raise Qasm3ConversionError(
                    f"Indexing '{qubit.name.name}' not supported in gate definition"
                )
            gate_op.qubits[i] = qubit_map[qubit.name]

    def _transform_gate_params(self, gate_op: QuantumGate, param_map: dict) -> None:
        """Transform the parameters of a gate operation with a parameter map.

        Args:
            gate_op (QuantumGate): The gate operation to transform.
            param_map (Dict[str, Union[FloatLiteral, IntegerLiteral]]): The parameter map to use
                                                                        for transformation.

        Returns:
            None
        """
        for i, param in enumerate(gate_op.arguments):
            if isinstance(param, Identifier):
                gate_op.arguments[i] = param_map[param.name]
            # TODO : update the arg value in expressions not just SINGLE identifiers

    def _validate_gate_call(
        self, operation: QuantumGate, gate_definition: QuantumGateDefinition, qubits_in_op
    ) -> None:
        if len(operation.arguments) != len(gate_definition.arguments):
            self._print_err_location(operation.span)
            raise Qasm3ConversionError(
                f"""Parameter count mismatch for gate {operation.name.name}. Expected \
{len(gate_definition.arguments)} but got {len(operation.arguments)} in operation"""
            )

        if qubits_in_op != len(gate_definition.qubits):
            self._print_err_location(operation.span)
            raise Qasm3ConversionError(
                f"""Qubit count mismatch for gate {operation.name.name}. Expected \
{len(gate_definition.qubits)} but got {qubits_in_op} in operation"""
            )

    def _visit_custom_gate_operation(self, operation: QuantumGate, inverse: bool = False) -> None:
        """Visit a custom gate operation element recursively.

        Args:
            operation (QuantumGate): The gate operation to visit.
            inverse (bool): Whether the operation is an inverse operation. Defaults to False.

                            If True, the gate operation is applied in reverse order and the
                            inverse modifier is appended to each gate call.
                            See https://openqasm.com/language/gates.html#inverse-modifier
                            for more clarity.

        Returns:
            None
        """
        _log.debug("Visiting custom gate operation '%s'", str(operation))
        gate_name: str = operation.name.name
        gate_definition: QuantumGateDefinition = self._custom_gates[gate_name]
        op_qubits = self._get_op_qubits(operation, qir_form=False)

        self._validate_gate_call(operation, gate_definition, len(op_qubits))
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

        gate_definition_ops = copy.deepcopy(gate_definition.body)
        if inverse:
            gate_definition_ops.reverse()

        for gate_op in gate_definition_ops:
            if gate_op.name.name == gate_name:
                self._print_err_location(gate_op.span)
                raise Qasm3ConversionError(
                    f"Recursive definitions not allowed for gate {gate_name}"
                )

            # necessary to avoid modifying the original gate definition
            # in case the gate is reapplied
            gate_op_copy = copy.deepcopy(gate_op)
            if isinstance(gate_op, QuantumGate):
                self._transform_gate_params(gate_op_copy, param_map)
                self._transform_gate_qubits(gate_op_copy, qubit_map)
                # need to trickle the inverse down to the child!
                if inverse:
                    # span doesn't matter as we don't analyse it
                    gate_op_copy.modifiers.append(QuantumGateModifier(GateModifierName.inv, None))
                self._visit_generic_gate_operation(gate_op_copy)
            else:
                # TODO: add control flow support
                self._print_err_location(gate_op.span)
                raise Qasm3ConversionError(f"Unsupported gate definition statement {gate_op}")

    def _collapse_gate_modifiers(self, operation: QuantumGate) -> Tuple[Any, Any]:
        """Collapse the gate modifiers of a gate operation.
           Some analysis is required to get this result.
           The basic idea is that any power operation is multiplied and inversions are toggled.
           The placement of the inverse operation does not matter.

        Args:
            operation (QuantumGate): The gate operation to collapse modifiers for.

        Returns:
            Tuple[Any, Any]: The power and inverse values of the gate operation.
        """
        power_value, inverse_value = 1, False

        for modifier in operation.modifiers:
            modifier_name = modifier.modifier
            if modifier_name == GateModifierName.pow and modifier.argument is not None:
                current_power = self._evaluate_expression(modifier.argument)
                if current_power < 0:
                    inverse_value = not inverse_value
                power_value = power_value * abs(current_power)
            elif modifier_name == GateModifierName.inv:
                inverse_value = not inverse_value
            elif modifier_name in [GateModifierName.ctrl, GateModifierName.negctrl]:
                self._print_err_location(operation.span)
                raise NotImplementedError(
                    "Controlled modifier gates not yet supported in gate operation"
                )
        return (power_value, inverse_value)

    def _visit_generic_gate_operation(self, operation: QuantumGate) -> None:
        """Visit a gate operation element.

        Args:
            operation (QuantumGate): The gate operation to visit.

        Returns:
            None
        """

        power_value, inverse_value = self._collapse_gate_modifiers(operation)

        # Applying the inverse first and then the power is same as
        # apply the power first and then inverting the gate
        for _ in range(power_value):
            if operation.name.name in self._custom_gates:
                self._visit_custom_gate_operation(operation, inverse_value)
            else:
                self._visit_basic_gate_operation(operation, inverse_value)

    def _visit_classical_operation(self, statement: ClassicalDeclaration) -> None:
        """Visit a classical operation element.

        Args:
            statement (ClassicalType): The classical operation to visit.

        Returns:
            None
        """
        raise NotImplementedError("Classical declarations not yet supported")

    # pylint: disable-next=too-many-return-statements
    def _evaluate_expression(self, expression: Any) -> bool:
        """Evaluate an expression.

        Args:
            expression (Any): The expression to evaluate.

        Returns:
            bool: The result of the evaluation.

        Raises:
            Qasm3ConversionError: If the expression is not supported.
        """
        if isinstance(expression, (ImaginaryLiteral, DurationLiteral)):
            self._print_err_location(expression.span)
            raise Qasm3ConversionError(f"Unsupported expression type {type(expression)}")
        if isinstance(expression, (Identifier, IndexedIdentifier)):
            # we need to check our scope and context to get the value of the identifier
            # if it is a classical register, we can directly get the value
            # how to get the value of the identifier in the QIR??

            # TODO: extend this
            try:
                return qasm3_constants_map(expression.name)
            except Exception as err:  # pylint: disable=broad-exception-caught
                self._print_err_location(expression.span)
                raise Qasm3ConversionError(
                    f"Undefined identifier {expression.name} in {expression}"
                ) from err

        if isinstance(expression, BooleanLiteral):
            return expression.value
        if isinstance(expression, (IntegerLiteral, FloatLiteral)):
            return expression.value
        if isinstance(expression, UnaryExpression):
            op = expression.op.name
            if op == "-":
                op = "UMINUS"
            operand = self._evaluate_expression(expression.expression)
            if op == "~":
                if not isinstance(operand, int):
                    self._print_err_location(expression.span)
                    raise Qasm3ConversionError(
                        f"Unsupported expression type {type(operand)} in ~ operation"
                    )
            return qasm3_expression_op_map(op, operand)
        if isinstance(expression, BinaryExpression):
            lhs = self._evaluate_expression(expression.lhs)
            op = expression.op.name
            rhs = self._evaluate_expression(expression.rhs)
            return qasm3_expression_op_map(op, lhs, rhs)

        self._print_err_location(expression.span)
        raise Qasm3ConversionError(f"Unsupported expression type {type(expression)}")

    def _analyse_branch_condition(self, condition) -> bool:
        """
        Analyse the branching condition to determine the branch to take

        Args:
            condition (Any): The condition to analyse

        Returns:
            bool: The branch to take
        """

        if isinstance(condition, UnaryExpression):
            if condition.op.name != "!":
                self._print_err_location(condition.span)
                raise Qasm3ConversionError(
                    f"Unsupported unary expression '{condition.op.name}' in if condition"
                )
            return False
        if isinstance(condition, BinaryExpression):
            if condition.op.name != "==":
                self._print_err_location(condition.span)
                raise Qasm3ConversionError(
                    f"Unsupported binary expression '{condition.op.name}' in if condition"
                )
            if not isinstance(condition.lhs, IndexExpression):
                self._print_err_location(condition.span)
                raise Qasm3ConversionError(
                    f"Unsupported expression type '{type(condition.lhs)}' in if condition"
                )
            return condition.rhs.value != 0
        if not isinstance(condition, IndexExpression):
            self._print_err_location(condition.span)
            raise Qasm3ConversionError(
                f"Unsupported expression type '{type(condition)}' in if condition. "
                "Can only be a simple comparison"
            )
        return True

    def _get_branch_params(self, condition) -> Tuple[Union[int, None], Union[str, None]]:
        """
        Get the branch parameters from the branching condition

        Args:
            condition (Any): The condition to analyse

        Returns:
            Tuple[Union[int, None], Union[str, None]]: The branch parameters
        """
        if isinstance(condition, UnaryExpression):
            return condition.expression.index[0].value, condition.expression.collection.name
        if isinstance(condition, BinaryExpression):
            return condition.lhs.index[0].value, condition.lhs.collection.name
        if isinstance(condition, IndexExpression):
            return condition.index[0].value, condition.collection.name
        return None, None

    def _visit_branching_statement(self, statement: BranchingStatement) -> None:
        """Visit a branching statement element.

        Args:
            statement (BranchingStatement): The branching statement to visit.

        Returns:
            None
        """
        condition = statement.condition
        positive_branching = self._analyse_branch_condition(condition)

        if_block = statement.if_block
        if not statement.if_block:
            self._print_err_location(statement.span)
            raise Qasm3ConversionError("Missing if block")
        else_block = statement.else_block
        if not positive_branching:
            if_block, else_block = else_block, if_block

        reg_id, reg_name = self._get_branch_params(condition)

        if reg_name not in self._creg_size_map:
            raise Qasm3ConversionError(
                f"Missing register declaration for {reg_name} in {condition}"
            )
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
        if isinstance(statement, Include):
            pass
        elif isinstance(statement, QuantumMeasurementStatement):
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
        elif isinstance(statement, SubroutineDefinition):
            raise NotImplementedError("OpenQASM 3 subroutines not yet supported")
        elif isinstance(statement, AliasStatement):
            raise NotImplementedError("OpenQASM 3 aliases not yet supported")
        elif isinstance(statement, IODeclaration):
            raise NotImplementedError("OpenQASM 3 IO declarations not yet supported")
        else:
            # TODO : extend this
            self._print_err_location(statement.span)
            raise Qasm3ConversionError(f"Unsupported statement of type {type(statement)}")

    def ir(self) -> str:
        return str(self._module)

    def bitcode(self) -> bytes:
        return self._module.bitcode()
