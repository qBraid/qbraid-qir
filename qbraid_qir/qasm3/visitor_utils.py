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
Module with utility functions for QASM3 visitor

"""
import logging
from typing import Any, Optional, Union

from openqasm3.ast import (
    ArrayType,
    BinaryExpression,
    ClassicalDeclaration,
    DiscreteSet,
    Identifier,
    IndexedIdentifier,
    IndexExpression,
    IntegerLiteral,
)
from openqasm3.ast import IntType as Qasm3IntType
from openqasm3.ast import (
    QuantumGate,
    QuantumGateDefinition,
    RangeDefinition,
    ReturnStatement,
    Span,
    Statement,
    SubroutineDefinition,
    UnaryExpression,
)

from .elements import Variable
from .exceptions import Qasm3ConversionError
from .maps import LIMITS_MAP, VARIABLE_TYPE_MAP, qasm_variable_type_cast


class Qasm3VisitorUtils:
    """Class with utility functions for QASM3 visitor"""

    # ************* Generic utilities *************
    @staticmethod
    def print_err_location(element: Span) -> None:
        """
        Print an error message with the location of the element in the source code.

        Args:
            element (Span): The element in the source code.
        """
        logging.error(
            "Error at line %s, column %s in QASM file", element.start_line, element.start_column
        )

    @staticmethod
    def extract_values_from_discrete_set(discrete_set: DiscreteSet) -> list[int]:
        """Extract the values from a discrete set.

        Args:
            discrete_set (DiscreteSet): The discrete set to extract values from.

        Returns:
            list[int]: The extracted values.
        """
        values = []
        for value in discrete_set.values:
            if not isinstance(value, IntegerLiteral):
                Qasm3VisitorUtils.print_err_location(discrete_set.span)
                raise Qasm3ConversionError(
                    f"Unsupported discrete set value {value} in discrete set"
                )
            values.append(value.value)
        return values

    @staticmethod
    def validate_register_index(index: Optional[int], size: int, qubit: bool = False) -> None:
        """Validate the index for a register.

        Args:
            index (optional, int): The index to validate.
            size (int): The size of the register.
            qubit (bool): Whether the register is a qubit register.

        Raises:
            Qasm3ConversionError: If the index is out of range.
        """
        if index is None or 0 <= index < size:
            return None

        raise Qasm3ConversionError(
            f"Index {index} out of range for register of size {size} in "
            f"{'qubit' if qubit else 'clbit'}"
        )

    @staticmethod
    def validate_statement_type(
        blacklisted_stmts: set, statement: Statement, construct: str
    ) -> None:
        """Validate the type of a statement.

        Args:
            blacklisted_stmts (set): The set of blacklisted statements.
            statement (Statement): The statement to validate.
            construct (str): The construct the statement is in.

        Raises:
            Qasm3ConversionError: If the statement is not supported.
        """
        stmt_type = statement.__class__
        if stmt_type in blacklisted_stmts:
            if stmt_type != ClassicalDeclaration:
                Qasm3VisitorUtils.print_err_location(statement.span)
                raise Qasm3ConversionError(
                    f"Unsupported statement {stmt_type} in {construct} block"
                )

            if statement.type.__class__ == ArrayType:
                Qasm3VisitorUtils.print_err_location(statement.span)
                raise Qasm3ConversionError(
                    f"Unsupported statement {stmt_type} with {statement.type.__class__}"
                    f" in {construct} block"
                )

    # ************* Generic utilities *************

    # ************* Classical Variable utilities *************
    @staticmethod
    def validate_variable_type(variable: Variable, reqd_type: Any) -> bool:
        """Validate the type of a variable.

        Args:
            variable (Variable): The variable to validate.
            reqd_type (Any): The required Qasm3 type of the variable.
        """
        if not reqd_type:
            return True
        if variable is None:
            return False
        return isinstance(variable.base_type, reqd_type)

    @staticmethod
    def validate_variable_assignment_value(variable: Variable, value) -> None:
        """Validate the assignment of a value to a variable.

        Args:
            variable (Variable): The variable to assign to.
            value (Any): The value to assign.

        Raises:
            Qasm3ConversionError: If the value is not of the correct type.
        """
        # check 1 - type match
        qasm_type = variable.base_type.__class__
        base_size = variable.base_size

        try:
            type_to_match = VARIABLE_TYPE_MAP[qasm_type]
        except KeyError as err:
            raise Qasm3ConversionError(
                f"Invalid type {qasm_type} for variable {variable.name}"
            ) from err

        # For each type we will have a "castable" type set and its corresponding cast operation
        type_casted_value = qasm_variable_type_cast(qasm_type, variable.name, base_size, value)
        # check 2 - range match , if bits mentioned in base size
        if type_to_match == int:
            base_size = variable.base_size
            left, right = 0, 0
            if qasm_type == Qasm3IntType:
                left, right = (
                    -1 * (2 ** (base_size - 1)),
                    2 ** (base_size - 1) - 1,
                )
            else:
                # would be uint only so we correctly get this
                left, right = 0, 2**base_size - 1
            if type_casted_value < left or type_casted_value > right:
                raise Qasm3ConversionError(
                    f"Value {type_casted_value} out of limits for variable {variable.name} "
                    f"with base size {base_size}"
                )

        elif type_to_match == float:
            base_size = variable.base_size
            left, right = 0, 0

            if base_size == 32:
                left, right = -(LIMITS_MAP["float_32"]), (LIMITS_MAP["float_32"])
            else:
                left, right = -(LIMITS_MAP["float_64"]), (LIMITS_MAP["float_64"])

            if type_casted_value < left or type_casted_value > right:
                raise Qasm3ConversionError(
                    f"Value {value} out of limits for variable {variable.name} "
                    f"with base size {base_size}"
                )
        elif type_to_match == bool:
            pass
        else:
            raise TypeError(f"Invalid type {type_to_match} for variable {variable.name}")

        return type_casted_value

    @staticmethod
    def validate_array_assignment_values(
        variable: Variable, dimensions: list[int], values: list
    ) -> None:
        """Validate the assignment of values to an array variable.

        Args:
            variable (Variable): The variable to assign to.
            values (list[Any]): The values to assign.

        Raises:
            Qasm3ConversionError: If the values are not of the correct type.
        """
        # recursively check the array
        if len(values) != dimensions[0]:
            raise Qasm3ConversionError(
                f"Invalid dimensions for array assignment to variable {variable.name}. "
                f"Expected {dimensions[0]} but got {len(values)}"
            )
        for i, value in enumerate(values):
            if isinstance(value, list):
                Qasm3VisitorUtils.validate_array_assignment_values(variable, dimensions[1:], value)
            else:
                if len(dimensions) != 1:
                    raise Qasm3ConversionError(
                        f"Invalid dimensions for array assignment to variable {variable.name}. "
                        f"Expected {len(dimensions)} but got 1"
                    )
                values[i] = Qasm3VisitorUtils.validate_variable_assignment_value(variable, value)

    @staticmethod
    def analyze_classical_indices(indices: list[IntegerLiteral], var: Variable) -> None:
        """Validate the indices for a classical variable.

        Args:
            indices (list[list[Any]]): The indices to validate.
            var_name (Variable): The variable to verify

        Raises:
            Qasm3ConversionError: If the indices are invalid.

        Returns:
            list: The list of indices.
        """
        indices_list = []
        var_name = var.name
        var_dimensions = var.dims

        if not var_dimensions:
            Qasm3VisitorUtils.print_err_location(indices[0].span)
            raise Qasm3ConversionError(f"Indexing error. Variable {var_name} is not an array")

        if len(indices) != len(var_dimensions):
            Qasm3VisitorUtils.print_err_location(indices[0].span)
            raise Qasm3ConversionError(
                f"Invalid number of indices for variable {var_name}. "
                f"Expected {len(var_dimensions)} but got {len(indices)}"
            )

        for i, index in enumerate(indices):
            if isinstance(index, RangeDefinition):
                Qasm3VisitorUtils.print_err_location(index.span)
                raise Qasm3ConversionError(
                    f"Range based indexing {index} not supported for classical variable {var_name}"
                )
            if not isinstance(index, IntegerLiteral):
                Qasm3VisitorUtils.print_err_location(index.span)
                raise Qasm3ConversionError(
                    f"Unsupported index type {type(index)} for classical variable {var_name}"
                )
            index_value = index.value
            curr_dimension = var_dimensions[i]

            if index_value < 0 or index_value >= curr_dimension:
                Qasm3VisitorUtils.print_err_location(index.span)
                raise Qasm3ConversionError(
                    f"Index {index_value} out of bounds for dimension {i+1} of variable {var_name}"
                )
            indices_list.append(index_value)

        return indices_list

    @staticmethod
    def update_array_element(multi_dim_arr: list[Any], indices: list[int], value: Any) -> None:
        """Update the value of an array at the specified indices.

        Args:
            multi_dim_arr (list): The multi-dimensional array to update.
            indices (list[int]): The indices to update.
            value (Any): The value to update.

        Returns:
            None
        """
        temp = multi_dim_arr
        for index in indices[:-1]:
            temp = temp[index]
        temp[indices[-1]] = value

    @staticmethod
    def find_array_element(multi_dim_arr: list[Any], indices: list[int]) -> Any:
        """Find the value of an array at the specified indices.

        Args:
            multi_dim_arr (list): The multi-dimensional list to search.
            indices (list[int]): The indices to search.

        Returns:
            Any: The value at the specified indices.
        """
        temp = multi_dim_arr
        for index in indices:
            temp = temp[index]
        return temp

    @staticmethod
    def analyze_index_expression(index_expr: IndexExpression) -> tuple[str, list[list]]:
        """analyze an index expression to get the variable name and indices.

        Args:
            index_expr (IndexExpression): The index expression to analyze.

        Returns:
            tuple[str, list[list]]: The variable name and indices.

        """
        indices = []
        var_name = None
        comma_separated = False

        if isinstance(index_expr.collection, IndexExpression):
            while isinstance(index_expr, IndexExpression):
                indices.append(index_expr.index[0])
                index_expr = index_expr.collection
        else:
            comma_separated = True
            indices = index_expr.index

        var_name = index_expr.collection.name if comma_separated else index_expr.name
        if not comma_separated:
            indices = indices[::-1]

        return var_name, indices

    # ************* Classical Variable utilities *************

    # ************* Quantum Gate utilities *************
    @staticmethod
    def transform_gate_qubits(gate_op: QuantumGate, qubit_map: dict) -> None:
        """Transform the qubits of a gate operation with a qubit map.

        Args:
            gate_op (QuantumGate): The gate operation to transform.
            qubit_map (Dict[str, IndexedIdentifier]): The qubit map to use for transformation.

        Returns:
            None
        """
        for i, qubit in enumerate(gate_op.qubits):
            if isinstance(qubit, IndexedIdentifier):
                Qasm3VisitorUtils.print_err_location(qubit.span)
                raise Qasm3ConversionError(
                    f"Indexing '{qubit.name.name}' not supported in gate definition"
                )
            gate_op.qubits[i] = qubit_map[qubit.name]

    @staticmethod
    def transform_gate_params(gate_op: QuantumGate, param_map: dict) -> None:
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

    @staticmethod
    def validate_gate_call(
        operation: QuantumGate,
        gate_definition: QuantumGateDefinition,
        qubits_in_op,
    ) -> None:
        """Validate the call of a gate operation.

        Args:
            operation (QuantumGate): The gate operation to validate.
            gate_definition (QuantumGateDefinition): The gate definition to validate against.
            qubits_in_op (int): The number of qubits in the operation.

        Raises:
            Qasm3ConversionError: If the number of parameters or qubits is invalid.
        """
        op_num_args = len(operation.arguments)
        gate_def_num_args = len(gate_definition.arguments)
        if op_num_args != gate_def_num_args:
            s = "" if gate_def_num_args == 1 else "s"
            Qasm3VisitorUtils.print_err_location(operation.span)
            raise Qasm3ConversionError(
                f"Parameter count mismatch for gate {operation.name.name}: "
                f"expected {gate_def_num_args} argument{s}, "
                f"but got {op_num_args} instead."
            )

        gate_def_num_qubits = len(gate_definition.qubits)
        if qubits_in_op != gate_def_num_qubits:
            s = "" if gate_def_num_qubits == 1 else "s"
            Qasm3VisitorUtils.print_err_location(operation.span)
            raise Qasm3ConversionError(
                f"Qubit count mismatch for gate {operation.name.name}: "
                f"expected {gate_def_num_qubits} qubit{s}, "
                f"but got {qubits_in_op} instead."
            )

    # ************* Quantum Gate utilities *************

    # ************* IF statement utilities *************
    @staticmethod
    def analyze_branch_condition(condition) -> bool:
        """
        analyze the branching condition to determine the branch to take

        Args:
            condition (Any): The condition to analyze

        Returns:
            bool: The branch to take
        """

        if isinstance(condition, UnaryExpression):
            if condition.op.name != "!":
                Qasm3VisitorUtils.print_err_location(condition.span)
                raise Qasm3ConversionError(
                    f"Unsupported unary expression '{condition.op.name}' in if condition"
                )
            return False
        if isinstance(condition, BinaryExpression):
            if condition.op.name != "==":
                Qasm3VisitorUtils.print_err_location(condition.span)
                raise Qasm3ConversionError(
                    f"Unsupported binary expression '{condition.op.name}' in if condition"
                )
            if not isinstance(condition.lhs, IndexExpression):
                Qasm3VisitorUtils.print_err_location(condition.span)
                raise Qasm3ConversionError(
                    f"Unsupported expression type '{type(condition.lhs)}' in if condition"
                )
            return condition.rhs.value != 0
        if not isinstance(condition, IndexExpression):
            Qasm3VisitorUtils.print_err_location(condition.span)
            raise Qasm3ConversionError(
                f"Unsupported expression type '{type(condition)}' in if condition. "
                "Can only be a simple comparison"
            )
        return True

    @staticmethod
    def get_branch_params(condition) -> tuple[Union[int, None], Union[str, None]]:
        """
        Get the branch parameters from the branching condition

        Args:
            condition (Any): The condition to analyze

        Returns:
            tuple[Union[int, None], Union[str, None]]: The branch parameters
        """
        if isinstance(condition, UnaryExpression):
            return (
                condition.expression.index[0].value,
                condition.expression.collection.name,
            )
        if isinstance(condition, BinaryExpression):
            return condition.lhs.index[0].value, condition.lhs.collection.name
        if isinstance(condition, IndexExpression):
            return condition.index[0].value, condition.collection.name
        return None, None

    # ************* IF statement utilities *************

    # ************* Function evaluation utilities *************

    @staticmethod
    # pylint: disable=inconsistent-return-statements
    def validate_return_statement(
        subroutine_def: SubroutineDefinition,
        return_statement: ReturnStatement,
        return_value: Any,
    ):
        """Validate the return type of a function.

        Args:
            subroutine_def (SubroutineDefinition): The subroutine definition.
            return_statement (ReturnStatement): The return statement.
            return_value (Any): The return value.

        Raises:
            Qasm3ConversionError: If the return type is invalid.
        """

        if subroutine_def.return_type is None:
            if return_value is not None:
                Qasm3VisitorUtils.print_err_location(return_statement.span)
                raise Qasm3ConversionError(
                    f"Return type mismatch for subroutine '{subroutine_def.name.name}'."
                    f" Expected void but got {type(return_value)}"
                )
        else:
            if return_value is None:
                Qasm3VisitorUtils.print_err_location(return_statement.span)
                raise Qasm3ConversionError(
                    f"Return type mismatch for subroutine '{subroutine_def.name.name}'."
                    f" Expected {subroutine_def.return_type} but got void"
                )
            base_size = 1
            if hasattr(subroutine_def.return_type, "size"):
                base_size = subroutine_def.return_type.size.value

            return Qasm3VisitorUtils.validate_variable_assignment_value(
                Variable(
                    subroutine_def.name.name + "_return",
                    subroutine_def.return_type,
                    base_size,
                    None,
                    None,
                ),
                return_value,
            )

    @staticmethod
    def validate_unique_qubits(qubit_map: dict, reg_name: str, indices: list) -> bool:
        """
        Validates that the qubits in the given register are unique.

        Args:
            qubit_map (dict): Dictionary of qubits.
            reg_name (str): The name of the register.
            indices (list): A list of indices representing the qubits.

        Raises:
            Qasm3ConversionError: If duplicate qubits are found in the function call.
        """
        if reg_name not in qubit_map:
            qubit_map[reg_name] = set(indices)
        else:
            for idx in indices:
                if idx in qubit_map[reg_name]:
                    return False
        return True

    # ************* Function evaluation utilities *************
