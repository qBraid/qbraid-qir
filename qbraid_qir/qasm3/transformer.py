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
from typing import Any, Optional, Union

from openqasm3.ast import (
    BinaryExpression,
    DiscreteSet,
    FloatLiteral,
    Identifier,
    IndexedIdentifier,
    IndexExpression,
    IntegerLiteral,
    QuantumBarrier,
    QuantumGate,
    QuantumReset,
    RangeDefinition,
    UnaryExpression,
)

from .exceptions import raise_qasm3_error
from .expressions import Qasm3ExprEvaluator
from .validator import Qasm3Validator


class Qasm3Transformer:
    """Class with utility functions for transforming QASM3 elements"""

    visitor_obj = None

    @classmethod
    def set_visitor_obj(cls, visitor_obj):
        cls.visitor_obj = visitor_obj

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
                    span=discrete_set.span,
                )
            values.append(value.value)
        return values

    @staticmethod
    def get_qubits_from_range_definition(
        range_def: RangeDefinition, qreg_size: int, is_qubit_reg: bool
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
            else Qasm3ExprEvaluator.evaluate_expression(range_def.start)
        )
        end_qid = (
            qreg_size
            if range_def.end is None
            else Qasm3ExprEvaluator.evaluate_expression(range_def.end)
        )
        step = (
            1 if range_def.step is None else Qasm3ExprEvaluator.evaluate_expression(range_def.step)
        )
        Qasm3Validator.validate_register_index(start_qid, qreg_size, qubit=is_qubit_reg)
        Qasm3Validator.validate_register_index(end_qid - 1, qreg_size, qubit=is_qubit_reg)
        return list(range(start_qid, end_qid, step))

    @staticmethod
    def transform_gate_qubits(
        gate_op: QuantumGate, qubit_map: dict[str, IndexedIdentifier]
    ) -> None:
        """Transform the qubits of a gate operation with a qubit map.

        Args:
            gate_op (QuantumGate): The gate operation to transform.
            qubit_map (dict[str, IndexedIdentifier]): The qubit map to use for transformation.

        Returns:
            None
        """
        for i, qubit in enumerate(gate_op.qubits):
            if isinstance(qubit, IndexedIdentifier):
                raise_qasm3_error(
                    f"Indexing '{qubit.name.name}' not supported in gate definition",
                    span=qubit.span,
                )

            gate_op.qubits[i] = qubit_map[qubit.name]

    @staticmethod
    def transform_gate_params(
        gate_op: QuantumGate, param_map: dict[str, Union[FloatLiteral, IntegerLiteral]]
    ) -> None:
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
    def get_branch_params(condition: Any) -> tuple[Optional[int], Optional[str]]:
        """
        Get the branch parameters from the branching condition

        Args:
            condition (Union[UnaryExpression, BinaryExpression, IndexExpression]): The condition
                                                                                   to analyze

        Returns:
            tuple[int, str]: The branch parameters
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

    @classmethod
    def transform_function_qubits(
        cls,
        q_op: Union[QuantumGate, QuantumBarrier, QuantumReset],
        formal_qreg_sizes: dict[str:int],
        qubit_map: dict[tuple:tuple],
    ) -> list:
        """Transform the qubits of a function call to the actual qubits.

        Args:
            visitor_obj: The visitor object.
            gate_op: The quantum operation to transform.
            formal_qreg_sizes (dict[str: int]): The formal qubit register sizes.
            qubit_map (dict[tuple: tuple]): The mapping of formal qubits to actual qubits.

        Returns:
            None
        """
        expanded_op_qubits = cls.visitor_obj._get_op_qubits(q_op, formal_qreg_sizes, qir_form=False)

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
