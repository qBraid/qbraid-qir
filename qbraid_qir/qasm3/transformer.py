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
Module with transformation functions for QASM3 visitor

"""
from typing import Any, Union

from openqasm3.ast import (
    BinaryExpression,
    DiscreteSet,
    Identifier,
    IndexedIdentifier,
    IndexExpression,
    IntegerLiteral,
    QuantumGate,
    UnaryExpression,
)

from .exceptions import Qasm3ConversionError, raise_qasm3_error


class Qasm3Transformer:
    """Class with utility functions for transforming QASM3 elements"""

    # ************* Classical Variable utilities *************
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
                raise_qasm3_error(
                    f"Unsupported discrete set value {value} in discrete set",
                    Qasm3ConversionError,
                    discrete_set.span,
                )
            values.append(value.value)
        return values

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
                raise_qasm3_error(
                    f"Indexing '{qubit.name.name}' not supported in gate definition",
                    Qasm3ConversionError,
                    qubit.span,
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

    # ************* Quantum Gate utilities *************

    # ************* If statement utilities *************
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

    # ************* If statement utilities *************
