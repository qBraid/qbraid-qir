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
from typing import Any, Optional

from openqasm3.ast import ArrayType, ClassicalDeclaration
from openqasm3.ast import IntType as Qasm3IntType
from openqasm3.ast import (
    QuantumGate,
    QuantumGateDefinition,
    ReturnStatement,
    Statement,
    SubroutineDefinition,
)

from .elements import Variable
from .exceptions import Qasm3ConversionError, raise_qasm3_error
from .maps import LIMITS_MAP, VARIABLE_TYPE_MAP, qasm_variable_type_cast


class Qasm3Validator:
    """Class with validation functions for QASM3 visitor"""

    # ************* Generic validations *************
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
                raise_qasm3_error(
                    f"Unsupported statement {stmt_type} in {construct} block",
                    Qasm3ConversionError,
                    statement.span,
                )

            if statement.type.__class__ == ArrayType:
                raise_qasm3_error(
                    f"Unsupported statement {stmt_type} with {statement.type.__class__}"
                    f" in {construct} block",
                    Qasm3ConversionError,
                    statement.span,
                )

    # ************* Generic validations *************

    # ************* Classical Variable utilities *************

    @staticmethod
    def validate_variable_type(variable: Optional[Variable], reqd_type: Any) -> bool:
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
                raise_qasm3_error(
                    f"Value {value} out of limits for variable {variable.name} with "
                    f"base size {base_size}",
                    Qasm3ConversionError,
                )

        elif type_to_match == float:
            base_size = variable.base_size
            left, right = 0, 0

            if base_size == 32:
                left, right = -(LIMITS_MAP["float_32"]), (LIMITS_MAP["float_32"])
            else:
                left, right = -(LIMITS_MAP["float_64"]), (LIMITS_MAP["float_64"])

            if type_casted_value < left or type_casted_value > right:
                raise_qasm3_error(
                    f"Value {value} out of limits for variable {variable.name} with "
                    f"base size {base_size}",
                    Qasm3ConversionError,
                )
        elif type_to_match == bool:
            pass
        else:
            raise_qasm3_error(
                f"Invalid type {type_to_match} for variable {variable.name}", TypeError
            )

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
            raise_qasm3_error(
                f"Invalid dimensions for array assignment to variable {variable.name}. "
                f"Expected {dimensions[0]} but got {len(values)}",
                Qasm3ConversionError,
            )
        for i, value in enumerate(values):
            if isinstance(value, list):
                Qasm3Validator.validate_array_assignment_values(variable, dimensions[1:], value)
            else:
                if len(dimensions) != 1:
                    raise_qasm3_error(
                        f"Invalid dimensions for array assignment to variable {variable.name}. "
                        f"Expected {len(dimensions)} but got 1",
                        Qasm3ConversionError,
                    )
                values[i] = Qasm3Validator.validate_variable_assignment_value(variable, value)

    # ************* Classical Variable utilities *************

    # ************* Quantum Gate utilities *************

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
            raise_qasm3_error(
                f"Parameter count mismatch for gate {operation.name.name}: "
                f"expected {gate_def_num_args} argument{s}, but got {op_num_args} instead.",
                Qasm3ConversionError,
                operation.span,
            )

        gate_def_num_qubits = len(gate_definition.qubits)
        if qubits_in_op != gate_def_num_qubits:
            s = "" if gate_def_num_qubits == 1 else "s"
            raise_qasm3_error(
                f"Qubit count mismatch for gate {operation.name.name}: "
                f"expected {gate_def_num_qubits} qubit{s}, but got {qubits_in_op} instead.",
                Qasm3ConversionError,
                operation.span,
            )

    # ************* Quantum Gate utilities *************

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
                raise_qasm3_error(
                    f"Return type mismatch for subroutine '{subroutine_def.name.name}'."
                    f" Expected void but got {type(return_value)}",
                    Qasm3ConversionError,
                    return_statement.span,
                )
        else:
            if return_value is None:
                raise_qasm3_error(
                    f"Return type mismatch for subroutine '{subroutine_def.name.name}'."
                    f" Expected {subroutine_def.return_type} but got void",
                    Qasm3ConversionError,
                    return_statement.span,
                )
            base_size = 1
            if hasattr(subroutine_def.return_type, "size"):
                base_size = subroutine_def.return_type.size.value

            return Qasm3Validator.validate_variable_assignment_value(
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
