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
Module containing the class for evaluating QASM3 expressions.

"""

from openqasm3.ast import (
    BinaryExpression,
    BooleanLiteral,
    BoolType,
    DurationLiteral,
    FloatLiteral,
    FunctionCall,
    Identifier,
    ImaginaryLiteral,
    IndexExpression,
    IntegerLiteral,
    UnaryExpression,
)

from ..exceptions import Qasm3ConversionError
from .imports import Qasm3FloatType, Qasm3IntType
from .maps import CONSTANTS_MAP, qasm3_expression_op_map
from .visitor_utils import Qasm3VisitorUtils


class Qasm3ExprEvaluator:
    """Class for evaluating QASM3 expressions."""

    @staticmethod
    def _check_var_in_scope(visitor_obj, var_name, expression):
        """
        Checks if a variable is in scope.
        Args:
            visitor_obj: The visitor object.
            var_name: The name of the variable to check.
            expression: The expression containing the variable.
        Raises:
            Qasm3ConversionError: If the variable is undefined in the current scope.
        """

        if not visitor_obj._check_in_scope(var_name, visitor_obj._get_curr_scope()):
            Qasm3VisitorUtils.print_err_location(expression.span)
            raise Qasm3ConversionError(f"Undefined identifier {var_name} in expression")

    @staticmethod
    def _check_var_constant(visitor_obj, var_name, const_expr, expression):
        """
        Checks if a variable is constant.

        Args:
            visitor_obj: The visitor object.
            var_name: The name of the variable to check.
            const_expr: Whether the expression is a constant.
            expression: The expression containing the variable.

        Raises:
            Qasm3ConversionError: If the variable is not a constant in the given
                                  expression.
        """
        const_var = visitor_obj._get_from_visible_scope(var_name).is_constant
        if const_expr and not const_var:
            Qasm3VisitorUtils.print_err_location(expression.span)
            raise Qasm3ConversionError(
                f"Variable '{var_name}' is not a constant in given expression"
            )

    @staticmethod
    def _check_var_type(visitor_obj, var_name, reqd_type, expression):
        """
        Check the type of a variable and raise an error if it does not match the
        required type.

        Args:
            visitor_obj: The visitor object.
            var_name: The name of the variable to check.
            reqd_type: The required type of the variable.
            expression: The expression where the variable is used.

        Raises:
            Qasm3ConversionError: If the variable has an invalid type for the required type.
        """

        if not Qasm3VisitorUtils.validate_variable_type(
            visitor_obj._get_from_visible_scope(var_name), reqd_type
        ):
            Qasm3VisitorUtils.print_err_location(expression.span)
            raise Qasm3ConversionError(
                f"Invalid type of variable {var_name} for required type {reqd_type}"
            )

    @staticmethod
    def _check_var_initialized(var_name, var_value, expression):
        """
        Checks if a variable is initialized and raises an error if it is not.
        Args:
            var_name (str): The name of the variable.
            var_value: The value of the variable.
            expression: The expression where the variable is used.
        Raises:
            Qasm3ConversionError: If the variable is uninitialized.
        """

        if var_value is None:
            Qasm3VisitorUtils.print_err_location(expression.span)
            raise Qasm3ConversionError(f"Uninitialized variable {var_name} in expression")

    @staticmethod
    def _get_var_value(visitor_obj, var_name, indices, expression):
        """
        Retrieves the value of a variable.
        Args:
            visitor_obj (Visitor): The visitor object.
            var_name (str): The name of the variable.
            indices (list): The indices of the variable (if it is an array).
            expression (Identifier or Expression): The expression representing the variable.
        Returns:
            var_value: The value of the variable.
        """

        var_value = None
        if isinstance(expression, Identifier):
            var_value = visitor_obj._get_from_visible_scope(var_name).value
        else:
            validated_indices = Qasm3VisitorUtils.analyse_classical_indices(
                indices, visitor_obj._get_from_visible_scope(var_name)
            )
            var_value = Qasm3VisitorUtils.find_array_element(
                visitor_obj._get_from_visible_scope(var_name).value, validated_indices
            )
        return var_value

    # pylint: disable-next=too-many-return-statements, too-many-statements
    @staticmethod
    def evaluate_expression(visitor_obj, expression, const_expr: bool = False, reqd_type=None):
        """Evaluate an expression. Scalar types are assigned by value.
        +
                Args:
                    expression (Any): The expression to evaluate.
                    const_expr (bool): Whether the expression is a constant. Defaults to False.
                    reqd_type (Any): The required type of the expression. Defaults to None.

                Returns:
                    Any : The result of the evaluation.

                Raises:
                    Qasm3ConversionError: If the expression is not supported.
        """
        if expression is None:
            return None

        if isinstance(expression, (ImaginaryLiteral, DurationLiteral)):
            Qasm3VisitorUtils.print_err_location(expression.span)
            raise Qasm3ConversionError(f"Unsupported expression type {type(expression)}")

        def _process_variable(var_name, indices=None):
            Qasm3ExprEvaluator._check_var_in_scope(visitor_obj, var_name, expression)
            Qasm3ExprEvaluator._check_var_constant(visitor_obj, var_name, const_expr, expression)
            Qasm3ExprEvaluator._check_var_type(visitor_obj, var_name, reqd_type, expression)
            var_value = Qasm3ExprEvaluator._get_var_value(
                visitor_obj, var_name, indices, expression
            )
            Qasm3ExprEvaluator._check_var_initialized(var_name, var_value, expression)
            return var_value

        if isinstance(expression, Identifier):
            var_name = expression.name
            if var_name in CONSTANTS_MAP:
                if not reqd_type or reqd_type == Qasm3FloatType:
                    return CONSTANTS_MAP[var_name]
                Qasm3VisitorUtils.print_err_location(expression.span)
                raise Qasm3ConversionError(
                    f"Constant {var_name} not allowed in non-float expression"
                )
            return _process_variable(var_name)

        if isinstance(expression, IndexExpression):
            var_name, indices = Qasm3VisitorUtils.analyse_index_expression(expression)
            return _process_variable(var_name, indices)

        if isinstance(expression, (BooleanLiteral, IntegerLiteral, FloatLiteral)):
            if reqd_type:
                if reqd_type == BoolType and isinstance(expression, BooleanLiteral):
                    return expression.value
                if reqd_type == Qasm3IntType and isinstance(expression, IntegerLiteral):
                    return expression.value
                if reqd_type == Qasm3FloatType and isinstance(expression, FloatLiteral):
                    return expression.value
                Qasm3VisitorUtils.print_err_location(expression.span)
                raise Qasm3ConversionError(
                    f"Invalid type {type(expression)} for required type {reqd_type}"
                )
            return expression.value

        if isinstance(expression, UnaryExpression):
            operand = Qasm3ExprEvaluator.evaluate_expression(
                visitor_obj, expression.expression, const_expr, reqd_type
            )
            if expression.op.name == "~" and not isinstance(operand, int):
                Qasm3VisitorUtils.print_err_location(expression.span)
                raise Qasm3ConversionError(
                    f"Unsupported expression type {type(operand)} in ~ operation"
                )
            return qasm3_expression_op_map(
                "UMINUS" if expression.op.name == "-" else expression.op.name, operand
            )
        if isinstance(expression, BinaryExpression):
            lhs = Qasm3ExprEvaluator.evaluate_expression(
                visitor_obj, expression.lhs, const_expr, reqd_type
            )
            rhs = Qasm3ExprEvaluator.evaluate_expression(
                visitor_obj, expression.rhs, const_expr, reqd_type
            )
            return qasm3_expression_op_map(expression.op.name, lhs, rhs)

        if isinstance(expression, FunctionCall):
            # function will not return a reqd / const type
            # Reference : https://openqasm.com/language/types.html#compile-time-constants
            # para      : 5
            return visitor_obj._visit_function_call(expression)

        Qasm3VisitorUtils.print_err_location(expression.span)
        raise Qasm3ConversionError(f"Unsupported expression type {type(expression)}")
