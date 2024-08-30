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
from typing import Any, Optional, Union

from openqasm3.ast import (
    BinaryExpression,
    DiscreteSet,
    Expression,
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
    def analyze_classical_indices(indices: list[Any], var: Variable) -> list:
        """Validate the indices for a classical variable.

        Args:
            indices (list[list[Any]]): The indices to validate.
            var_name (Variable): The variable to verify

        Raises:
            Qasm3ConversionError: If the indices are invalid.

        Returns:
            list[list]: The list of indices. Note, we can also have a list of indices within
                        a list if the variable is a multi-dimensional array.
        """
        indices_list = []
        var_name = var.name
        var_dimensions: Optional[list[int]] = var.dims

        if var_dimensions is None or len(var_dimensions) == 0:
            raise_qasm3_error(
                message=f"Indexing error. Variable {var_name} is not an array",
                err_type=Qasm3ConversionError,
                span=indices[0].span,
            )
        if isinstance(indices, DiscreteSet):
            indices = indices.values

        if len(indices) != len(var_dimensions):  # type: ignore[arg-type]
            raise_qasm3_error(
                message=f"Invalid number of indices for variable {var_name}. "
                f"Expected {len(var_dimensions)} but got {len(indices)}",  # type: ignore[arg-type]
                err_type=Qasm3ConversionError,
                span=indices[0].span,
            )

        def _validate_index(index, dimension, var_name, span, dim_num):
            if index < 0 or index >= dimension:
                raise_qasm3_error(
                    message=f"Index {index} out of bounds for dimension {dim_num} "
                    f"of variable {var_name}",
                    err_type=Qasm3ConversionError,
                    span=span,
                )

        def _validate_step(start_id, end_id, step, span):
            if (step < 0 and start_id < end_id) or (step > 0 and start_id > end_id):
                direction = "less than" if step < 0 else "greater than"
                raise_qasm3_error(
                    message=f"Index {start_id} is {direction} {end_id} but step"
                    f" is {'negative' if step < 0 else 'positive'}",
                    err_type=Qasm3ConversionError,
                    span=span,
                )

        for i, index in enumerate(indices):
            if not isinstance(index, (RangeDefinition, IntegerLiteral)):
                raise_qasm3_error(
                    message=f"Unsupported index type {type(index)} for "
                    f"classical variable {var_name}",
                    err_type=Qasm3ConversionError,
                    span=index.span,
                )

            if isinstance(index, RangeDefinition):
                range_def = index
                # TODO : add support for identifiers here
                assert var_dimensions is not None

                start_id = (
                    range_def.start.value if isinstance(range_def.start, IntegerLiteral) else 0
                )
                end_id = (
                    range_def.end.value
                    if isinstance(range_def.end, IntegerLiteral)
                    else var_dimensions[i] - 1
                )
                step = range_def.step.value if isinstance(range_def.step, IntegerLiteral) else 1

                _validate_index(start_id, var_dimensions[i], var_name, range_def.span, i)
                _validate_index(end_id, var_dimensions[i], var_name, range_def.span, i)
                _validate_step(start_id, end_id, step, range_def.span)

                indices_list.append((start_id, end_id, step))

            if isinstance(index, IntegerLiteral):
                index_value = index.value
                curr_dimension = var_dimensions[i]  # type: ignore[index]
                _validate_index(index_value, curr_dimension, var_name, index.span, i)

                indices_list.append((index_value, index_value, 1))

        return indices_list

    @staticmethod
    def analyze_index_expression(
        index_expr: IndexExpression,
    ) -> tuple[str, list[Union[Any, Expression, RangeDefinition]]]:
        """Analyze an index expression to get the variable name and indices.

        Args:
            index_expr (IndexExpression): The index expression to analyze.

        Returns:
            tuple[str, list[Any]]: The variable name and indices in openqasm objects

        """
        indices: list[Any] = []
        var_name = ""
        comma_separated = False

        if isinstance(index_expr.collection, IndexExpression):
            while isinstance(index_expr, IndexExpression):
                if isinstance(index_expr.index, list):
                    indices.append(index_expr.index[0])
                    index_expr = index_expr.collection
        else:
            comma_separated = True
            indices = index_expr.index  # type: ignore[assignment]
        var_name = (
            index_expr.collection.name  # type: ignore[attr-defined]
            if comma_separated
            else index_expr.name  # type: ignore[attr-defined]
        )
        if not comma_separated:
            indices = indices[::-1]

        return var_name, indices

    @staticmethod
    def find_array_element(multi_dim_arr: list[Any], indices: list[tuple[int, int, int]]) -> Any:
        """Find the value of an array at the specified indices.

        Args:
            multi_dim_arr (list): The multi-dimensional list to search.
            indices (list[int]): The indices to search.

        Returns:
            Any: The value at the specified indices.
        """
        temp = multi_dim_arr
        for index_element in indices:
            start, end, step = index_element
            temp = temp[start : end + 1 : step]
            if start == end:  # if literal index, we decrease the dimension by 1
                temp = temp[0]
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
            return condition.rhs.value != 0  # type: ignore[attr-defined]
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
