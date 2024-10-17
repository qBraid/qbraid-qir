# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=too-many-instance-attributes,too-many-lines,too-many-branches

"""
Module defining Qasm3 Visitor.

"""
import copy
import logging
from abc import ABCMeta, abstractmethod
from collections import deque
from typing import Any, Optional, Union

import numpy as np
import openqasm3.ast as qasm3_ast
import pyqir
import pyqir._native
import pyqir.rt

from .analyzer import Qasm3Analyzer
from .elements import Context, InversionOp, Qasm3Module, Variable
from .exceptions import Qasm3ConversionError, raise_qasm3_error
from .expressions import Qasm3ExprEvaluator
from .maps import (
    ARRAY_TYPE_MAP,
    CONSTANTS_MAP,
    MAX_ARRAY_DIMENSIONS,
    SWITCH_BLACKLIST_STMTS,
    map_qasm_inv_op_to_pyqir_callable,
    map_qasm_op_to_pyqir_callable,
)
from .subroutines import Qasm3SubroutineProcessor
from .transformer import Qasm3Transformer
from .validator import Qasm3Validator

logger = logging.getLogger(__name__)


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

    def __init__(
        self, initialize_runtime: bool = True, record_output: bool = True, check_only: bool = False
    ):
        self._module: pyqir.Module
        self._builder: pyqir.Builder
        self._entry_point: str = ""
        self._scope: deque = deque([{}])
        self._context: deque = deque([Context.GLOBAL])
        self._qubit_labels: dict[str, int] = {}
        self._clbit_labels: dict[str, int] = {}
        self._global_qreg_size_map: dict[str, int] = {}
        self._function_qreg_size_map: deque = deque([])  # for nested functions
        self._function_qreg_transform_map: deque = deque([])  # for nested functions
        self._global_creg_size_map: dict[str, int] = {}
        self._custom_gates: dict[str, qasm3_ast.QuantumGateDefinition] = {}
        self._subroutine_defns: dict[str, qasm3_ast.SubroutineDefinition] = {}
        self._initialize_runtime: bool = initialize_runtime
        self._record_output: bool = record_output
        self._check_only: bool = check_only
        self._curr_scope: int = 0
        self._label_scope_level: dict[int, set] = {self._curr_scope: set()}

        self._init_utilities()

    def visit_qasm3_module(self, module: Qasm3Module) -> None:
        """
        Visit a Qasm3 module.

        Args:
            module (Qasm3Module): The module to visit.

        Returns:
            None
        """
        logger.debug("Visiting Qasm3 module '%s' (%d)", module.name, module.num_qubits)
        self._module = module.module
        context = self._module.context
        entry = pyqir.entry_point(self._module, module.name, module.num_qubits, module.num_clbits)

        self._entry_point = entry.name
        self._builder = pyqir.Builder(context)
        self._builder.insert_at_end(pyqir.BasicBlock(context, "entry", entry))

        if self._initialize_runtime is True:
            i8p = pyqir.PointerType(pyqir.IntType(context, 8))
            nullptr = pyqir.Constant.null(i8p)
            pyqir.rt.initialize(self._builder, nullptr)

    def _init_utilities(self):
        """Initialize the utilities for the visitor."""
        for class_obj in [Qasm3Transformer, Qasm3ExprEvaluator, Qasm3SubroutineProcessor]:
            class_obj.set_visitor_obj(self)

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

    def _check_in_scope(self, var_name: str) -> bool:
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
          variable in the parent scope is shadowed. We need to remember the
          original value of the shadowed variable when we exit the block scope

        """
        global_scope = self._get_global_scope()
        curr_scope = self._get_curr_scope()
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
        if self._record_output is False or self._check_only:
            return

        i8p = pyqir.PointerType(pyqir.IntType(self._module.context, 8))

        for i in range(module.num_qubits):
            result_ref = pyqir.result(self._module.context, i)
            pyqir.rt.result_record_output(self._builder, result_ref, pyqir.Constant.null(i8p))

    def visit_register(
        self, register: Union[qasm3_ast.QubitDeclaration, qasm3_ast.ClassicalDeclaration]
    ) -> None:
        """Visit a register element.

        Args:
            register (QubitDeclaration|ClassicalDeclaration): The register name and size.

        Returns:
            None
        """
        logger.debug("Visiting register '%s'", str(register))
        is_qubit = isinstance(register, qasm3_ast.QubitDeclaration)

        current_size = len(self._qubit_labels) if is_qubit else len(self._clbit_labels)
        if is_qubit:
            register_size = (
                1 if register.size is None else register.size.value  # type: ignore[union-attr]
            )
        else:
            register_size = (
                1
                if register.type.size is None  # type: ignore[union-attr]
                else register.type.size.value  # type: ignore[union-attr]
            )
        register_name = (
            register.qubit.name  # type: ignore[union-attr]
            if is_qubit
            else register.identifier.name  # type: ignore[union-attr]
        )

        size_map = self._global_qreg_size_map if is_qubit else self._global_creg_size_map
        label_map = self._qubit_labels if is_qubit else self._clbit_labels

        if self._check_in_scope(register_name):
            raise_qasm3_error(
                f"Invalid declaration of register with name '{register_name}'", span=register.span
            )

        if is_qubit:  # as bit type vars are added in classical decl handler
            self._add_var_in_scope(
                Variable(
                    register_name,
                    qasm3_ast.QubitDeclaration,
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

        logger.debug("Added labels for register '%s'", str(register))

    def _check_if_name_in_scope(self, name: str, operation: Any) -> None:
        """Check if a name is in scope to avoid duplicate declarations.
        Args:
            name (str): The name to check.
            operation (Any): The operation to check the name in scope for.

        Returns:
            bool: Whether the name is in scope.
        """
        for scope_level in range(0, self._curr_scope + 1):
            if name in self._label_scope_level[scope_level]:
                return
        raise_qasm3_error(
            f"Variable {name} not in scope for operation {operation}", span=operation.span
        )

    def _get_op_bits(
        self, operation: Any, reg_size_map: dict, qubits: bool = True, qir_form: bool = True
    ) -> Union[list[pyqir.Constant], list[qasm3_ast.IndexedIdentifier]]:
        """Get the quantum / classical bits for the operation.

        Args:
            operation (Any): The operation to get qubits for.
            reg_size_map (dict): The size map of the registers in scope.
            qubits (bool): Whether the bits are quantum bits or classical bits. Defaults to True.
            qir_form (bool): Whether to return bits in QIR form or not. Defaults to True.

        Returns:
            Union[list[pyqir.Constant], list[qasm3_ast.IndexedIdentifier]] : The bits for the
                                                                             operation.
        """
        qir_bits = []
        openqasm_bits = []
        visited_bits = set()
        bit_list = []
        if isinstance(operation, qasm3_ast.QuantumMeasurementStatement):
            assert operation.target is not None
            bit_list = [operation.measure.qubit] if qubits else [operation.target]
        else:
            bit_list = (
                operation.qubits if isinstance(operation.qubits, list) else [operation.qubits]
            )

        for bit in bit_list:
            if isinstance(bit, qasm3_ast.IndexedIdentifier):
                reg_name = bit.name.name
            else:
                reg_name = bit.name

            if reg_name not in reg_size_map:
                raise_qasm3_error(
                    f"Missing register declaration for {reg_name} in operation {operation}",
                    span=operation.span,
                )
            self._check_if_name_in_scope(reg_name, operation)

            if isinstance(bit, qasm3_ast.IndexedIdentifier):
                if isinstance(bit.indices[0], qasm3_ast.DiscreteSet):
                    bit_ids = Qasm3Transformer.extract_values_from_discrete_set(bit.indices[0])
                elif isinstance(bit.indices[0][0], qasm3_ast.RangeDefinition):
                    bit_ids = Qasm3Transformer.get_qubits_from_range_definition(
                        bit.indices[0][0], reg_size_map[reg_name], is_qubit_reg=qubits
                    )
                else:
                    bit_id = Qasm3ExprEvaluator.evaluate_expression(bit.indices[0][0])
                    Qasm3Validator.validate_register_index(
                        bit_id, reg_size_map[reg_name], qubit=qubits
                    )
                    bit_ids = [bit_id]
                openqasm_bits.extend(
                    [
                        qasm3_ast.IndexedIdentifier(
                            qasm3_ast.Identifier(reg_name), [[qasm3_ast.IntegerLiteral(bit_id)]]
                        )
                        for bit_id in bit_ids
                    ]
                )

            else:
                bit_ids = list(range(reg_size_map[reg_name]))
                openqasm_bits.extend(
                    [
                        qasm3_ast.IndexedIdentifier(
                            qasm3_ast.Identifier(reg_name), [[qasm3_ast.IntegerLiteral(bit_id)]]
                        )
                        for bit_id in bit_ids
                    ]
                )

            if qir_form:
                label_map = self._qubit_labels if qubits else self._clbit_labels
                reg_ids = [label_map[f"{reg_name}_{bit_id}"] for bit_id in bit_ids]
                for bit_id in reg_ids:
                    if bit_id in visited_bits:
                        raise_qasm3_error(
                            f"Duplicate {'qubit' if qubits else 'clbit'} "
                            f"{reg_name}[{bit_id}] argument",
                            span=operation.span,
                        )
                    visited_bits.add(bit_id)
                qir_bits.extend(
                    [
                        (
                            pyqir.qubit(self._module.context, bit_id)
                            if qubits
                            else pyqir.result(self._module.context, bit_id)
                        )
                        for bit_id in reg_ids
                    ]
                )

        return qir_bits if qir_form else openqasm_bits

    def _visit_measurement(self, statement: qasm3_ast.QuantumMeasurementStatement) -> None:
        """Visit a measurement statement element.

        Args:
            statement (qasm3_ast.QuantumMeasurementStatement): The measurement statement to visit.

        Returns:
            None
        """
        logger.debug("Visiting measurement statement '%s'", str(statement))

        source = statement.measure.qubit
        target = statement.target
        assert source and target

        # # TODO: handle in-function measurements
        source_name: str = (
            source.name if isinstance(source, qasm3_ast.Identifier) else source.name.name
        )
        if source_name not in self._global_qreg_size_map:
            raise_qasm3_error(
                f"Missing register declaration for {source_name} in measurement "
                f"operation {statement}",
                span=statement.span,
            )

        target_name: str = (
            target.name if isinstance(target, qasm3_ast.Identifier) else target.name.name
        )
        if target_name not in self._global_creg_size_map:
            raise_qasm3_error(
                f"Missing register declaration for {target_name} in measurement "
                f"operation {statement}",
                span=statement.span,
            )

        source_ids = self._get_op_bits(
            statement, reg_size_map=self._global_qreg_size_map, qubits=True
        )
        target_ids = self._get_op_bits(
            statement, reg_size_map=self._global_creg_size_map, qubits=False
        )

        if len(source_ids) != len(target_ids):
            raise_qasm3_error(
                f"Register sizes of {source_name} and {target_name} do not match "
                "for measurement operation",
                span=statement.span,
            )
        if not self._check_only:
            for src_id, tgt_id in zip(source_ids, target_ids):
                pyqir._native.mz(self._builder, src_id, tgt_id)  # type: ignore[arg-type]

    def _visit_reset(self, statement: qasm3_ast.QuantumReset) -> None:
        """Visit a reset statement element.

        Args:
            statement (qasm3_ast.QuantumReset): The reset statement to visit.

        Returns:
            None
        """
        logger.debug("Visiting reset statement '%s'", str(statement))
        if len(self._function_qreg_size_map) > 0:  # atleast in SOME function scope
            # transform qubits to use the global qreg identifiers
            statement.qubits = (
                Qasm3Transformer.transform_function_qubits(  # type: ignore[assignment]
                    statement,
                    self._function_qreg_size_map[-1],
                    self._function_qreg_transform_map[-1],
                )
            )
        qubit_ids = self._get_op_bits(statement, self._global_qreg_size_map, True)

        if not self._check_only:
            for qid in qubit_ids:
                # qid is of type Constant which is inherited from Value, so we ignore the type error
                pyqir._native.reset(self._builder, qid)  # type: ignore[arg-type]

    def _visit_barrier(self, barrier: qasm3_ast.QuantumBarrier) -> None:
        """Visit a barrier statement element.

        Args:
            statement (qasm3_ast.QuantumBarrier): The barrier statement to visit.

        Returns:
            None
        """
        # if barrier is applied to ALL qubits at once, we are fine
        if len(self._function_qreg_size_map) > 0:  # atleast in SOME function scope
            # transform qubits to use the global qreg identifiers

            # since we are changing the qubits to IndexedIdentifiers, we need to supress the
            # error for the type checker
            barrier.qubits = (
                Qasm3Transformer.transform_function_qubits(  # type: ignore [assignment]
                    barrier,
                    self._function_qreg_size_map[-1],
                    self._function_qreg_transform_map[-1],
                )
            )
        barrier_qubits = self._get_op_bits(barrier, self._global_qreg_size_map)
        total_qubit_count = sum(self._global_qreg_size_map.values())
        if len(barrier_qubits) == total_qubit_count:
            if not self._check_only:
                pyqir._native.barrier(self._builder)
        else:
            raise_qasm3_error(
                "Barrier operation on a qubit subset is not supported in pyqir",
                err_type=NotImplementedError,
                span=barrier.span,
            )

    def _get_op_parameters(self, operation: qasm3_ast.QuantumGate) -> list[float]:
        """Get the parameters for the operation.

        Args:
            operation (qasm3_ast.QuantumGate): The operation to get parameters for.

        Returns:
            list[float]: The parameters for the operation.
        """
        param_list = []
        for param in operation.arguments:
            param_value = Qasm3ExprEvaluator.evaluate_expression(param)
            param_list.append(param_value)

        return param_list

    def _visit_gate_definition(self, definition: qasm3_ast.QuantumGateDefinition) -> None:
        """Visit a gate definition element.

        Args:
            definition (qasm3_ast.QuantumGateDefinition): The gate definition to visit.

        Returns:
            None
        """
        gate_name = definition.name.name
        if gate_name in self._custom_gates:
            raise_qasm3_error(f"Duplicate gate definition for {gate_name}", span=definition.span)
        self._custom_gates[gate_name] = definition

    def _visit_basic_gate_operation(
        self, operation: qasm3_ast.QuantumGate, inverse: bool = False
    ) -> None:
        """Visit a gate operation element.

        Args:
            operation (qasm3_ast.QuantumGate): The gate operation to visit.
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

        logger.debug("Visiting basic gate operation '%s'", str(operation))
        op_name: str = operation.name.name
        op_qubits = self._get_op_bits(operation, self._global_qreg_size_map)
        inverse_action = None
        if not inverse:
            qir_func, op_qubit_count = map_qasm_op_to_pyqir_callable(op_name)
        else:
            # in basic gates, inverse action only affects the rotation gates
            qir_func, op_qubit_count, inverse_action = map_qasm_inv_op_to_pyqir_callable(op_name)

        op_parameters = None

        if len(op_qubits) % op_qubit_count != 0:
            raise_qasm3_error(
                f"Invalid number of qubits {len(op_qubits)} for operation {operation.name.name}",
                span=operation.span,
            )

        if len(operation.arguments) > 0:  # parametric gate
            op_parameters = self._get_op_parameters(operation)
            if inverse_action == InversionOp.INVERT_ROTATION:
                op_parameters = [-1 * param for param in op_parameters]

        if not self._check_only:
            for i in range(0, len(op_qubits), op_qubit_count):
                # we apply the gate on the qubit subset linearly
                qubit_subset = op_qubits[i : i + op_qubit_count]
                if op_parameters is not None:
                    qir_func(self._builder, *op_parameters, *qubit_subset)
                else:
                    qir_func(self._builder, *qubit_subset)

    def _visit_custom_gate_operation(
        self, operation: qasm3_ast.QuantumGate, inverse: bool = False
    ) -> None:
        """Visit a custom gate operation element recursively.

        Args:
            operation (qasm3_ast.QuantumGate): The gate operation to visit.
            inverse (bool): Whether the operation is an inverse operation. Defaults to False.

                            If True, the gate operation is applied in reverse order and the
                            inverse modifier is appended to each gate call.
                            See https://openqasm.com/language/gates.html#inverse-modifier
                            for more clarity.

        Returns:
            None
        """
        logger.debug("Visiting custom gate operation '%s'", str(operation))
        gate_name: str = operation.name.name
        gate_definition: qasm3_ast.QuantumGateDefinition = self._custom_gates[gate_name]
        op_qubits: list[qasm3_ast.IndexedIdentifier] = (
            self._get_op_bits(  # type: ignore [assignment]
                operation, self._global_qreg_size_map, qir_form=False
            )
        )

        Qasm3Validator.validate_gate_call(operation, gate_definition, len(op_qubits))
        # we need this because the gates applied inside a gate definition use the
        # VARIABLE names and not the qubits

        # so we need to update the arguments of these gate applications with the actual
        # qubit identifiers and then RECURSIVELY call the visit_generic_gate_operation
        qubit_map = {
            formal_arg.name: actual_arg
            for formal_arg, actual_arg in zip(gate_definition.qubits, op_qubits)
        }
        param_map = {
            formal_arg.name: Qasm3ExprEvaluator.evaluate_expression(actual_arg)
            for formal_arg, actual_arg in zip(gate_definition.arguments, operation.arguments)
        }

        gate_definition_ops = copy.deepcopy(gate_definition.body)
        if inverse:
            gate_definition_ops.reverse()

        self._push_context(Context.GATE)

        for gate_op in gate_definition_ops:
            if isinstance(gate_op, qasm3_ast.QuantumGate):
                # necessary to avoid modifying the original gate definition
                # in case the gate is reapplied
                gate_op_copy = copy.deepcopy(gate_op)
                if gate_op.name.name == gate_name:
                    raise_qasm3_error(
                        f"Recursive definitions not allowed for gate {gate_name}", span=gate_op.span
                    )
                Qasm3Transformer.transform_gate_params(gate_op_copy, param_map)
                Qasm3Transformer.transform_gate_qubits(gate_op_copy, qubit_map)
                # need to trickle the inverse down to the child gates
                if inverse:
                    # span doesn't matter as we don't analyze it
                    gate_op_copy.modifiers.append(
                        qasm3_ast.QuantumGateModifier(qasm3_ast.GateModifierName.inv, None)
                    )
                self._visit_generic_gate_operation(gate_op_copy)
            else:
                # TODO: add control flow support
                raise_qasm3_error(
                    f"Unsupported gate definition statement {gate_op}", span=gate_op.span
                )

        self._restore_context()

    def _collapse_gate_modifiers(self, operation: qasm3_ast.QuantumGate) -> tuple:
        """Collapse the gate modifiers of a gate operation.
           Some analysis is required to get this result.
           The basic idea is that any power operation is multiplied and inversions are toggled.
           The placement of the inverse operation does not matter.

        Args:
            operation (qasm3_ast.QuantumGate): The gate operation to collapse modifiers for.

        Returns:
            tuple[Any, Any]: The power and inverse values of the gate operation.
        """
        power_value, inverse_value = 1, False

        for modifier in operation.modifiers:
            modifier_name = modifier.modifier
            if modifier_name == qasm3_ast.GateModifierName.pow and modifier.argument is not None:
                current_power = Qasm3ExprEvaluator.evaluate_expression(modifier.argument)
                if current_power < 0:
                    inverse_value = not inverse_value
                power_value = power_value * abs(current_power)
            elif modifier_name == qasm3_ast.GateModifierName.inv:
                inverse_value = not inverse_value
            elif modifier_name in [
                qasm3_ast.GateModifierName.ctrl,
                qasm3_ast.GateModifierName.negctrl,
            ]:
                raise_qasm3_error(
                    f"Controlled modifier gates not yet supported in gate operation {operation}",
                    err_type=NotImplementedError,
                    span=operation.span,
                )
        return (power_value, inverse_value)

    def _visit_generic_gate_operation(self, operation: qasm3_ast.QuantumGate) -> None:
        """Visit a gate operation element.

        Args:
            operation (qasm3_ast.QuantumGate): The gate operation to visit.

        Returns:
            None
        """
        power_value, inverse_value = self._collapse_gate_modifiers(operation)
        operation = copy.deepcopy(operation)

        # only needs to be done once for a gate operation
        if not self._in_gate_scope() and len(self._function_qreg_size_map) > 0:
            # we are in SOME function scope
            # transform qubits to use the global qreg identifiers
            operation.qubits = (
                Qasm3Transformer.transform_function_qubits(  # type: ignore [assignment]
                    operation,
                    self._function_qreg_size_map[-1],
                    self._function_qreg_transform_map[-1],
                )
            )
        # Applying the inverse first and then the power is same as
        # apply the power first and then inverting the result
        for _ in range(power_value):
            if operation.name.name in self._custom_gates:
                self._visit_custom_gate_operation(operation, inverse_value)
            else:
                self._visit_basic_gate_operation(operation, inverse_value)

    def _visit_constant_declaration(self, statement: qasm3_ast.ConstantDeclaration) -> None:
        """
        Visit a constant declaration element. Const can only be declared for scalar
        type variables and not arrays. Assignment is mandatory in constant declaration.

        Args:
            statement (qasm3_ast.ConstantDeclaration): The constant declaration to visit.

        Returns:
            None
        """

        var_name = statement.identifier.name

        if var_name in CONSTANTS_MAP:
            raise_qasm3_error(
                f"Can not declare variable with keyword name {var_name}", span=statement.span
            )
        if self._check_in_scope(var_name):
            raise_qasm3_error(f"Re-declaration of variable {var_name}", span=statement.span)
        init_value = Qasm3ExprEvaluator.evaluate_expression(
            statement.init_expression, const_expr=True
        )

        base_type = statement.type
        if isinstance(base_type, qasm3_ast.BoolType):
            base_size = 1
        elif hasattr(base_type, "size"):
            if base_type.size is None:
                base_size = 32  # default for now
            else:
                base_size = Qasm3ExprEvaluator.evaluate_expression(base_type.size, const_expr=True)
                if not isinstance(base_size, int) or base_size <= 0:
                    raise_qasm3_error(
                        f"Invalid base size {base_size} for variable {var_name}",
                        span=statement.span,
                    )

        variable = Variable(var_name, base_type, base_size, [], init_value, is_constant=True)

        # cast + validation
        variable.value = Qasm3Validator.validate_variable_assignment_value(variable, init_value)

        self._add_var_in_scope(variable)

    # pylint: disable=too-many-branches
    def _visit_classical_declaration(self, statement: qasm3_ast.ClassicalDeclaration) -> None:
        """Visit a classical operation element.

        Args:
            statement (ClassicalType): The classical operation to visit.

        Returns:
            None
        """
        var_name = statement.identifier.name
        if var_name in CONSTANTS_MAP:
            raise_qasm3_error(
                f"Can not declare variable with keyword name {var_name}", span=statement.span
            )
        if self._check_in_scope(var_name):
            if self._in_block_scope() and var_name not in self._get_curr_scope():
                # we can re-declare variables once in block scope even if they are
                # present in the parent scope
                # Eg.
                # int a = 10;
                # { int a = 20; // valid
                # }
                pass
            else:
                raise_qasm3_error(f"Re-declaration of variable {var_name}", span=statement.span)

        init_value = None
        base_type = statement.type
        final_dimensions = []

        if isinstance(base_type, qasm3_ast.ArrayType):
            dimensions = base_type.dimensions

            if len(dimensions) > MAX_ARRAY_DIMENSIONS:
                raise_qasm3_error(
                    f"Invalid dimensions {len(dimensions)} for array declaration for {var_name}. "
                    f"Max allowed dimensions is {MAX_ARRAY_DIMENSIONS}",
                    span=statement.span,
                )

            base_type = base_type.base_type
            num_elements = 1
            for dim in dimensions:
                dim_value = Qasm3ExprEvaluator.evaluate_expression(dim)
                if not isinstance(dim_value, int) or dim_value <= 0:
                    raise_qasm3_error(
                        f"Invalid dimension size {dim_value} in array declaration for {var_name}",
                        span=statement.span,
                    )
                final_dimensions.append(dim_value)
                num_elements *= dim_value

            init_value = np.full(final_dimensions, None)

        if statement.init_expression:
            if isinstance(statement.init_expression, qasm3_ast.ArrayLiteral):
                init_value = self._evaluate_array_initialization(
                    statement.init_expression, final_dimensions, base_type
                )
            else:
                init_value = Qasm3ExprEvaluator.evaluate_expression(statement.init_expression)
        base_size = 1
        if not isinstance(base_type, qasm3_ast.BoolType):
            base_size = (
                32
                if not hasattr(base_type, "size") or base_type.size is None
                else Qasm3ExprEvaluator.evaluate_expression(base_type.size)
            )

        if not isinstance(base_size, int) or base_size <= 0:
            raise_qasm3_error(
                f"Invalid base size {base_size} for variable {var_name}", span=statement.span
            )

        if isinstance(base_type, qasm3_ast.FloatType) and base_size not in [32, 64]:
            raise_qasm3_error(
                f"Invalid base size {base_size} for float variable {var_name}", span=statement.span
            )

        variable = Variable(var_name, base_type, base_size, final_dimensions, init_value)

        if statement.init_expression:
            if isinstance(init_value, np.ndarray):
                assert variable.dims is not None
                Qasm3Validator.validate_array_assignment_values(variable, variable.dims, init_value)
            else:
                variable.value = Qasm3Validator.validate_variable_assignment_value(
                    variable, init_value
                )

        self._add_var_in_scope(variable)

    def _visit_classical_assignment(self, statement: qasm3_ast.ClassicalAssignment) -> None:
        """Visit a classical assignment element.

        Args:
            statement (qasm3_ast.ClassicalAssignment): The classical assignment to visit.

        Returns:
            None
        """
        lvalue = statement.lvalue
        lvar_name = lvalue.name
        if isinstance(lvar_name, qasm3_ast.Identifier):
            lvar_name = lvar_name.name

        lvar = self._get_from_visible_scope(lvar_name)
        if lvar is None:  # we check for none here, so type errors are irrelevant afterwards
            raise_qasm3_error(f"Undefined variable {lvar_name} in assignment", span=statement.span)
        if lvar.is_constant:  # type: ignore[union-attr]
            raise_qasm3_error(
                f"Assignment to constant variable {lvar_name} not allowed", span=statement.span
            )

        # rvalue will be an evaluated value (scalar, list)
        # if rvalue is a list, we want a copy of it
        rvalue = statement.rvalue
        rvalue_raw = Qasm3ExprEvaluator.evaluate_expression(
            rvalue
        )  # consists of scope check and index validation

        # cast + validation
        # rhs is a scalar
        rvalue_eval = None
        if not isinstance(rvalue_raw, np.ndarray):
            rvalue_eval = Qasm3Validator.validate_variable_assignment_value(
                lvar, rvalue_raw  # type: ignore[arg-type]
            )
        else:  # rhs is a list
            rvalue_dimensions = list(rvalue_raw.shape)

            # validate that the values inside rvar are valid for lvar
            Qasm3Validator.validate_array_assignment_values(
                variable=lvar,  # type: ignore[arg-type]
                dimensions=rvalue_dimensions,
                values=rvalue_raw,  # type: ignore[arg-type]
            )
            rvalue_eval = rvalue_raw

        if lvar.readonly:  # type: ignore[union-attr]
            raise_qasm3_error(
                f"Assignment to readonly variable '{lvar_name}' not allowed" " in function call",
                span=statement.span,
            )

        # lvalue will be the variable which will HOLD this value
        if isinstance(lvalue, qasm3_ast.IndexedIdentifier):
            # stupid indices structure in openqasm :/
            if len(lvalue.indices[0]) > 1:  # type: ignore[arg-type]
                l_indices = lvalue.indices[0]
            else:
                l_indices = [idx[0] for idx in lvalue.indices]  # type: ignore[assignment, index]

            validated_l_indices = Qasm3Analyzer.analyze_classical_indices(
                l_indices, lvar, Qasm3ExprEvaluator  # type: ignore[arg-type]
            )
            Qasm3Transformer.update_array_element(
                multi_dim_arr=lvar.value,  # type: ignore[union-attr, arg-type]
                indices=validated_l_indices,
                value=rvalue_eval,
            )
        else:
            lvar.value = rvalue_eval  # type: ignore[union-attr]
        self._update_var_in_scope(lvar)  # type: ignore[arg-type]

    def _evaluate_array_initialization(
        self, array_literal: qasm3_ast.ArrayLiteral, dimensions: list[int], base_type: Any
    ) -> np.ndarray:
        """Evaluate an array initialization.

        Args:
            array_literal (qasm3_ast.ArrayLiteral): The array literal to evaluate.
            dimensions (list[int]): The dimensions of the array.
            base_type (Any): The base type of the array.

        Returns:
            np.ndarray: The evaluated array initialization.
        """
        init_values = []
        for value in array_literal.values:
            if isinstance(value, qasm3_ast.ArrayLiteral):
                nested_array = self._evaluate_array_initialization(value, dimensions[1:], base_type)
                init_values.append(nested_array)
            else:
                eval_value = Qasm3ExprEvaluator.evaluate_expression(value)
                init_values.append(eval_value)

        return np.array(init_values, dtype=ARRAY_TYPE_MAP[base_type.__class__])

    def _visit_branching_statement(self, statement: qasm3_ast.BranchingStatement) -> None:
        """Visit a branching statement element.

        Args:
            statement (qasm3_ast.BranchingStatement): The branching statement to visit.

        Returns:
            None
        """
        self._push_context(Context.BLOCK)
        self._push_scope({})
        self._curr_scope += 1
        self._label_scope_level[self._curr_scope] = set()

        condition = statement.condition
        positive_branching = Qasm3Analyzer.analyse_branch_condition(condition)

        if_block = statement.if_block
        if not statement.if_block:
            raise_qasm3_error("Missing if block", span=statement.span)
        else_block = statement.else_block
        if not positive_branching:
            if_block, else_block = else_block, if_block

        reg_id, reg_name = Qasm3Transformer.get_branch_params(condition)

        if reg_name not in self._global_creg_size_map:
            raise_qasm3_error(
                f"Missing register declaration for {reg_name} in {condition}",
                span=statement.span,
            )
        Qasm3Validator.validate_register_index(
            reg_id, self._global_creg_size_map[reg_name], qubit=False
        )

        def _visit_statement_block(block):
            for stmt in block:
                self.visit_statement(stmt)

        if not self._check_only:
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

    def _visit_forin_loop(self, statement: qasm3_ast.ForInLoop) -> None:
        # Compute loop variable values
        if isinstance(statement.set_declaration, qasm3_ast.RangeDefinition):
            init_exp = statement.set_declaration.start
            startval = Qasm3ExprEvaluator.evaluate_expression(init_exp)
            range_def = statement.set_declaration
            stepval = (
                1
                if range_def.step is None
                else Qasm3ExprEvaluator.evaluate_expression(range_def.step)
            )
            endval = Qasm3ExprEvaluator.evaluate_expression(range_def.end)
            irange = list(range(startval, endval + stepval, stepval))
        elif isinstance(statement.set_declaration, qasm3_ast.DiscreteSet):
            init_exp = statement.set_declaration.values[0]
            irange = [
                Qasm3ExprEvaluator.evaluate_expression(exp)
                for exp in statement.set_declaration.values
            ]
        else:
            raise Qasm3ConversionError(
                f"Unexpected type {type(statement.set_declaration)} of set_declaration in loop."
            )

        i: Optional[Variable]  # will store iteration Variable to update to loop scope

        for ival in irange:
            self._push_context(Context.BLOCK)
            self._push_scope({})

            # Initialize loop variable in loop scope
            # need to re-declare as we discard the block scope in subsequent
            # iterations of the loop
            self._visit_classical_declaration(
                qasm3_ast.ClassicalDeclaration(statement.type, statement.identifier, init_exp)
            )
            i = self._get_from_visible_scope(statement.identifier.name)

            # Update scope with current value of loop Variable
            if i is not None:
                i.value = ival
                self._update_var_in_scope(i)

            for stmt in statement.block:
                self.visit_statement(stmt)

            # scope not persistent between loop iterations
            self._pop_scope()
            self._restore_context()

            # as we are only checking compile time errors
            # not runtime errors, we can break here
            if self._check_only:
                break

    def _visit_subroutine_definition(self, statement: qasm3_ast.SubroutineDefinition) -> None:
        """Visit a subroutine definition element.
           Reference: https://openqasm.com/language/subroutines.html#subroutines

        Args:
            statement (qasm3_ast.SubroutineDefinition): The subroutine definition to visit.

        Returns:
            None
        """
        fn_name = statement.name.name

        if fn_name in CONSTANTS_MAP:
            raise_qasm3_error(
                f"Subroutine name '{fn_name}' is a reserved keyword", span=statement.span
            )

        if fn_name in self._subroutine_defns:
            raise_qasm3_error(f"Redefinition of subroutine '{fn_name}'", span=statement.span)

        if self._check_in_scope(fn_name):
            raise_qasm3_error(
                f"Can not declare subroutine with name '{fn_name}' as "
                "it is already declared as a variable",
                span=statement.span,
            )

        self._subroutine_defns[fn_name] = statement

    # pylint: disable=too-many-locals, too-many-statements
    def _visit_function_call(self, statement: qasm3_ast.FunctionCall) -> Optional[Any]:
        """Visit a function call element.

        Args:
            statement (qasm3_ast.FunctionCall): The function call to visit.
        Returns:
            None

        """
        fn_name = statement.name.name
        if fn_name not in self._subroutine_defns:
            raise_qasm3_error(f"Undefined subroutine '{fn_name}' was called", span=statement.span)

        subroutine_def = self._subroutine_defns[fn_name]

        if len(statement.arguments) != len(subroutine_def.arguments):
            raise_qasm3_error(
                f"Parameter count mismatch for subroutine '{fn_name}'. Expected "
                f"{len(subroutine_def.arguments)} but got {len(statement.arguments)} in call",
                span=statement.span,
            )

        duplicate_qubit_detect_map: dict = {}
        qubit_transform_map: dict = {}  # {(formal arg, idx) : (actual arg, idx)}
        formal_qreg_size_map: dict = {}

        quantum_vars, classical_vars = [], []
        for actual_arg, formal_arg in zip(statement.arguments, subroutine_def.arguments):
            if isinstance(formal_arg, qasm3_ast.ClassicalArgument):
                classical_vars.append(
                    Qasm3SubroutineProcessor.process_classical_arg(
                        formal_arg, actual_arg, fn_name, statement.span
                    )
                )
            else:
                quantum_vars.append(
                    Qasm3SubroutineProcessor.process_quantum_arg(
                        formal_arg,
                        actual_arg,
                        formal_qreg_size_map,
                        duplicate_qubit_detect_map,
                        qubit_transform_map,
                        fn_name,
                        statement.span,
                    )
                )

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

        return_statement = None
        for function_op in subroutine_def.body:
            if isinstance(function_op, qasm3_ast.ReturnStatement):
                return_statement = copy.deepcopy(function_op)
                break
            self.visit_statement(copy.deepcopy(function_op))

        return_value = None
        if return_statement:
            return_value = Qasm3ExprEvaluator.evaluate_expression(return_statement.expression)
            return_value = Qasm3Validator.validate_return_statement(
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

    def _visit_while_loop(self, statement: qasm3_ast.WhileLoop) -> None:
        pass

    def _visit_alias_statement(self, statement: qasm3_ast.AliasStatement) -> None:
        """Visit an alias statement element.

        Args:
            statement (qasm3_ast.AliasStatement): The alias statement to visit.

        Returns:
            None
        """
        # pylint: disable=too-many-branches
        target = statement.target
        value = statement.value

        alias_reg_name: str = target.name
        alias_reg_size: int = 0
        aliased_reg_name: str = ""
        aliased_reg_size: int = 0

        # Alias should not be redeclared earlier as a variable or a constant
        if self._check_in_scope(alias_reg_name):
            raise_qasm3_error(f"Re-declaration of variable '{alias_reg_name}'", span=statement.span)
        self._label_scope_level[self._curr_scope].add(alias_reg_name)

        if isinstance(value, qasm3_ast.Identifier):
            aliased_reg_name = value.name
        elif isinstance(value, qasm3_ast.IndexExpression) and isinstance(
            value.collection, qasm3_ast.Identifier
        ):
            aliased_reg_name = value.collection.name
        else:
            raise_qasm3_error(f"Unsupported aliasing {statement}", span=statement.span)

        if aliased_reg_name not in self._global_qreg_size_map:
            raise_qasm3_error(
                f"Qubit register {aliased_reg_name} not found for aliasing", span=statement.span
            )
        aliased_reg_size = self._global_qreg_size_map[aliased_reg_name]
        if isinstance(value, qasm3_ast.Identifier):  # "let alias = q;"
            for i in range(aliased_reg_size):
                self._qubit_labels[f"{alias_reg_name}_{i}"] = self._qubit_labels[
                    f"{aliased_reg_name}_{i}"
                ]
            alias_reg_size = aliased_reg_size
        elif isinstance(value, qasm3_ast.IndexExpression):
            if isinstance(value.index, qasm3_ast.DiscreteSet):  # "let alias = q[{0,1}];"
                qids = Qasm3Transformer.extract_values_from_discrete_set(value.index)
                for i, qid in enumerate(qids):
                    Qasm3Validator.validate_register_index(
                        qid, self._global_qreg_size_map[aliased_reg_name], qubit=True
                    )
                    self._qubit_labels[f"{alias_reg_name}_{i}"] = self._qubit_labels[
                        f"{aliased_reg_name}_{qid}"
                    ]
                alias_reg_size = len(qids)
            elif len(value.index) != 1:  # like "let alias = q[0,1];"?
                raise_qasm3_error(
                    "An index set can be specified by a single integer (signed or unsigned), "
                    "a comma-separated list of integers contained in braces {a,b,c,…}, "
                    "or a range",
                    span=statement.span,
                )
            elif isinstance(value.index[0], qasm3_ast.IntegerLiteral):  # "let alias = q[0];"
                qid = value.index[0].value
                Qasm3Validator.validate_register_index(
                    qid, self._global_qreg_size_map[aliased_reg_name], qubit=True
                )
                self._qubit_labels[f"{alias_reg_name}_0"] = value.index[0].value
                alias_reg_size = 1
            elif isinstance(value.index[0], qasm3_ast.RangeDefinition):  # "let alias = q[0:1:2];"
                qids = Qasm3Transformer.get_qubits_from_range_definition(
                    value.index[0],
                    aliased_reg_size,
                    is_qubit_reg=True,
                )
                for i, qid in enumerate(qids):
                    self._qubit_labels[f"{alias_reg_name}_{i}"] = qid
                alias_reg_size = len(qids)

        self._global_qreg_size_map[alias_reg_name] = alias_reg_size

        logger.debug("Added labels for aliasing '%s'", target)

    def _visit_switch_statement(self, statement: qasm3_ast.SwitchStatement) -> None:
        """Visit a switch statement element.

        Args:
            statement (qasm3_ast.SwitchStatement): The switch statement to visit.

        Returns:
            None
        """
        # 1. analyze the target - it should ONLY be int, not casted
        switch_target = statement.target
        switch_target_name = ""
        # either identifier or indexed expression
        if isinstance(switch_target, qasm3_ast.Identifier):
            switch_target_name = switch_target.name
        elif isinstance(switch_target, qasm3_ast.IndexExpression):
            switch_target_name, _ = Qasm3Analyzer.analyze_index_expression(switch_target)

        if not Qasm3Validator.validate_variable_type(
            self._get_from_visible_scope(switch_target_name), qasm3_ast.IntType
        ):
            raise_qasm3_error(
                f"Switch target {switch_target_name} must be of type int", span=statement.span
            )

        switch_target_val = Qasm3ExprEvaluator.evaluate_expression(switch_target)

        if len(statement.cases) == 0:
            raise_qasm3_error("Switch statement must have at least one case", span=statement.span)

        # 2. handle the cases of the switch stmt
        #    each element in the list of the values
        #    should be of const int type and no duplicates should be present

        def _evaluate_case(statements):
            # can not put 'context' outside
            # BECAUSE the case expression CAN CONTAIN VARS from global scope
            self._push_context(Context.BLOCK)
            self._push_scope({})

            for stmt in statements:
                Qasm3Validator.validate_statement_type(SWITCH_BLACKLIST_STMTS, stmt, "switch")
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
                    case_expr, const_expr=True, reqd_type=qasm3_ast.IntType
                )

                if case_val in seen_values:
                    raise_qasm3_error(
                        f"Duplicate case value {case_val} in switch statement", span=case_expr.span
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

    def visit_statement(self, statement: qasm3_ast.Statement) -> None:
        """Visit a statement element.

        Args:
            statement (qasm3_ast.Statement): The statement to visit.

        Returns:
            None
        """
        logger.debug("Visiting statement '%s'", str(statement))

        visit_map = {
            qasm3_ast.Include: lambda x: None,  # No operation
            qasm3_ast.QuantumMeasurementStatement: self._visit_measurement,
            qasm3_ast.QuantumReset: self._visit_reset,
            qasm3_ast.QuantumBarrier: self._visit_barrier,
            qasm3_ast.QuantumGateDefinition: self._visit_gate_definition,
            qasm3_ast.QuantumGate: self._visit_generic_gate_operation,
            qasm3_ast.ClassicalDeclaration: self._visit_classical_declaration,
            qasm3_ast.ClassicalAssignment: self._visit_classical_assignment,
            qasm3_ast.ConstantDeclaration: self._visit_constant_declaration,
            qasm3_ast.BranchingStatement: self._visit_branching_statement,
            qasm3_ast.ForInLoop: self._visit_forin_loop,
            qasm3_ast.AliasStatement: self._visit_alias_statement,
            qasm3_ast.SwitchStatement: self._visit_switch_statement,
            qasm3_ast.SubroutineDefinition: self._visit_subroutine_definition,
            qasm3_ast.ExpressionStatement: lambda x: self._visit_function_call(x.expression),
            qasm3_ast.IODeclaration: lambda x: (_ for _ in ()).throw(
                NotImplementedError("OpenQASM 3 IO declarations not yet supported")
            ),
        }

        visitor_function = visit_map.get(type(statement))

        if visitor_function:
            visitor_function(statement)  # type: ignore[operator]
        else:
            raise_qasm3_error(
                f"Unsupported statement of type {type(statement)}", span=statement.span
            )

    def ir(self) -> str:
        return str(self._module)

    def bitcode(self) -> bytes:
        return self._module.bitcode
