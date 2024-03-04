# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.
"""
Module containing unit tests Cirq to QIR utility/helper functions

"""
# isort: skip_file

from typing import List

from pyqir import (
    Context,
    Function,
    Module,
    is_entry_point,
    required_num_qubits,
    required_num_results,
)


def _qubit_string(qubit: int) -> str:
    if qubit == 0:
        return "%Qubit* null"
    return f"%Qubit* inttoptr (i64 {qubit} to %Qubit*)"


def _barrier_string() -> str:
    return "call void @__quantum__qis__barrier__body()"


def _result_string(res: int) -> str:
    if res == 0:
        return "%Result* null"
    return f"%Result* inttoptr (i64 {res} to %Result*)"


def initialize_call_string() -> str:
    return "call void @__quantum__rt__initialize(i8* null)"


def single_op_call_string(name: str, qb: int) -> str:
    if "dg" in name: #stands for dagger representation
        name = name.removesuffix("dg") + "__adj"
        return f"call void @__quantum__qis__{name}({_qubit_string(qb)})"
    
    return f"call void @__quantum__qis__{name}__body({_qubit_string(qb)})"


def double_op_call_string(name: str, qb1: int, qb2: int) -> str:
    return f"call void @__quantum__qis__{name}__body({_qubit_string(qb1)}, {_qubit_string(qb2)})"


def rotation_call_string(name: str, theta: float, qb: int) -> str:
    return f"call void @__quantum__qis__{name}__body(double {theta:#e}, {_qubit_string(qb)})"


def measure_call_string(name: str, res: str, qb: int) -> str:
    return f"call void @__quantum__qis__{name}__body({_qubit_string(qb)}, {_result_string(res)})"


def array_record_output_string(num_elements: int) -> str:
    return (
        f"call void @__quantum__rt__array_record_output(i64 {num_elements}, i8* null)"
    )


def result_record_output_string(res: str) -> str:
    return f"call void @__quantum__rt__result_record_output({_result_string(res)}, i8* null)"


def reset_call_string(qb: int) -> str:
    return f"call void @__quantum__qis__reset__body({_qubit_string(qb)})"


def generic_op_call_string(name: str, qbs: List[int]) -> str:
    args = ", ".join(_qubit_string(qb) for qb in qbs)
    return f"call void @__quantum__qis__{name}__body({args})"


def return_string() -> str:
    return "ret void"


def get_entry_point(mod: Module) -> Function:
    func = next(filter(is_entry_point, mod.functions))
    assert func is not None, "No main function found"
    return func


def get_entry_point_body(qir: List[str]) -> List[str]:
    joined = "\n".join(qir)
    mod = Module.from_ir(Context(), joined)
    func = next(filter(is_entry_point, mod.functions))
    assert func is not None, "No main function found"
    lines = str(func).splitlines()[2:-1]
    return list(map(lambda line: line.strip(), lines))


def check_attributes_on_entrypoint(
    func: Function, expected_qubits: int = 0, expected_results: int = 0
) -> None:
    actual_qubits = -1
    actual_results = -1

    actual_qubits = required_num_qubits(func)
    actual_results = required_num_results(func)
    assert (
        expected_qubits == actual_qubits
    ), f"Incorrect qubit count: {expected_qubits} expected, {actual_qubits} actual"

    assert (
        expected_results == actual_results
    ), f"Incorrect result count: {expected_results} expected, {actual_results} actual"


def check_attributes(
    qir: List[str], expected_qubits: int = 0, expected_results: int = 0
) -> None:
    x = "\n".join(qir)
    mod = Module.from_ir(Context(), x)
    func = next(filter(is_entry_point, mod.functions))

    check_attributes_on_entrypoint(func, expected_qubits, expected_results)


def check_resets(qir: List[str], expected_resets: int, qubit_list: List[int]):
    entry_body = get_entry_point_body(qir)
    reset_count = 0
    for line in entry_body:
        if line.strip().startswith("call") and "qis__reset" in line:
            expected_reset = reset_call_string(qubit_list[reset_count])
            assert (
                line.strip() == expected_reset.strip()
            ), f"Incorrect reset call: {expected_reset} expected, {line} actual"
            reset_count += 1
        if reset_count == expected_resets:
            break

    if reset_count != expected_resets:
        assert (
            False
        ), f"Incorrect reset count: {expected_resets} expected, {reset_count} actual"


