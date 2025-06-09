# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: disable=too-many-instance-attributes,too-many-lines,too-many-branches

"""
Module defining Profile-based Qasm3 Visitor for QIR generation.

This refactored approach uses Profile objects to handle different QIR profiles
without code duplication, based on JSON profile specifications.

"""
import logging
from typing import Any, Callable, List, Optional, Union

import openqasm3.ast as qasm3_ast
import pyqir
import pyqir._native
import pyqir.rt
from openqasm3.ast import UnaryOperator
from pyqir import qis


from ..profile import QIRVisitor
from ..profiles import Profile, ProfileRegistry

from .exceptions import raise_qasm3_error
from .maps import PYQIR_ONE_QUBIT_ROTATION_MAP, map_qasm_op_to_pyqir_callable

logger = logging.getLogger(__name__)


class QasmQIRVisitor(QIRVisitor):
    """A profile-aware visitor for converting OpenQASM 3 programs to QIR.

    This class is designed to traverse and interact with statements in an OpenQASM program.
        It uses Profile objects to handle different QIR profile requirements.

    Args:
        profile_name (str): Name of the QIR profile to use. Defaults to "Base".
        initialize_runtime (bool): If True, quantum runtime will be initialized. Defaults to True.
        record_output (bool): If True, output of the circuit will be recorded. Defaults to True.
        external_gates (list[str]): List of custom gates that should not be unrolled.
        emit_barrier_calls (bool): If True, barrier calls will be emitted. Defaults to True.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        profile_name: str = "Base",
        initialize_runtime: bool = True,
        record_output: bool = True,
        external_gates: Optional[list[str]] = None,
        emit_barrier_calls: bool = True,
    ):

        # Call parent class constructor
        super().__init__()

        # Get the profile
        self._profile = ProfileRegistry.get_profile(profile_name)

        self._llvm_module: pyqir.Module
        self._builder: pyqir.Builder
        self._entry_point: str = ""
        self._qubit_labels: dict[str, int] = {}
        self._clbit_labels: dict[str, int] = {}
        self._global_qreg_size_map: dict[str, int] = {}
        self._global_creg_size_map: dict[str, int] = {}
        self._custom_gates: dict[str, qasm3_ast.QuantumGateDefinition] = {}
        self._barrier_qubits: set[pyqir.Constant] = set()

        # Configuration
        self._initialize_runtime: bool = initialize_runtime
        self._record_output: bool = record_output
        self._emit_barrier_calls: bool = emit_barrier_calls

        # Profile-specific attributes
        if self._profile.should_track_qubit_measurement():
            self._measured_qubits: dict[int, bool] = {}

        # External gates
        if external_gates is None:
            external_gates = []
        self._external_gates_map: dict[str, Optional[pyqir.Function]] = {
            external_gate: None for external_gate in external_gates
        }

    @property
    def profile(self) -> Profile:
        """Get the current profile."""
        return self._profile

    @property
    def entry_point(self) -> str:
        return self._entry_point

    def visit_qasm3_module(self, module: QasmQIRModule) -> None:
        """
        Visit a Qasm3 module.

        Args:
            module (Qasm3Module): The module to visit.

        Returns:
            None
        """
        qasm3_module = module.qasm_program
        logger.debug(
            "Visiting Qasm3 module '%s' (%d) with profile '%s'",
            module.name,
            qasm3_module.num_qubits,
            self._profile.name,
        )

        self._llvm_module = module.llvm_module
        context = self._llvm_module.context
        # Set qir_profiles based on the profile being used
        qir_profiles = "adaptive" if self._profile.name == "AdaptiveExecution" else "base"

        entry = pyqir.entry_point(
            self._llvm_module,
            module.name,
            qasm3_module.num_qubits,
            qasm3_module.num_clbits,
            qir_profiles=qir_profiles,
        )

        self._entry_point = entry.name
        self._builder = pyqir.Builder(context)
        self._builder.insert_at_end(pyqir.BasicBlock(context, "entry", entry))

        if self._initialize_runtime:
            i8p = pyqir.PointerType(pyqir.IntType(context, 8))
            nullptr = pyqir.Constant.null(i8p)
            pyqir.rt.initialize(self._builder, nullptr)

    def finalize(self) -> None:
        self._check_and_apply_barrier()  # to check if we have an incomplete barrier at program end
        self._builder.ret(None)

    def record_output(self, module: QasmQIRModule) -> None:
        """Record output using profile-specific method."""
        self._profile.record_output_method(self, module)

    def _visit_register(
        self, register: Union[qasm3_ast.QubitDeclaration, qasm3_ast.ClassicalDeclaration]
    ) -> None:
        """Visit a register statement.

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

        for i in range(register_size):
            size_map[f"{register_name}"] = register_size
            label_map[f"{register_name}_{i}"] = current_size + i

        logger.debug("Added labels for register '%s'", str(register))

    def _get_op_bits(self, operation: Any, qubits: bool = True) -> list[pyqir.Constant]:
        """Get the quantum / classical bits for the operation.

        Args:
            operation (Any): The operation to get qubits for.
            reg_size_map (dict): The size map of the registers in scope.
            qubits (bool): Whether the bits are quantum bits or classical bits. Defaults to True.

        Returns:
            Unionlist[pyqir.Constant] : The bits for the operation.
        """
        qir_bits = []
        bit_list = []
        if isinstance(operation, qasm3_ast.QuantumMeasurementStatement):
            assert operation.target is not None
            bit_list = [operation.measure.qubit] if qubits else [operation.target]
        else:
            bit_list = (
                operation.qubits if isinstance(operation.qubits, list) else [operation.qubits]
            )

        for bit in bit_list:
            # as we have unrolled qasm3, we can assume that the bit is an IndexedIdentifier
            assert isinstance(bit, qasm3_ast.IndexedIdentifier)
            reg_name = bit.name.name

            assert isinstance(bit.indices, list) and len(bit.indices) == 1
            assert isinstance(bit.indices[0], list) and len(bit.indices[0]) == 1
            assert isinstance(bit.indices[0][0], qasm3_ast.IntegerLiteral)
            bit_id = bit.indices[0][0].value
            bit_ids = [bit_id]

            label_map = self._qubit_labels if qubits else self._clbit_labels
            reg_ids = [label_map[f"{reg_name}_{bit_id}"] for bit_id in bit_ids]

            qir_bits.extend(
                [
                    (
                        pyqir.qubit(self._llvm_module.context, bit_id)
                        if qubits
                        else pyqir.result(self._llvm_module.context, bit_id)
                    )
                    for bit_id in reg_ids
                ]
            )

        return qir_bits

    # pylint: disable=unused-argument
    def _check_qubit_use_after_measurement(self, qubit_ids: List[pyqir.Constant]) -> None:
        """
        Check qubit use after measurement based on profile capabilities.

        Args:
            qubit_ids (List[pyqir.Constant]): The qubit ids to check.

        Returns:
            None
        """
        if not self._profile.allow_qubit_use_after_measurement():
            # For profiles that don't allow it, we could add validation here
            for qubit_id in qubit_ids:
                qubit_id_result = pyqir.qubit_id(qubit_id)
                if qubit_id_result is not None and self._measured_qubits.get(
                    qubit_id_result, False
                ):
                    raise_qasm3_error(
                        f"Base Profile violation: Cannot use qubit {qubit_id_result} after measurement"  # pylint: disable=line-too-long
                    )

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
        source_ids = self._get_op_bits(statement, qubits=True)
        target_ids = self._get_op_bits(statement, qubits=False)
        measurement_func = self._profile.get_measurement_function()

        for src_id, tgt_id in zip(source_ids, target_ids):
            # Track measurement if profile supports it
            if self._profile.should_track_qubit_measurement():
                qubit_id_result = pyqir.qubit_id(src_id)
                if qubit_id_result is not None:
                    self._measured_qubits[qubit_id_result] = True

            measurement_func(self._builder, src_id, tgt_id)

    def _visit_reset(self, statement: qasm3_ast.QuantumReset) -> None:
        """Visit a reset statement element.

        Args:
            statement (qasm3_ast.QuantumReset): The reset statement to visit.

        Returns:
            None
        """
        logger.debug("Visiting reset statement '%s'", str(statement))
        qubit_ids = self._get_op_bits(statement, True)
        reset_func = self._profile.get_reset_function()

        for qid in qubit_ids:
            # Clear measurement tracking if profile supports it
            if self._profile.should_track_qubit_measurement():
                qubit_id_result = pyqir.qubit_id(qid)
                if qubit_id_result is not None:
                    self._measured_qubits[qubit_id_result] = False

            reset_func(self._builder, qid)

    def _barrier_applicable(self) -> bool:
        """Check if the barrier operation is applicable.

        Args:
            None

        Returns:
            bool: Whether the barrier operation is applicable.
        """
        if self._profile.restrictions.subset_barriers_allowed:
            return True

        total_qubit_count = sum(self._global_qreg_size_map.values())
        return len(self._barrier_qubits) == total_qubit_count

    def _check_and_apply_barrier(self) -> None:
        """Apply the barrier operation.

        Returns:
            None
        """
        if len(self._barrier_qubits) == 0:
            return

        if self._barrier_applicable():
            if self._emit_barrier_calls:
                barrier_func = self._profile.get_barrier_function()
                barrier_func(self._builder)
            self._barrier_qubits.clear()
        else:
            if self._emit_barrier_calls:
                raise_qasm3_error(
                    "Barrier operation on a qubit subset is not supported in pyqir",
                    err_type=NotImplementedError,
                )

    # pylint: disable=unused-argument
    def _visit_barrier(self, barrier: qasm3_ast.QuantumBarrier) -> None:
        """Visit a barrier statement element.

        Args:
            statement (qasm3_ast.QuantumBarrier): The barrier statement to visit.
        Returns:
            None
        """
        barrier_qubit = self._get_op_bits(barrier, qubits=True)
        self._barrier_qubits.update(barrier_qubit)

        # try to apply barrier in case all qubits are covered here itself
        if self._barrier_applicable():
            if self._emit_barrier_calls:
                barrier_func = self._profile.get_barrier_function()
                barrier_func(self._builder)
            self._barrier_qubits.clear()

    def _get_op_parameters(self, operation: qasm3_ast.QuantumGate) -> list[float]:
        """Get the parameters for the operation.

        Args:
            operation (qasm3_ast.QuantumGate): The operation to get parameters for.

        Returns:
            list[float]: The parameters for the operation.
        """
        param_list = []
        for param in operation.arguments:
            assert hasattr(param, "value")
            param_value = param.value
            param_list.append(param_value)

        return param_list

    def _visit_basic_gate_operation(self, operation: qasm3_ast.QuantumGate) -> None:
        """Visit a gate operation element.

        Args:
            operation (qasm3_ast.QuantumGate): The gate operation to visit.


        Returns:
            None

        Raises:
            Qasm3ConversionError: If the number of qubits is invalid.

        """

        logger.debug("Visiting basic gate operation '%s'", str(operation))
        op_name: str = operation.name.name
        op_qubits = self._get_op_bits(operation)

        # Profile-aware qubit usage check
        self._check_qubit_use_after_measurement(op_qubits)

        # Use existing gate mapping logic but with profile awareness
        gate_map = {
            "h": qis.h if self._profile.restrictions.prefer_qis_over_native else qis.h,
            "x": qis.x,
            "y": qis.y,
            "z": qis.z,
            "s": qis.s,
            "sdg": qis.s_adj,
            "t": qis.t,
            "tdg": qis.t_adj,
            "cx": qis.cx,
            "cnot": qis.cx,
            "cz": qis.cz,
            "ccx": qis.ccx,
            "swap": qis.swap,
            "rx": qis.rx,
            "ry": qis.ry,
            "rz": qis.rz,
        }

        if op_name in gate_map:
            qir_func = gate_map[op_name]
            if op_name in ["rx", "ry", "rz"]:
                op_parameters = self._get_op_parameters(operation)
                if op_parameters:
                    qir_func(self._builder, *op_parameters, *op_qubits)  # type: ignore
                else:
                    raise_qasm3_error(f"Parametric gate {op_name} requires parameters")
            else:
                qir_func(self._builder, *op_qubits)  # type: ignore
        elif op_name == "id":
            # Identity gate implementation
            qubit = op_qubits[0]
            qis.x(self._builder, qubit)
            qis.x(self._builder, qubit)
        else:
            # Use the mapping system
            try:
                qir_func, expected_qubit_count = map_qasm_op_to_pyqir_callable(op_name)
                if len(op_qubits) != expected_qubit_count:
                    raise_qasm3_error(
                        f"Gate {op_name} expects {expected_qubit_count} qubits,got {len(op_qubits)}"
                    )

                op_parameters = self._get_op_parameters(operation)
                is_parametric = op_name in PYQIR_ONE_QUBIT_ROTATION_MAP or op_name in [
                    "xx",
                    "xy",
                    "yy",
                    "zz",
                    "pswap",
                    "cp",
                    "cphaseshift",
                    "cp00",
                    "cphaseshift00",
                    "cp01",
                    "cphaseshift01",
                    "cp10",
                    "cphaseshift10",
                    "ms",
                    "prx",
                ]

                if is_parametric:
                    if not op_parameters:
                        raise_qasm3_error(f"Parametric gate {op_name} requires parameters")
                    qir_func(self._builder, *op_parameters, *op_qubits)
                else:
                    if op_parameters:
                        raise_qasm3_error(
                            f"Non-parametric gate {op_name} should not have parameters"
                        )
                    qir_func(self._builder, *op_qubits)

            except ValueError as conversion_error:
                if "Unsupported / undeclared QASM operation" in str(conversion_error):
                    raise_qasm3_error(f"Unsupported gate operation: {op_name}")
                else:
                    raise_qasm3_error(f"Error mapping gate {op_name}: {conversion_error}")
            except (TypeError, Exception) as e:  # pylint: disable=broad-exception-caught
                raise_qasm3_error(f"Error executing gate {op_name}: {e}")

    def _visit_external_gate_operation(self, operation: qasm3_ast.QuantumGate) -> None:
        """Visit an external gate operation element.

        Args:
            operation (qasm3_ast.QuantumGate): The gate operation to visit.


        Returns:
            None

        Raises:
            Qasm3ConversionError: If the number of qubits is invalid.

        """
        logger.debug("Visiting external gate operation '%s'", str(operation))
        op_name: str = operation.name.name
        op_qubits = self._get_op_bits(operation)
        op_qubit_count = len(op_qubits)

        self._check_qubit_use_after_measurement(op_qubits)

        if len(operation.modifiers) > 0:
            raise_qasm3_error(
                "Modifiers on externally linked gates are not supported in pyqir",
                err_type=NotImplementedError,
            )

        context = self._llvm_module.context
        qir_function = self._external_gates_map[op_name]
        if qir_function is None:
            # First time seeing this external gate -> define new function
            qir_function_arguments = [pyqir.Type.double(context)] * len(operation.arguments)
            qir_function_arguments += [pyqir.qubit_type(context)] * op_qubit_count

            qir_function = pyqir.Function(
                pyqir.FunctionType(pyqir.Type.void(context), qir_function_arguments),
                pyqir.Linkage.EXTERNAL,
                f"__quantum__qis__{op_name}__body",
                self._llvm_module,
            )
            self._external_gates_map[op_name] = qir_function

        op_parameters = None
        if len(operation.arguments) > 0:  # parametric gate
            op_parameters = self._get_op_parameters(operation)
            op_parameters = list(map(float, op_parameters))
        if op_parameters is not None:
            self._builder.call(qir_function, [*op_parameters, *op_qubits])
        else:
            self._builder.call(qir_function, op_qubits)

    def _visit_generic_gate_operation(self, operation: qasm3_ast.QuantumGate) -> None:
        """Visit a gate operation element.

        Args:
            operation (qasm3_ast.QuantumGate): The gate operation to visit.

        Returns:
            None
        """
        if operation.name.name in self._external_gates_map:
            self._visit_external_gate_operation(operation)
        else:
            self._visit_basic_gate_operation(operation)

    def _get_branch_params(self, condition: Any) -> tuple[str, int, bool]:
        """
        Get the branch parameters from the branching condition

        Args:
            condition (Any): The condition to analyze

        Returns:
            tuple[str, int, bool]: (register name, register id, positive branch)
        """

        def validate_index_expression(expression):
            assert isinstance(expression, qasm3_ast.IndexExpression)
            assert isinstance(expression.collection, qasm3_ast.Identifier)
            assert isinstance(expression.index, list) and len(expression.index) == 1
            assert isinstance(expression.index[0], qasm3_ast.IntegerLiteral)

        if isinstance(condition, qasm3_ast.UnaryExpression):
            validate_index_expression(condition.expression)
            return (
                condition.expression.collection.name,  # type: ignore
                condition.expression.index[0].value,  # type: ignore
                not condition.op == UnaryOperator["!"],
            )
        if isinstance(condition, qasm3_ast.BinaryExpression):
            assert isinstance(
                condition.rhs, qasm3_ast.BooleanLiteral
            ), "Invalid branching condition"
            validate_index_expression(condition.lhs)
            return (
                condition.lhs.collection.name,  # type: ignore
                condition.lhs.index[0].value,  # type: ignore
                condition.rhs.value,
            )
        if isinstance(condition, qasm3_ast.IndexExpression):
            assert isinstance(condition.index, list) and len(condition.index) == 1
            return (condition.collection.name, condition.index[0].value, True)  # type: ignore
        # default case
        return "", -1, True

    def _visit_branching_statement(self, statement: qasm3_ast.BranchingStatement) -> None:
        """Visit a branching statement element.

        Args:
            statement (qasm3_ast.BranchingStatement): The branching statement to visit.

        Returns:
            None
        """
        logger.debug("Visiting branching statement with profile '%s'", self._profile.name)

        # Check if profile supports conditional execution
        if not self._profile.capabilities.conditional_execution:
            raise_qasm3_error(
                f"Profile '{self._profile.name}' does not support conditional execution",
                err_type=NotImplementedError,
            )

        condition = statement.condition
        if_block = statement.if_block
        else_block = statement.else_block
        reg_name, reg_id, positive_branch = self._get_branch_params(condition)

        if not positive_branch:
            if_block, else_block = else_block, if_block

        def _visit_statement_block(block):
            if block:
                for stmt in block:
                    self.visit_statement(stmt)

        # Use profile-specific conditional function
        conditional_func = self._profile.get_conditional_function()
        zero_callback: Callable[[], None] = lambda: _visit_statement_block(else_block)
        one_callback: Callable[[], None] = lambda: _visit_statement_block(if_block)

        conditional_func(
            self._builder,
            pyqir.result(self._llvm_module.context, self._clbit_labels[f"{reg_name}_{reg_id}"]),
            zero=zero_callback,
            one=one_callback,
        )

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
            qasm3_ast.QubitDeclaration: self._visit_register,
            qasm3_ast.ClassicalDeclaration: self._visit_register,
            qasm3_ast.QuantumMeasurementStatement: self._visit_measurement,
            qasm3_ast.QuantumReset: self._visit_reset,
            qasm3_ast.QuantumBarrier: self._visit_barrier,
            qasm3_ast.QuantumGate: self._visit_generic_gate_operation,
            qasm3_ast.BranchingStatement: self._visit_branching_statement,
            qasm3_ast.QuantumPhase: lambda x: None,  # No operation
        }

        visitor_function = visit_map.get(type(statement))

        if not isinstance(statement, qasm3_ast.QuantumBarrier):
            self._check_and_apply_barrier()

        if visitor_function:
            visitor_function(statement)  # type: ignore[operator]
        else:
            raise_qasm3_error(
                f"Unsupported statement of type {type(statement)}", span=statement.span
            )

    def ir(self) -> str:
        return str(self._llvm_module)

    def bitcode(self) -> bytes:
        return self._llvm_module.bitcode
