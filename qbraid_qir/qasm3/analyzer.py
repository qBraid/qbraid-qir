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
Module with analysis functions for QASM3 visitor

"""
from typing import Any

from openqasm3.ast import (
    BinaryExpression,
    IndexExpression,
    IntegerLiteral,
    RangeDefinition,
    UnaryExpression,
)

from .elements import Variable
from .exceptions import Qasm3ConversionError, raise_qasm3_error


class Qasm3Analyzer:
    """Class with utility functions for analyzing QASM3 elements"""

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
            raise_qasm3_error(
                message=f"Indexing error. Variable {var_name} is not an array",
                err_type=Qasm3ConversionError,
                span=indices[0].span,
            )
        if len(indices) != len(var_dimensions):
            raise_qasm3_error(
                message=f"Invalid number of indices for variable {var_name}. "
                f"Expected {len(var_dimensions)} but got {len(indices)}",
                err_type=Qasm3ConversionError,
                span=indices[0].span,
            )

        for i, index in enumerate(indices):
            if isinstance(index, RangeDefinition):
                raise_qasm3_error(
                    message=f"Range based indexing {index} not supported for "
                    f"classical variable {var_name}",
                    err_type=Qasm3ConversionError,
                    span=index.span,
                )

            if not isinstance(index, IntegerLiteral):
                raise_qasm3_error(
                    message=f"Unsupported index type {type(index)} for "
                    f"classical variable {var_name}",
                    err_type=Qasm3ConversionError,
                    span=index.span,
                )
            index_value = index.value
            curr_dimension = var_dimensions[i]

            if index_value < 0 or index_value >= curr_dimension:
                raise_qasm3_error(
                    message=f"Index {index_value} out of bounds for dimension {i+1} "
                    f"of variable {var_name}",
                    err_type=Qasm3ConversionError,
                    span=index.span,
                )
            indices_list.append(index_value)

        return indices_list

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
    def analyse_branch_condition(condition: Any) -> bool:
        """
        analyze the branching condition to determine the branch to take

        Args:
            condition (Any): The condition to analyze

        Returns:
            bool: The branch to take
        """

        if isinstance(condition, UnaryExpression):
            if condition.op.name != "!":
                raise_qasm3_error(
                    message=f"Unsupported unary expression '{condition.op.name}' in if condition",
                    err_type=Qasm3ConversionError,
                    span=condition.span,
                )
            return False
        if isinstance(condition, BinaryExpression):
            if condition.op.name != "==":
                raise_qasm3_error(
                    message=f"Unsupported binary expression '{condition.op.name}' in if condition",
                    err_type=Qasm3ConversionError,
                    span=condition.span,
                )
            if not isinstance(condition.lhs, IndexExpression):
                raise_qasm3_error(
                    message=f"Unsupported expression type '{type(condition.rhs)}' in if condition",
                    err_type=Qasm3ConversionError,
                    span=condition.span,
                )
            return condition.rhs.value != 0
        if not isinstance(condition, IndexExpression):
            raise_qasm3_error(
                message=(
                    f"Unsupported expression type '{type(condition)}' in if condition. "
                    "Can only be a simple comparison"
                ),
                err_type=Qasm3ConversionError,
                span=condition.span,
            )
        return True