def check_barrier(qir: List[str], expected_barriers: int):
    entry_body = get_entry_point_body(qir)
    barrier_count = 0
    for line in entry_body:
        if line.strip().startswith("call") and "qis__barrier" in line:
            assert (
                line.strip() == _barrier_string()
            ), f"Incorrect barrier call in qir - {line}"
            barrier_count += 1
        if barrier_count == expected_barriers:
            break

    if barrier_count != expected_barriers:
        assert (
            False
        ), f"Incorrect barrier count: {expected_barriers} expected, {barrier_count} actual"


def check_measure_op(
    qir: List[str], expected_ops: int, qubit_list: List[int], bit_list: List[int]
):
    entry_body = get_entry_point_body(qir)
    measure_count = 0
    q_id, b_id = 0, 0

    assert len(qubit_list) == len(
        bit_list
    ), "Qubit list and bit list should be of same sizes"

    for line in entry_body:
        if line.strip().startswith("call") and "qis__mz" in line:
            assert line.strip() == measure_call_string(
                "mz", bit_list[b_id], qubit_list[q_id]
            ), f"Incorrect measure call in qir - {line}"
            measure_count += 1
            q_id += 1
            b_id += 1

        if measure_count == expected_ops:
            break

    if measure_count != expected_ops:
        assert (
            False
        ), f"Incorrect barrier count: {expected_ops} expected, {measure_count} actual"

def check_single_qubit_gate_op(
    qir: List[str], expected_ops: int, qubit_list: List[int], gate_name: str
):
    entry_body = get_entry_point_body(qir)
    op_count = 0
    q_id = 0

    for line in entry_body:
        gate_call_id = f"qis__{gate_name}" if "dg" not in gate_name else f"qis__{gate_name.removesuffix('dg')}"
        print(gate_call_id)
        if line.strip().startswith("call") and gate_call_id in line:
            assert line.strip() == single_op_call_string(
                gate_name, qubit_list[q_id]
            ), f"Incorrect single qubit gate call in qir - {line}"
            op_count += 1
            q_id += 1

        if op_count == expected_ops:
            break

    if op_count != expected_ops:
        assert (
            False
        ), f"Incorrect single qubit gate count: {expected_ops} expected, {op_count} actual"


def check_two_qubit_gate_op(
        qir: List[str], expected_ops: int, qubit_lists: List[int], gate_name: str
):
    entry_body = get_entry_point_body(qir)
    op_count = 0
    q_id = 0

    for line in entry_body:

        if gate_name.lower() == "cx":
            gate_name = "cnot" # cnot is used in qir

        if line.strip().startswith("call") and f"qis__{gate_name}" in line:
            assert line.strip() == double_op_call_string(
                gate_name, qubit_lists[q_id][0], qubit_lists[q_id][1]
            ), f"Incorrect two qubit gate call in qir - {line}"
            op_count += 1
            q_id += 1

        if op_count == expected_ops:
            break
    
    if op_count != expected_ops:
        assert (
            False
        ), f"Incorrect two qubit gate count: {expected_ops} expected, {op_count} actual"


def check_single_qubit_rotation_op(
    qir: List[str], expected_ops: int, qubit_list: List[int], param_list: List[float], gate_name: str
):
    entry_body = get_entry_point_body(qir)
    op_count = 0
    q_id = 0

    for line in entry_body:
        if line.strip().startswith("call") and f"qis__{gate_name}" in line:
            assert line.strip() == rotation_call_string(
                gate_name, param_list[q_id], qubit_list[q_id]
            ), f"Incorrect rotation gate call in qir - {line}"
            op_count += 1
            q_id += 1

        if op_count == expected_ops:
            break
    
    if op_count != expected_ops:
        assert (
            False
        ), f"Incorrect rotation gate count: {expected_ops} expected, {op_count} actual"

def check_three_qubit_gate_op(
    qir: List[str], expected_ops: int, qubit_lists: List[int], gate_name: str
):
    entry_body = get_entry_point_body(qir)
    op_count = 0
    q_id = 0

    for line in entry_body:
        if line.strip().startswith("call") and f"qis__{gate_name}" in line:
            assert line.strip() == generic_op_call_string(
                gate_name, qubit_lists[q_id]
            ), f"Incorrect three qubit gate call in qir - {line}"
            op_count += 1
            q_id += 1

        if op_count == expected_ops:
            break
    
    if op_count != expected_ops:
        assert (
            False
        ), f"Incorrect three qubit gate count: {expected_ops} expected, {op_count} actual"