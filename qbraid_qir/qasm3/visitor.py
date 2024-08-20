# Copyright (C) 2024 qBraid
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
import copy
import logging
from abc import ABCMeta, abstractmethod

# pylint: disable=too-many-instance-attributes,too-many-lines
from collections import deque
from typing import Union

import pyqir
import pyqir._native
import pyqir.rt
from pyqir import BasicBlock, Builder, Constant
from pyqir import IntType as qirIntType
from pyqir import PointerType

from .elements import Context, InversionOp, Qasm3Module, Variable
from .exceptions import Qasm3ConversionError
from .utils.expressions import Qasm3ExprEvaluator
from .utils.imports import *
from .utils.maps import (
    CONSTANTS_MAP,
    MAX_ARRAY_DIMENSIONS,
    SWITCH_BLACKLIST_STMTS,
    map_qasm_inv_op_to_pyqir_callable,
    map_qasm_op_to_pyqir_callable,
)
from .utils.visitor_utils import Qasm3VisitorUtils

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
        self._scope = deque([{}])
        self._context = deque([Context.GLOBAL])
        self._qubit_labels = {}
        self._clbit_labels = {}
        self._global_qreg_size_map = {}
        self._function_qreg_size_map = deque([])  # for nested functions
        self._function_qreg_transform_map = deque([])  # for nested functions
        self._global_creg_size_map = {}
        self._custom_gates = {}
        self._subroutine_defns = {}
        self._measured_qubits = {}
        self._initialize_runtime = initialize_runtime
        self._record_output = record_output
        self._curr_scope = 0
        self._label_scope_level = {self._curr_scope: set()}

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

    def _push_scope(self, scope: dict) -> None:
        if not isinstance(scope, dict):
            raise TypeError("Scope must be a dictionary")
        self._scope.append(scope)

    def _push_context(self, context: Context) -> None:
        if not isinstance(context, Context):
            raise TypeError("Context must be an instance of Context")
        self._context.append(context)

    def _pop_scope(self) -> None:
        if len(self._scope) == 0:
            raise IndexError("Scope list is empty, can not pop")
        self._scope.pop()

    def _restore_context(self) -> None:
        if len(self._context) == 0:
            raise IndexError("Context list is empty, can not pop")
        self._context.pop()

    def _get_parent_scope(self) -> dict:
        if len(self._scope) < 2:
            raise IndexError("Parent scope not available")
        return self._scope[-2]

    def _get_curr_scope(self) -> dict:
        if len(self._scope) == 0:
            raise IndexError("No scopes available to get")
        return self._scope[-1]

    def _get_curr_context(self) -> Context:
        if len(self._context) == 0:
            raise IndexError("No context available to get")
        return self._context[-1]

    def _get_global_scope(self) -> dict:
        if len(self._scope) == 0:
            raise IndexError("No scopes available to get")
        return self._scope[0]

    def _check_in_scope(self, var_name: str, curr_scope) -> bool:
        """
        Checks if a variable is in scope.

        Args:
            var_name (str): The name of the variable to check.

        Returns:
            bool: True if the variable is in scope, False otherwise.

        NOTE:

        - According to our definition of scope, we have a NEW DICT
          for each block scope also
        - Since all visible variables of the immediate parent are visible
          inside block scope, we have to check till we reach the boundary
          contexts
        - The "boundary" for a scope is either a FUNCTION / GATE context
          OR the GLOBAL context
        - Why then do we need a new scope for a block?
        - Well, if the block redeclares a variable in its scope, then the
          variable in the parent scope is shadowed
        - We need to remember the original value of the shadowed variable when we exit
          the block scope

        """
        global_scope = self._get_global_scope()
        if self._in_global_scope():
            return var_name in global_scope
        if self._in_function_scope() or self._in_gate_scope():
            if var_name in curr_scope:
                return True
            if var_name in global_scope:
                return global_scope[var_name].is_constant
        if self._in_block_scope():
            for scope, context in zip(reversed(self._scope), reversed(self._context)):
                if context != Context.BLOCK:
                    return var_name in scope
                if var_name in scope:
                    return True
        return False

    def _get_from_visible_scope(self, var_name: str) -> Union[Variable, None]:
        """
        Retrieves a variable from the visible scope.

        Args:
            var_name (str): The name of the variable to retrieve.

        Returns:
            Union[Variable, None]: The variable if found, None otherwise.
        """
        global_scope = self._get_global_scope()
        curr_scope = self._get_curr_scope()

        if self._in_global_scope():
            return global_scope.get(var_name, None)
        if self._in_function_scope() or self._in_gate_scope():
            if var_name in curr_scope:
                return curr_scope[var_name]
            if var_name in global_scope and global_scope[var_name].is_constant:
                return global_scope[var_name]
        if self._in_block_scope():
            for scope, context in zip(reversed(self._scope), reversed(self._context)):
                if context != Context.BLOCK:
                    return scope.get(var_name, None)
                if var_name in scope:
                    return scope[var_name]
                    # keep on checking
        return None

    def _add_var_in_scope(self, variable: Variable) -> None:
        """Add a variable to the current scope.

        Args:
            variable (Variable): The variable to add.

        Raises:
            ValueError: If the variable already exists in the current scope.
        """
        curr_scope = self._get_curr_scope()
        if variable.name in curr_scope:
            raise ValueError(f"Variable '{variable.name}' already exists in current scope")
        curr_scope[variable.name] = variable

    def _update_var_in_scope(self, variable: Variable) -> None:
        """
        Updates the variable in the current scope.

        Args:
            variable (Variable): The variable to be updated.

        Raises:
            ValueError: If no scope is available to update.
        """
        if len(self._scope) == 0:
            raise ValueError("No scope available to update")

        global_scope = self._get_global_scope()
        curr_scope = self._get_curr_scope()

        if self._in_global_scope():
            global_scope[variable.name] = variable
        if self._in_function_scope() or self._in_gate_scope():
            curr_scope[variable.name] = variable
        if self._in_block_scope():
            for scope, context in zip(reversed(self._scope), reversed(self._context)):
                if context != Context.BLOCK:
                    scope[variable.name] = variable
                    break
                if variable.name in scope:
                    scope[variable.name] = variable
                    break
                continue

    def _in_global_scope(self) -> bool:
        return len(self._scope) == 1 and self._get_curr_context() == Context.GLOBAL

    def _in_function_scope(self) -> bool:
        return len(self._scope) > 1 and self._get_curr_context() == Context.FUNCTION

    def _in_gate_scope(self) -> bool:
        return len(self._scope) > 1 and self._get_curr_context() == Context.GATE

    def _in_block_scope(self) -> bool:  # block scope is for if/else/for/while constructs
        return len(self._scope) > 1 and self._get_curr_context() == Context.BLOCK

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
            register (QubitDeclaration | ClassicalDeclaration): The register name and size.

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

        size_map = self._global_qreg_size_map if is_qubit else self._global_creg_size_map
        label_map = self._qubit_labels if is_qubit else self._clbit_labels

        if self._check_in_scope(register_name, self._get_curr_scope()):
            Qasm3VisitorUtils.print_err_location(register.span)
            raise Qasm3ConversionError(
                f"Invalid declaration of register with name '{register_name}'"
            )

        if is_qubit:  # as bit type vars are added in classical decl handler
            self._add_var_in_scope(
                Variable(
                    register_name,
                    QubitDeclaration,
                    register_size,
                    None,
                    None,
                    False,
                )
            )

        for i in range(register_size):
            # required if indices are not used while applying a gate or measurement
            size_map[f"{register_name}"] = register_size
            label_map[f"{register_name}_{i}"] = current_size + i

        self._label_scope_level[self._curr_scope].add(register_name)

        _log.debug("Added labels for register '%s'", str(register))

    def _get_qubits_from_range_definition(
        self, range_def: RangeDefinition, qreg_size: int, is_qubit_reg: bool
    ) -> list[int]:
        """Get the qubits from a range definition.
        Args:
            range_def (RangeDefinition): The range definition to get qubits from.
            qreg_size (int): The size of the register.
            is_qubit_reg (bool): Whether the register is a qubit register.
        Returns:
            list[int]: The list of qubit identifiers.
        """
        start_qid = (
            0
            if range_def.start is None
            else Qasm3ExprEvaluator.evaluate_expression(self, range_def.start)
        )
        end_qid = (
            qreg_size
            if range_def.end is None
            else Qasm3ExprEvaluator.evaluate_expression(self, range_def.end)
        )
        step = (
            1
            if range_def.step is None
            else Qasm3ExprEvaluator.evaluate_expression(self, range_def.step)
        )
        Qasm3VisitorUtils.validate_register_index(start_qid, qreg_size, qubit=is_qubit_reg)
        Qasm3VisitorUtils.validate_register_index(end_qid - 1, qreg_size, qubit=is_qubit_reg)
        return list(range(start_qid, end_qid, step))

    def _check_if_name_in_scope(self, name: str, operation) -> None:
        """Check if a name is in scope to avoid duplicate declarations.
        Args:
            name (str): The name to check.
        Returns:
            bool: Whether the name is in scope.
        """
        for scope_level in range(0, self._curr_scope + 1):
            if name in self._label_scope_level[scope_level]:
                return None
        Qasm3VisitorUtils.print_err_location(operation.span)
        raise Qasm3ConversionError(f"Variable {name} not in scope for operation {operation}")

    def _get_op_qubits(self, operation, qreg_size_map, qir_form: bool = True) -> list[pyqir.qubit]:
        """Get the qubits for the operation.

        Args:
            operation (Any): The operation to get qubits for.

        Returns:
            list[pyqir.qubit]: The qubits for the operation.
        """
        qir_qubits = []
        openqasm_qubits = []
        visited_qubits = set()
        qubit_list = operation.qubits if isinstance(operation.qubits, list) else [operation.qubits]

        for qubit in qubit_list:
            if isinstance(qubit, IndexedIdentifier):
                qreg_name = qubit.name.name
            else:
                qreg_name = qubit.name

            if qreg_name not in qreg_size_map:
                Qasm3VisitorUtils.print_err_location(operation.span)
                raise Qasm3ConversionError(
                    f"Missing register declaration for {qreg_name} in operation {operation}"
                )
            self._check_if_name_in_scope(qreg_name, operation)
            qreg_size = qreg_size_map[qreg_name]

            if isinstance(qubit, IndexedIdentifier):
                if isinstance(qubit.indices[0][0], RangeDefinition):
                    qids = self._get_qubits_from_range_definition(
                        qubit.indices[0][0], qreg_size, is_qubit_reg=True
                    )
                else:
                    qid = Qasm3ExprEvaluator.evaluate_expression(self, qubit.indices[0][0])
                    Qasm3VisitorUtils.validate_register_index(qid, qreg_size, qubit=True)
                    qids = [qid]
                openqasm_qubits.extend(
                    [IndexedIdentifier(Identifier(qreg_name), [[IntegerLiteral(i)]]) for i in qids]
                )
            else:
                qids = list(range(qreg_size))
                openqasm_qubits.extend(
                    [IndexedIdentifier(Identifier(qreg_name), [[IntegerLiteral(i)]]) for i in qids]
                )

            if qir_form:
                qreg_qids = [self._qubit_labels[f"{qreg_name}_{i}"] for i in qids]
                for qid in qreg_qids:
                    if qid in visited_qubits:
                        Qasm3VisitorUtils.print_err_location(operation.span)
                        raise Qasm3ConversionError(f"Duplicate qubit {qreg_name}[{qid}] argument")
                    visited_qubits.add(qid)
                qir_qubits.extend([pyqir.qubit(self._module.context, n) for n in qreg_qids])

        return qir_qubits if qir_form else openqasm_qubits

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
        # TODO: handle in-function measurements
        source_name = source.name
        if isinstance(source, IndexedIdentifier):
            source_name = source.name.name
            if isinstance(source.indices[0][0], RangeDefinition):
                Qasm3VisitorUtils.print_err_location(statement.span)
                raise Qasm3ConversionError(
                    f"Range based measurement {statement} not supported at the moment"
                )
            source_id = source.indices[0][0].value

        target_name = target.name
        if isinstance(target, IndexedIdentifier):
            target_name = target.name.name
            if isinstance(target.indices[0][0], RangeDefinition):
                Qasm3VisitorUtils.print_err_location(statement.span)
                raise Qasm3ConversionError(
                    f"Range based measurement {statement} not supported at the moment"
                )
            target_id = target.indices[0][0].value

        if source_name not in self._global_qreg_size_map:
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(
                f"Missing register declaration for {source_name} in measurement "
                f"operation {statement}"
            )
        if target_name not in self._global_creg_size_map:
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(
                f"Missing register declaration for {target_name} in measurement "
                f"operation {statement}"
            )

        def _build_qir_measurement(
            src_name: str,
            src_id: Union[int, None],
            target_name: str,
            target_id: Union[int, None],
        ):
            src_id = 0 if src_id is None else src_id
            target_id = 0 if target_id is None else target_id

            source_qubit = pyqir.qubit(
                self._module.context, self._qubit_labels[f"{src_name}_{src_id}"]
            )
            result = pyqir.result(
                self._module.context,
                self._clbit_labels[f"{target_name}_{target_id}"],
            )
            pyqir._native.mz(self._builder, source_qubit, result)

        if source_id is None and target_id is None:
            if self._global_qreg_size_map[source_name] != self._global_creg_size_map[target_name]:
                Qasm3VisitorUtils.print_err_location(statement.span)
                raise Qasm3ConversionError(
                    f"Register sizes of {source_name} and {target_name} do not match "
                    "for measurement operation"
                )
            for i in range(self._global_qreg_size_map[source_name]):
                _build_qir_measurement(source_name, i, target_name, i)
        else:
            Qasm3VisitorUtils.validate_register_index(
                source_id, self._global_qreg_size_map[source_name], qubit=True
            )
            Qasm3VisitorUtils.validate_register_index(
                target_id, self._global_creg_size_map[target_name], qubit=False
            )
            _build_qir_measurement(source_name, source_id, target_name, target_id)

    def _visit_reset(self, statement: QuantumReset) -> None:
        """Visit a reset statement element.

        Args:
            statement (QuantumReset): The reset statement to visit.

        Returns:
            None
        """
        _log.debug("Visiting reset statement '%s'", str(statement))
        if len(self._function_qreg_size_map) > 0:  # atleast in SOME function scope
            # transform qubits to use the global qreg identifiers
            statement.qubits = self._transform_function_qubits(
                statement, self._function_qreg_size_map[-1], self._function_qreg_transform_map[-1]
            )
        qubit_ids = self._get_op_qubits(statement, self._global_qreg_size_map, True)

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
        if len(self._function_qreg_size_map) > 0:  # atleast in SOME function scope
            # transform qubits to use the global qreg identifiers
            barrier.qubits = self._transform_function_qubits(
                barrier, self._function_qreg_size_map[-1], self._function_qreg_transform_map[-1]
            )

        barrier_qubits = self._get_op_qubits(barrier, self._global_qreg_size_map)
        total_qubit_count = sum(self._global_qreg_size_map.values())
        if len(barrier_qubits) == total_qubit_count:
            pyqir._native.barrier(self._builder)
        else:
            Qasm3VisitorUtils.print_err_location(barrier.span)
            raise NotImplementedError(
                "Barrier operation on a qubit subset is not supported in pyqir"
            )

    def _get_op_parameters(self, operation: QuantumGate) -> list[float]:
        """Get the parameters for the operation.

        Args:
            operation (QuantumGate): The operation to get parameters for.

        Returns:
            list[float]: The parameters for the operation.
        """
        param_list = []
        for param in operation.arguments:
            param_value = Qasm3ExprEvaluator.evaluate_expression(self, param)
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
            Qasm3VisitorUtils.print_err_location(definition.span)
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
        op_qubits = self._get_op_qubits(operation, self._global_qreg_size_map)
        inverse_action = None
        if not inverse:
            qir_func, op_qubit_count = map_qasm_op_to_pyqir_callable(op_name)
        else:
            # in basic gates, inverse action only affects the rotation gates
            qir_func, op_qubit_count, inverse_action = map_qasm_inv_op_to_pyqir_callable(op_name)

        op_parameters = None

        if len(op_qubits) % op_qubit_count != 0:
            Qasm3VisitorUtils.print_err_location(operation.span)
            raise Qasm3ConversionError(
                f"Invalid number of qubits {len(op_qubits)} for operation {operation.name.name}"
            )

        if len(operation.arguments) > 0:  # parametric gate
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
        op_qubits = self._get_op_qubits(operation, self._global_qreg_size_map, qir_form=False)

        Qasm3VisitorUtils.validate_gate_call(operation, gate_definition, len(op_qubits))
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

        self._push_context(Context.GATE)

        for gate_op in gate_definition_ops:
            if gate_op.name.name == gate_name:
                Qasm3VisitorUtils.print_err_location(gate_op.span)
                raise Qasm3ConversionError(
                    f"Recursive definitions not allowed for gate {gate_name}"
                )

            # necessary to avoid modifying the original gate definition
            # in case the gate is reapplied
            gate_op_copy = copy.deepcopy(gate_op)
            if isinstance(gate_op, QuantumGate):
                Qasm3VisitorUtils.transform_gate_params(gate_op_copy, param_map)
                Qasm3VisitorUtils.transform_gate_qubits(gate_op_copy, qubit_map)
                # need to trickle the inverse down to the child gates
                if inverse:
                    # span doesn't matter as we don't analyse it
                    gate_op_copy.modifiers.append(QuantumGateModifier(GateModifierName.inv, None))
                self._visit_generic_gate_operation(gate_op_copy)
            else:
                # TODO: add control flow support
                Qasm3VisitorUtils.print_err_location(gate_op.span)
                raise Qasm3ConversionError(f"Unsupported gate definition statement {gate_op}")

        self._restore_context()

    def _collapse_gate_modifiers(self, operation: QuantumGate) -> tuple:
        """Collapse the gate modifiers of a gate operation.
           Some analysis is required to get this result.
           The basic idea is that any power operation is multiplied and inversions are toggled.
           The placement of the inverse operation does not matter.

        Args:
            operation (QuantumGate): The gate operation to collapse modifiers for.

        Returns:
            tuple[Any, Any]: The power and inverse values of the gate operation.
        """
        power_value, inverse_value = 1, False

        for modifier in operation.modifiers:
            modifier_name = modifier.modifier
            if modifier_name == GateModifierName.pow and modifier.argument is not None:
                current_power = Qasm3ExprEvaluator.evaluate_expression(self, modifier.argument)
                if current_power < 0:
                    inverse_value = not inverse_value
                power_value = power_value * abs(current_power)
            elif modifier_name == GateModifierName.inv:
                inverse_value = not inverse_value
            elif modifier_name in [
                GateModifierName.ctrl,
                GateModifierName.negctrl,
            ]:
                Qasm3VisitorUtils.print_err_location(operation.span)
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
        operation = copy.deepcopy(operation)

        # only needs to be done once for a gate operation
        if not self._in_gate_scope() and len(self._function_qreg_size_map) > 0:
            # we are in SOME function scope
            # transform qubits to use the global qreg identifiers
            operation.qubits = self._transform_function_qubits(
                operation, self._function_qreg_size_map[-1], self._function_qreg_transform_map[-1]
            )
        # Applying the inverse first and then the power is same as
        # apply the power first and then inverting the result
        for _ in range(power_value):
            if operation.name.name in self._custom_gates:
                self._visit_custom_gate_operation(operation, inverse_value)
            else:
                self._visit_basic_gate_operation(operation, inverse_value)

    def _visit_constant_declaration(self, statement: ConstantDeclaration) -> None:
        """
        Visit a constant declaration element. Const can only be declared for scalar
        type variables and not arrays. Assignment is mandatory in constant declaration.

        Args:
            statement (ConstantDeclaration): The constant declaration to visit.

        Returns:
            None
        """

        var_name = statement.identifier.name

        if var_name in CONSTANTS_MAP:
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(f"Can not declare variable with keyword name {var_name}")

        if self._check_in_scope(var_name, self._get_curr_scope()):
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(f"Re-declaration of variable {var_name}")

        init_value = Qasm3ExprEvaluator.evaluate_expression(
            self, statement.init_expression, const_expr=True
        )

        base_type = statement.type
        if isinstance(base_type, BoolType):
            base_size = 1
        elif base_type.size is None:
            base_size = 32  # default for now
        else:
            base_size = Qasm3ExprEvaluator.evaluate_expression(
                self, base_type.size, const_expr=True
            )
            if not isinstance(base_size, int) or base_size <= 0:
                Qasm3VisitorUtils.print_err_location(statement.span)
                raise Qasm3ConversionError(f"Invalid base size {base_size} for variable {var_name}")

        variable = Variable(var_name, base_type, base_size, [], init_value, is_constant=True)

        # cast + validation
        variable.value = Qasm3VisitorUtils.validate_variable_assignment_value(variable, init_value)

        self._add_var_in_scope(variable)

    # pylint: disable=too-many-branches
    def _visit_classical_declaration(self, statement: ClassicalDeclaration) -> None:
        """Visit a classical operation element.

        Args:
            statement (ClassicalType): The classical operation to visit.

        Returns:
            None
        """
        var_name = statement.identifier.name
        if var_name in CONSTANTS_MAP:
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(f"Can not declare variable with keyword name {var_name}")
        if self._check_in_scope(var_name, self._get_curr_scope()):
            if self._in_block_scope() and var_name not in self._get_curr_scope():
                # we can re-declare variables once in block scope even if they are
                # present in the parent scope
                # Eg.
                # int a = 10;
                # { int a = 20; // valid
                # }
                pass
            else:
                Qasm3VisitorUtils.print_err_location(statement.span)
                raise Qasm3ConversionError(f"Re-declaration of variable {var_name}")

        init_value = None
        base_type = statement.type
        final_dimensions = []

        if isinstance(base_type, ArrayType):
            dimensions = base_type.dimensions

            if len(dimensions) > MAX_ARRAY_DIMENSIONS:
                Qasm3VisitorUtils.print_err_location(statement.span)
                raise Qasm3ConversionError(
                    f"Invalid dimensions {len(dimensions)} for array declaration for {var_name}. "
                    f"Max allowed dimensions is {MAX_ARRAY_DIMENSIONS}"
                )

            base_type = base_type.base_type
            num_elements = 1
            for dim in dimensions:
                dim_value = Qasm3ExprEvaluator.evaluate_expression(self, dim)
                if not isinstance(dim_value, int) or dim_value <= 0:
                    Qasm3VisitorUtils.print_err_location(statement.span)
                    raise Qasm3ConversionError(
                        f"Invalid dimension size {dim_value} in array declaration for {var_name}"
                    )
                final_dimensions.append(dim_value)
                num_elements *= dim_value

            init_value = None
            for dim in reversed(final_dimensions):
                init_value = [init_value for _ in range(dim)]

        if statement.init_expression:
            if isinstance(statement.init_expression, ArrayLiteral):
                init_value = self._evaluate_array_initialization(
                    statement.init_expression, final_dimensions, base_type
                )
            else:
                init_value = Qasm3ExprEvaluator.evaluate_expression(self, statement.init_expression)
        base_size = 1
        if not isinstance(base_type, BoolType):
            base_size = (
                32
                if base_type.size is None
                else Qasm3ExprEvaluator.evaluate_expression(self, base_type.size)
            )

        if not isinstance(base_size, int) or base_size <= 0:
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(f"Invalid base size {base_size} for variable {var_name}")

        if isinstance(base_type, Qasm3FloatType) and base_size not in [32, 64]:
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(
                f"Invalid base size {base_size} for float variable {var_name}"
            )

        variable = Variable(var_name, base_type, base_size, final_dimensions, init_value)

        if statement.init_expression:
            if isinstance(init_value, list):
                Qasm3VisitorUtils.validate_array_assignment_values(
                    variable, variable.dims, init_value
                )
            else:
                variable.value = Qasm3VisitorUtils.validate_variable_assignment_value(
                    variable, init_value
                )

        self._add_var_in_scope(variable)

    def _visit_classical_assignment(self, statement: ClassicalAssignment) -> None:
        """Visit a classical assignment element.

        Args:
            statement (ClassicalAssignment): The classical assignment to visit.

        Returns:
            None
        """
        lvalue = statement.lvalue
        var_name = lvalue.name

        if isinstance(lvalue, IndexedIdentifier):
            var_name = var_name.name

        var = self._get_from_visible_scope(var_name)

        if var is None:
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(f"Undefined variable {var_name} in assignment")

        if var.is_constant:
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(f"Assignment to constant variable {var_name} not allowed")

        var_value = Qasm3ExprEvaluator.evaluate_expression(self, statement.rvalue)

        # currently we support single array assignment only
        # range based assignment not supported yet

        # cast + validation
        var_value = Qasm3VisitorUtils.validate_variable_assignment_value(var, var_value)

        # handle assignment for arrays
        if isinstance(lvalue, IndexedIdentifier):
            # stupid indices structure in openqasm :/
            if len(lvalue.indices[0]) > 1:
                indices = lvalue.indices[0]
            else:
                indices = [idx[0] for idx in lvalue.indices]

            validated_indices = Qasm3VisitorUtils.analyse_classical_indices(
                indices, self._get_from_visible_scope(var_name)
            )
            Qasm3VisitorUtils.update_array_element(var.value, validated_indices, var_value)
        else:
            var.value = var_value

        self._update_var_in_scope(var)

    def _evaluate_array_initialization(
        self, array_literal: ArrayLiteral, dimensions: list[int], base_type
    ) -> list:
        """Evaluate an array initialization.

        Args:
            array_literal (ArrayLiteral): The array literal to evaluate.
            dimensions (list[int]): The dimensions of the array.
            base_type (Any): The base type of the array.

        Returns:
            list: The evaluated array initialization.
        """
        init_values = []

        for value in array_literal.values:
            if isinstance(value, ArrayLiteral):
                init_values.append(
                    self._evaluate_array_initialization(value, dimensions[1:], base_type)
                )
            else:
                eval_value = Qasm3ExprEvaluator.evaluate_expression(self, value)
                init_values.append(eval_value)

        return init_values

    def _visit_branching_statement(self, statement: BranchingStatement) -> None:
        """Visit a branching statement element.

        Args:
            statement (BranchingStatement): The branching statement to visit.

        Returns:
            None
        """
        self._push_context(Context.BLOCK)
        self._push_scope({})
        self._curr_scope += 1
        self._label_scope_level[self._curr_scope] = set()

        condition = statement.condition
        positive_branching = Qasm3VisitorUtils.analyse_branch_condition(condition)

        if_block = statement.if_block
        if not statement.if_block:
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError("Missing if block")
        else_block = statement.else_block
        if not positive_branching:
            if_block, else_block = else_block, if_block

        reg_id, reg_name = Qasm3VisitorUtils.get_branch_params(condition)

        if reg_name not in self._global_creg_size_map:
            raise Qasm3ConversionError(
                f"Missing register declaration for {reg_name} in {condition}"
            )
        Qasm3VisitorUtils.validate_register_index(
            reg_id, self._global_creg_size_map[reg_name], qubit=False
        )

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

        del self._label_scope_level[self._curr_scope]
        self._curr_scope -= 1
        self._pop_scope()
        self._restore_context()

    def _visit_forin_loop(self, statement: ForInLoop) -> None:
        # Compute loop variable values
        if isinstance(statement.set_declaration, RangeDefinition):
            init_exp = statement.set_declaration.start
            startval = Qasm3ExprEvaluator.evaluate_expression(self, init_exp)
            range_def = statement.set_declaration
            stepval = (
                1
                if range_def.step is None
                else Qasm3ExprEvaluator.evaluate_expression(self, range_def.step)
            )
            endval = Qasm3ExprEvaluator.evaluate_expression(self, range_def.end)
            irange = list(range(startval, endval + stepval, stepval))
        elif isinstance(statement.set_declaration, DiscreteSet):
            init_exp = statement.set_declaration.values[0]
            irange = [
                Qasm3ExprEvaluator.evaluate_expression(self, exp)
                for exp in statement.set_declaration.values
            ]
        else:
            raise Qasm3ConversionError(
                f"Unexpected type {type(statement.set_declaration)} of set_declaration in loop."
            )

        i = None  # will store iteration Variable to update to loop scope

        for ival in irange:
            self._push_context(Context.BLOCK)
            self._push_scope({})

            # Initialize loop variable in loop scope
            # need to re-declare as we discard the block scope in subsequent
            # iterations of the loop
            self._visit_classical_declaration(
                ClassicalDeclaration(statement.type, statement.identifier, init_exp)
            )
            i = self._get_from_visible_scope(statement.identifier.name)

            # Update scope with current value of loop Variable
            i.value = ival
            self._update_var_in_scope(i)

            for stmt in statement.block:
                self.visit_statement(stmt)

            # scope not persistent between loop iterations
            self._pop_scope()
            self._restore_context()

    def _visit_subroutine_definition(self, statement: SubroutineDefinition) -> None:
        """Visit a subroutine definition element.
           Reference: https://openqasm.com/language/subroutines.html#subroutines

        Args:
            statement (SubroutineDefinition): The subroutine definition to visit.

        Returns:
            None
        """
        fn_name = statement.name.name

        if fn_name in CONSTANTS_MAP:
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(f"Subroutine name '{fn_name}' is a reserved keyword")

        if fn_name in self._subroutine_defns:
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(f"Redefinition of subroutine '{fn_name}'")

        if self._check_in_scope(fn_name, self._get_curr_scope()):
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(
                f"Can not declare subroutine with name '{fn_name}' "
                "as it is already declared as a variable"
            )

        self._subroutine_defns[fn_name] = statement

    def _transform_function_qubits(
        self, q_op, formal_qreg_sizes: dict[str:int], qubit_map: dict[tuple:tuple]
    ) -> list:
        """Transform the qubits of a function call to the actual qubits.

        Args:
            gate_op : The quantum operation to transform.
            formal_qreg_sizes (dict[str: int]): The formal qubit register sizes.
            qubit_map (dict[tuple: tuple]): The mapping of formal qubits to actual qubits.

        Returns:
            None
        """
        expanded_op_qubits = self._get_op_qubits(q_op, formal_qreg_sizes, qir_form=False)

        transformed_qubits = []
        for qubit in expanded_op_qubits:
            formal_qreg_name = qubit.name.name
            formal_qreg_idx = qubit.indices[0][0].value

            # replace the formal qubit with the actual qubit
            actual_qreg_name, actual_qreg_idx = qubit_map[(formal_qreg_name, formal_qreg_idx)]
            transformed_qubits.append(
                IndexedIdentifier(
                    Identifier(actual_qreg_name),
                    [[IntegerLiteral(actual_qreg_idx)]],
                )
            )

        return transformed_qubits

    def _get_target_qubits(self, target, qreg_size_map, target_name):
        """Get the target qubits of a statement.

        Args:
            target (Any): The target of the statement.
            qreg_size_map (dict[str: int]): The quantum register size map.
            target_name (str): The name of the register.

        Returns:
            tuple: The target qubits.
        """
        target_qids = None
        target_qubits_size = None

        if isinstance(target, Identifier):  # "(q);"
            target_qids = list(range(qreg_size_map[target_name]))
            target_qubits_size = qreg_size_map[target_name]

        elif isinstance(target, IndexExpression):
            if isinstance(target.index, DiscreteSet):  # "(q[{0,1}]);"
                target_qids = Qasm3VisitorUtils.extract_values_from_discrete_set(target.index)
                for qid in target_qids:
                    Qasm3VisitorUtils.validate_register_index(
                        qid, qreg_size_map[target_name], qubit=True
                    )
                target_qubits_size = len(target_qids)
            elif isinstance(target.index[0], (IntegerLiteral, Identifier)):  # "(q[0]); OR (q[i]);"
                target_qids = [Qasm3ExprEvaluator.evaluate_expression(self, target.index[0])]
                Qasm3VisitorUtils.validate_register_index(
                    target_qids[0], qreg_size_map[target_name], qubit=True
                )
                target_qubits_size = 1
            elif isinstance(target.index[0], RangeDefinition):  # "(q[0:1:2]);"
                target_qids = self._get_qubits_from_range_definition(
                    target.index[0],
                    qreg_size_map[target_name],
                    is_qubit_reg=True,
                )
                target_qubits_size = len(target_qids)
        return target_qids, target_qubits_size

    # pylint: disable=too-many-locals, too-many-statements
    def _visit_function_call(self, statement: FunctionCall) -> None:
        """Visit a function call element.

        Args:
            statement (FunctionCall): The function call to visit.
        Returns:
            None

        """
        fn_name = statement.name.name
        if fn_name not in self._subroutine_defns:
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(f"Undefined subroutine '{fn_name}' was called")

        subroutine_def = self._subroutine_defns[fn_name]

        if len(statement.arguments) != len(subroutine_def.arguments):
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(
                f"Parameter count mismatch for subroutine '{fn_name}'. Expected "
                f"{len(subroutine_def.arguments)} but got {len(statement.arguments)} in call"
            )

        duplicate_qubit_detect_map = {}
        qubit_transform_map = {}  # {(formal arg, idx) : (actual arg, idx)}
        formal_qreg_size_map = {}

        quantum_vars, classical_vars = [], []

        def _validate_unique_qubits(reg_name, indices):
            """
            Validates that the qubits in the given register are unique.

            Args:
                reg_name (str): The name of the register.
                indices (list): A list of indices representing the qubits.

            Raises:
                Qasm3ConversionError: If duplicate qubits are found in the function call.
            """
            if reg_name not in duplicate_qubit_detect_map:
                duplicate_qubit_detect_map[reg_name] = set(indices)
            else:
                for idx in indices:
                    if idx in duplicate_qubit_detect_map[reg_name]:
                        Qasm3VisitorUtils.print_err_location(statement.span)
                        raise Qasm3ConversionError(
                            f"Duplicate qubit argument '{reg_name}[{idx}]' "
                            f"in function call for '{fn_name}'"
                        )

        def _process_classical_arg(formal_arg, actual_arg, actual_arg_name):
            """
            Process the classical argument for a function call.

            Args:
                formal_arg (FormalArgument): The formal argument of the function.
                actual_arg (ActualArgument): The actual argument passed to the function.
                actual_arg_name (str): The name of the actual argument.

            Raises:
                Qasm3ConversionError: If the actual argument is a qubit register instead
                                    of a classical argument.
                Qasm3ConversionError: If the actual argument is an undefined variable.
            """
            # 1. variable mapping is equivalent to declaring the variable
            #     with the formal argument name and doing classical assignment
            #     in the scope of the function
            if actual_arg_name:
                if actual_arg_name in self._global_qreg_size_map:
                    Qasm3VisitorUtils.print_err_location(statement.span)
                    raise Qasm3ConversionError(
                        f"Expecting classical argument for '{formal_arg.name.name}'. "
                        f"Qubit register '{actual_arg_name}' found for function '{fn_name}'"
                    )

                # 2. as we have pushed the scope for fn, we need to check in parent
                #    scope for argument validation
                if not self._check_in_scope(actual_arg_name, self._get_curr_scope()):
                    Qasm3VisitorUtils.print_err_location(statement.span)
                    raise Qasm3ConversionError(
                        f"Undefined variable '{actual_arg_name}' used for function '{fn_name}'"
                    )

            # NOTE: actual_argument can also be an EXPRESSION
            # Better to just evaluate that expression and assign that value later to
            # the formal argument
            actual_arg_value = Qasm3ExprEvaluator.evaluate_expression(self, actual_arg)

            # save this value to be updated later in scope
            classical_vars.append(
                Variable(
                    formal_arg.name.name,
                    formal_arg.type,
                    Qasm3ExprEvaluator.evaluate_expression(self, formal_arg.type.size),
                    None,
                    actual_arg_value,
                    False,
                )
            )

        def _process_quantum_arg(formal_arg, actual_arg, formal_reg_name, actual_arg_name):
            """
            Process a quantum argument in the QASM3 visitor.

            Args:
                formal_arg (Qasm3Expression): The formal argument in the function signature.
                actual_arg (Qasm3Expression): The actual argument passed to the function.
                formal_reg_name (str): The name of the formal quantum register.
                actual_arg_name (str): The name of the actual quantum register.

            Returns:
                list: The list of actual qubit ids.

            Raises:
                Qasm3ConversionError: If there is a mismatch in the quantum register size or
                                      if the actual argument is not a qubit register.

            """
            formal_qubit_size = Qasm3ExprEvaluator.evaluate_expression(
                self, formal_arg.size, reqd_type=Qasm3IntType, const_expr=True
            )
            if formal_qubit_size is None:
                formal_qubit_size = 1
            formal_qreg_size_map[formal_reg_name] = formal_qubit_size

            # we expect that actual arg is qubit type only
            if actual_arg_name not in self._global_qreg_size_map:
                Qasm3VisitorUtils.print_err_location(statement.span)
                raise Qasm3ConversionError(
                    f"Expecting qubit argument for '{formal_reg_name}'."
                    f" Qubit register '{actual_arg_name}' not found for function '{fn_name}'"
                )
            self._label_scope_level[self._curr_scope].add(formal_reg_name)

            actual_qids, actual_qubits_size = self._get_target_qubits(
                actual_arg, self._global_qreg_size_map, actual_arg_name
            )

            if formal_qubit_size != actual_qubits_size:
                Qasm3VisitorUtils.print_err_location(statement.span)
                raise Qasm3ConversionError(
                    f"Qubit register size mismatch for function '{fn_name}'. "
                    f"Expected {formal_qubit_size} in variable '{formal_reg_name}' "
                    f"but got {actual_qubits_size}"
                )

            quantum_vars.append(
                Variable(formal_reg_name, QubitDeclaration, formal_qubit_size, None, None, False)
            )

            _validate_unique_qubits(actual_arg_name, actual_qids)
            for idx, qid in enumerate(actual_qids):
                qubit_transform_map[(formal_reg_name, idx)] = (actual_arg_name, qid)

        for actual_arg, formal_arg in zip(statement.arguments, subroutine_def.arguments):
            actual_arg_name = None
            if isinstance(actual_arg, Identifier):
                actual_arg_name = actual_arg.name
            elif isinstance(actual_arg, IndexExpression):
                actual_arg_name = actual_arg.collection.name

            if isinstance(formal_arg, ClassicalArgument):
                # TODO: add the handling for access : mutable / readonly arrays
                _process_classical_arg(formal_arg, actual_arg, actual_arg_name)
            else:
                _process_quantum_arg(formal_arg, actual_arg, formal_arg.name.name, actual_arg_name)

        self._push_scope({})
        self._curr_scope += 1
        self._label_scope_level[self._curr_scope] = set()
        self._push_context(Context.FUNCTION)

        for var in quantum_vars:
            self._add_var_in_scope(var)

        for var in classical_vars:
            self._add_var_in_scope(var)

        # push qubit transform maps
        self._function_qreg_size_map.append(formal_qreg_size_map)
        self._function_qreg_transform_map.append(qubit_transform_map)

        for function_op in subroutine_def.body:
            if isinstance(function_op, ReturnStatement):
                return_statement = copy.deepcopy(function_op)
                break
            self.visit_statement(copy.deepcopy(function_op))

        return_value = Qasm3ExprEvaluator.evaluate_expression(self, return_statement.expression)
        return_value = Qasm3VisitorUtils.validate_return_statement(
            subroutine_def, return_statement, return_value
        )

        # remove qubit transformation map
        self._function_qreg_transform_map.pop()
        self._function_qreg_size_map.pop()

        self._restore_context()
        del self._label_scope_level[self._curr_scope]
        self._curr_scope -= 1
        self._pop_scope()

        return return_value if subroutine_def.return_type is not None else None

    def _visit_while_loop(self, statement: WhileLoop) -> None:
        pass

    def _visit_alias_statement(self, statement: AliasStatement) -> None:
        """Visit an alias statement element.

        Args:
            statement (AliasStatement): The alias statement to visit.

        Returns:
            None
        """
        # pylint: disable=too-many-branches
        target = statement.target
        value = statement.value

        alias_reg_name = target.name
        alias_reg_size = None
        aliased_reg_name = None
        aliased_reg_size = None

        # Alias should not be redeclared earlier as a variable or a constant
        if self._check_in_scope(alias_reg_name, self._get_curr_scope()):
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(f"Re-declaration of variable '{alias_reg_name}'")

        self._label_scope_level[self._curr_scope].add(alias_reg_name)

        if isinstance(value, Identifier):
            aliased_reg_name = value.name
        elif isinstance(value, IndexExpression):
            aliased_reg_name = value.collection.name
        else:
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(
                f"Unsupported aliasing {statement} not supported at the moment"
            )

        if aliased_reg_name not in self._global_qreg_size_map:
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(f"Qubit register {aliased_reg_name} not found for aliasing")

        aliased_reg_size = self._global_qreg_size_map[aliased_reg_name]
        if isinstance(value, Identifier):  # "let alias = q;"
            for i in range(aliased_reg_size):
                self._qubit_labels[f"{alias_reg_name}_{i}"] = self._qubit_labels[
                    f"{aliased_reg_name}_{i}"
                ]
            alias_reg_size = aliased_reg_size
        elif isinstance(value, IndexExpression):
            if isinstance(value.index, DiscreteSet):  # "let alias = q[{0,1}];"
                qids = Qasm3VisitorUtils.extract_values_from_discrete_set(value.index)
                for i, qid in enumerate(qids):
                    Qasm3VisitorUtils.validate_register_index(
                        qid, self._global_qreg_size_map[aliased_reg_name], qubit=True
                    )
                    self._qubit_labels[f"{alias_reg_name}_{i}"] = self._qubit_labels[
                        f"{aliased_reg_name}_{qid}"
                    ]
                alias_reg_size = len(qids)
            elif len(value.index) != 1:  # like "let alias = q[0,1];"?
                Qasm3VisitorUtils.print_err_location(statement.span)
                raise Qasm3ConversionError(
                    "An index set can be specified by a single integer (signed or unsigned), "
                    "a comma-separated list of integers contained in braces {a,b,c,…}, "
                    "or a range"
                )
            elif isinstance(value.index[0], IntegerLiteral):  # "let alias = q[0];"
                qid = value.index[0].value
                Qasm3VisitorUtils.validate_register_index(
                    qid, self._global_qreg_size_map[aliased_reg_name], qubit=True
                )
                self._qubit_labels[f"{alias_reg_name}_0"] = value.index[0].value
                alias_reg_size = 1
            elif isinstance(value.index[0], RangeDefinition):  # "let alias = q[0:1:2];"
                qids = self._get_qubits_from_range_definition(
                    value.index[0],
                    aliased_reg_size,
                    is_qubit_reg=True,
                )
                for i, qid in enumerate(qids):
                    self._qubit_labels[f"{alias_reg_name}_{i}"] = qid
                alias_reg_size = len(qids)

        self._global_qreg_size_map[alias_reg_name] = alias_reg_size

        _log.debug("Added labels for aliasing '%s'", target)

    def _visit_switch_statement(self, statement: SwitchStatement) -> None:
        """Visit a switch statement element.

        Args:
            statement (SwitchStatement): The switch statement to visit.

        Returns:
            None
        """
        # 1. analyse the target - it should ONLY be int, not casted
        switch_target = statement.target

        # either identifier or indexed expression
        if isinstance(switch_target, Identifier):
            switch_target_name = switch_target.name
        else:
            switch_target_name, _ = Qasm3VisitorUtils.analyse_index_expression(switch_target)

        if not Qasm3VisitorUtils.validate_variable_type(
            self._get_from_visible_scope(switch_target_name), Qasm3IntType
        ):
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(f"Switch target {switch_target_name} must be of type int")

        switch_target_val = Qasm3ExprEvaluator.evaluate_expression(self, switch_target)

        if len(statement.cases) == 0:
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError("Switch statement must have at least one case")

        # 2. handle the cases of the switch stmt
        #    each element in the list of the values
        #    should be of const int type and no duplicates should be present

        def _evaluate_case(statements):
            # can not put 'context' outside
            # BECAUSE the case expression CAN CONTAIN VARS from global scope
            self._push_context(Context.BLOCK)
            self._push_scope({})

            for stmt in statements:
                Qasm3VisitorUtils.validate_statement_type(SWITCH_BLACKLIST_STMTS, stmt, "switch")
                self.visit_statement(stmt)

            self._pop_scope()
            self._restore_context()

        case_fulfilled = False
        for case in statement.cases:
            case_list = case[0]
            seen_values = set()
            for case_expr in case_list:
                # 3. evaluate and verify that it is a const_expression
                # using vars only within the scope AND each component is either a
                # literal OR type int
                case_val = Qasm3ExprEvaluator.evaluate_expression(
                    self, case_expr, const_expr=True, reqd_type=Qasm3IntType
                )

                if case_val in seen_values:
                    Qasm3VisitorUtils.print_err_location(case_expr.span)
                    raise Qasm3ConversionError(
                        f"Duplicate case value {case_val} in switch statement"
                    )

                seen_values.add(case_val)

                if case_val == switch_target_val:
                    case_fulfilled = True

            if case_fulfilled:
                case_stmts = case[1].statements
                _evaluate_case(case_stmts)
                break

        if not case_fulfilled and statement.default:
            default_stmts = statement.default.statements
            _evaluate_case(default_stmts)

    # pylint: disable-next=too-many-branches
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
            self._visit_classical_declaration(statement)
        elif isinstance(statement, ClassicalAssignment):
            self._visit_classical_assignment(statement)
        elif isinstance(statement, ConstantDeclaration):
            self._visit_constant_declaration(statement)
        elif isinstance(statement, BranchingStatement):
            self._visit_branching_statement(statement)
        elif isinstance(statement, ForInLoop):
            self._visit_forin_loop(statement)
        elif isinstance(statement, AliasStatement):
            self._visit_alias_statement(statement)
        elif isinstance(statement, SwitchStatement):
            self._visit_switch_statement(statement)
        elif isinstance(statement, SubroutineDefinition):
            self._visit_subroutine_definition(statement)
        elif isinstance(statement, ExpressionStatement):
            self._visit_function_call(statement.expression)
        elif isinstance(statement, IODeclaration):
            raise NotImplementedError("OpenQASM 3 IO declarations not yet supported")
        else:
            # TODO : extend this
            Qasm3VisitorUtils.print_err_location(statement.span)
            raise Qasm3ConversionError(f"Unsupported statement of type {type(statement)}")

    def ir(self) -> str:
        return str(self._module)

    def bitcode(self) -> bytes:
        return self._module.bitcode()
