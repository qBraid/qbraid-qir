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
Module for containing QIR code utils functions used for unit tests.

"""

import struct
from typing import Union

from pyqir import (
    Context,
    Function,
    Module,
    is_entry_point,
    required_num_qubits,
    required_num_results,
)

from qbraid_qir.qasm3.maps import CONSTANTS_MAP


def double_to_hex(f):
    return hex(struct.unpack("<Q", struct.pack("<d", f))[0])


def assert_equal_qir(given_qir: str, filepath: str) -> None:
    """Function that compares generated qir to the qir in a file.

    Args:
        given_qir (str): Given qir string that should be compared with the file.
        filepath (str): Path to the file that should be compared with the given qir.
    """
    with open(filepath, encoding="utf-8") as file:
        file_data = file.read().strip()

    processed_given_qir = given_qir.strip()

    assert file_data == processed_given_qir


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
    if "dg" in name:  # stands for dagger representation
        name = name.removesuffix("dg") + "__adj"
        return f"call void @__quantum__qis__{name}({_qubit_string(qb)})"

    return f"call void @__quantum__qis__{name}__body({_qubit_string(qb)})"


def double_op_call_string(name: str, qb1: int, qb2: int) -> str:
    return f"call void @__quantum__qis__{name}__body({_qubit_string(qb1)}, {_qubit_string(qb2)})"


def rotation_call_string(name: str, theta: Union[float, str], qb: int) -> str:
    if isinstance(theta, str):
        # for hex matching
        theta = theta.replace("X", "x")
        return f"call void @__quantum__qis__{name}__body(double {theta}, {_qubit_string(qb)})"
    return f"call void @__quantum__qis__{name}__body(double {theta:#e}, {_qubit_string(qb)})"


def measure_call_string(name: str, res: str, qb: int) -> str:
    return f"call void @__quantum__qis__{name}__body({_qubit_string(qb)}, {_result_string(res)})"


def array_record_output_string(num_elements: int) -> str:
    return f"call void @__quantum__rt__array_record_output(i64 {num_elements}, i8* null)"


def result_record_output_string(res: str) -> str:
    return f"call void @__quantum__rt__result_record_output({_result_string(res)}, i8* null)"


def reset_call_string(qb: int) -> str:
    return f"call void @__quantum__qis__reset__body({_qubit_string(qb)})"


def generic_op_call_string(name: str, qbs: list[int]) -> str:
    args = ", ".join(_qubit_string(qb) for qb in qbs)
    return f"call void @__quantum__qis__{name}__body({args})"


def return_string() -> str:
    return "ret void"


def get_entry_point(mod: Module) -> Function:
    func = next(filter(is_entry_point, mod.functions))
    assert func is not None, "No main function found"
    return func


def get_entry_point_body(qir: list[str]) -> list[str]:
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


def check_attributes(qir: list[str], expected_qubits: int = 0, expected_results: int = 0) -> None:
    x = "\n".join(qir)
    mod = Module.from_ir(Context(), x)
    func = next(filter(is_entry_point, mod.functions))

    check_attributes_on_entrypoint(func, expected_qubits, expected_results)


def check_resets(qir: list[str], expected_resets: int, qubit_list: list[int]):
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
        assert False, f"Incorrect reset count: {expected_resets} expected, {reset_count} actual"


def check_barrier(qir: list[str], expected_barriers: int):
    entry_body = get_entry_point_body(qir)
    barrier_count = 0
    for line in entry_body:
        if line.strip().startswith("call") and "qis__barrier" in line:
            assert line.strip() == _barrier_string(), f"Incorrect barrier call in qir - {line}"
            barrier_count += 1
        if barrier_count == expected_barriers:
            break

    if barrier_count != expected_barriers:
        assert (
            False
        ), f"Incorrect barrier count: {expected_barriers} expected, {barrier_count} actual"


def check_measure_op(qir: list[str], expected_ops: int, qubit_list: list[int], bit_list: list[int]):
    entry_body = get_entry_point_body(qir)
    measure_count = 0
    q_id, b_id = 0, 0

    assert len(qubit_list) == len(bit_list), "Qubit list and bit list should be of same sizes"

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
        assert False, f"Incorrect barrier count: {expected_ops} expected, {measure_count} actual"


def check_single_qubit_gate_op(
    qir: list[str], expected_ops: int, qubit_list: list[int], gate_name: str
):
    entry_body = get_entry_point_body(qir)
    op_count = 0
    q_id = 0

    for line in entry_body:
        gate_call_id = (
            f"qis__{gate_name}" if "dg" not in gate_name else f"qis__{gate_name.removesuffix('dg')}"
        )
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
    qir: list[str], expected_ops: int, qubit_lists: list[int], gate_name: str
):
    entry_body = get_entry_point_body(qir)
    op_count = 0
    q_id = 0

    for line in entry_body:
        if gate_name.lower() == "cx":
            gate_name = "cnot"  # cnot is used in qir

        if line.strip().startswith("call") and f"qis__{gate_name}" in line:
            assert line.strip() == double_op_call_string(
                gate_name, qubit_lists[q_id][0], qubit_lists[q_id][1]
            ), f"Incorrect two qubit gate call in qir - {line}"
            op_count += 1
            q_id += 1

        if op_count == expected_ops:
            break

    if op_count != expected_ops:
        assert False, f"Incorrect two qubit gate count: {expected_ops} expected, {op_count} actual"


# pylint: disable-next=too-many-locals
def check_single_qubit_u3_op(
    entry_body: list[str], expected_ops: int, qubit_list: list[int], param_list: list[float]
):
    theta, phi, lam = param_list
    op_count = 0
    q_id = 0
    pi = CONSTANTS_MAP["pi"]
    u3_param_list = [lam, pi / 2, theta + pi, pi / 2, phi + pi]
    u3_gate_list = ["rz", "rx", "rz", "rx", "rz"]
    u3_gates_id = 0

    for line in entry_body:
        gate_name = u3_gate_list[u3_gates_id]
        if line.strip().startswith("call") and f"qis__{gate_name}" in line:
            try:
                rotation_call = rotation_call_string(
                    gate_name, u3_param_list[u3_gates_id], qubit_list[q_id]
                )
                assert (
                    line.strip() == rotation_call.strip()
                ), f"Incorrect rotation gate call in qir - {line}, expected {rotation_call}"
            except Exception:  # pylint: disable=broad-exception-caught
                rotation_call = rotation_call_string(
                    gate_name, double_to_hex(u3_param_list[u3_gates_id]).upper(), qubit_list[q_id]
                )
                assert (
                    line.strip() == rotation_call.strip()
                ), f"Incorrect rotation gate call in qir - {line}, expected {rotation_call}"

            u3_gates_id += 1
            if u3_gates_id == len(u3_gate_list):
                op_count += 1
                q_id += 1
                u3_gates_id = 0
            if op_count == expected_ops:
                break
    if op_count != expected_ops:
        raise AssertionError(
            "Incorrect rotation gate count for decomposed U3: "
            f"{expected_ops} expected, {op_count} actual."
        )


def check_single_qubit_rotation_op(
    qir: list[str],
    expected_ops: int,
    qubit_list: list[int],
    param_list: list[float],
    gate_name: str,
):
    entry_body = get_entry_point_body(qir)
    op_count = 0
    q_id = 0
    if gate_name == "u3":
        check_single_qubit_u3_op(entry_body, expected_ops, qubit_list, param_list)
        return
    if gate_name == "u2":
        param_list = [CONSTANTS_MAP["pi"] / 2, param_list[0], param_list[1]]
        check_single_qubit_u3_op(entry_body, expected_ops, qubit_list, param_list)
        return
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
        assert False, f"Incorrect rotation gate count: {expected_ops} expected, {op_count} actual"


def check_three_qubit_gate_op(
    qir: list[str], expected_ops: int, qubit_lists: list[int], gate_name: str
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


def _validate_simple_custom_op(entry_body: list[str]):
    custom_op_lines = [
        initialize_call_string(),
        single_op_call_string("h", 0),
        single_op_call_string("z", 1),
        rotation_call_string("rx", 1.1, 0),
        double_op_call_string("cnot", 0, 1),
        result_record_output_string(0),
        result_record_output_string(1),
        return_string(),
    ]

    assert len(entry_body) == len(custom_op_lines), "Incorrect number of lines in custom op"
    for i, body_line in enumerate(entry_body):
        assert body_line.strip() == custom_op_lines[i].strip(), "Incorrect custom op line"


def _validate_nested_custom_op(entry_body: list[str]):
    nested_op_lines = [
        initialize_call_string(),
        single_op_call_string("h", 1),
        rotation_call_string("rz", 4.8, 1),
        single_op_call_string("h", 0),
        double_op_call_string("cnot", 0, 1),
        rotation_call_string("rx", 4.8, 1),
        rotation_call_string("ry", 5, 1),
        result_record_output_string(0),
        result_record_output_string(1),
        return_string(),
    ]

    assert len(entry_body) == len(nested_op_lines), "Incorrect number of lines in nested op"
    for i, body_line in enumerate(entry_body):
        assert body_line.strip() == nested_op_lines[i].strip(), "Incorrect nested op line"


def _validate_complex_custom_op(entry_body: list[str]):
    complex_op_lines = [
        initialize_call_string(),
        single_op_call_string("h", 0),
        single_op_call_string("x", 0),
        rotation_call_string("rx", 0.5, 0),
        rotation_call_string("ry", 0.1, 0),
        rotation_call_string("rz", 0.2, 0),
        double_op_call_string("cnot", 0, 1),
        result_record_output_string(0),
        result_record_output_string(1),
        return_string(),
    ]

    assert len(entry_body) == len(complex_op_lines), "Incorrect number of lines in complex op"
    for i, body_line in enumerate(entry_body):
        assert body_line.strip() == complex_op_lines[i].strip(), "Incorrect complex op line"


def check_custom_qasm_gate_op(qir: list[str], test_type: str):
    entry_body = get_entry_point_body(qir)
    if test_type == "simple":
        _validate_simple_custom_op(entry_body)
    elif test_type == "nested":
        _validate_nested_custom_op(entry_body)
    elif test_type == "complex":
        _validate_complex_custom_op(entry_body)
    else:
        assert False, f"Unknown test type {test_type} for custom ops"


def check_expressions(
    qir: list[str], expected_ops: int, gates: list[str], expression_values, qubits: list[int]
):
    entry_body = get_entry_point_body(qir)
    op_count = 0
    q_id = 0

    for line in entry_body:
        if line.strip().startswith("call") and "qis__" in line:
            assert line.strip() == rotation_call_string(
                gates[q_id], expression_values[q_id], qubits[q_id]
            ), f"Incorrect rotation gate call in qir - {line}"
            op_count += 1
            q_id += 1

        if op_count == expected_ops:
            break

    if op_count != expected_ops:
        assert False, f"Incorrect rotation gate count: {expected_ops} expected, {op_count} actual"


def check_simple_if(
    qir: list[str],  # pylint: disable=unused-argument
):
    pass


def check_complex_if(
    qir: list[str],  # pylint: disable=unused-argument
):
    pass
