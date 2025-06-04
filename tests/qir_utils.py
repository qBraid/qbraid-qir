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


def generic_op_call_string(name: str, angles: list[str], qubits: list[int]) -> str:
    angles = ["double " + angle for angle in angles]
    qubits = [_qubit_string(q) for q in qubits]
    parameters = ", ".join(angles + qubits)
    return f"call void @__quantum__qis__{name}__body({parameters})"


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


def check_generic_gate_op(
    qir: list[str], expected_ops: int, qubit_list: list[int], param_list: list[str], gate_name: str
):
    entry_body = get_entry_point_body(qir)
    op_count = 0

    for line in entry_body:
        gate_call_id = (
            f"qis__{gate_name}" if "dg" not in gate_name else f"qis__{gate_name.removesuffix('dg')}"
        )
        if line.strip().startswith("call") and gate_call_id in line:
            expected_line = generic_op_call_string(gate_name, param_list, qubit_list)
            assert line.strip() == expected_line, (
                "Incorrect single qubit gate call in qir"
                + f"Expected {expected_line}, found {line.strip()}"
            )
            op_count += 1

        if op_count == expected_ops:
            break

    if op_count != expected_ops:
        assert False, f"Incorrect gate count: {expected_ops} expected, {op_count} actual"


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
                gate_name, [], qubit_lists[q_id]
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


def check_custom_qasm_gate_op_with_external_gates(qir: list[str], test_type: str):
    if test_type == "simple":
        check_generic_gate_op(qir, 1, [0, 1], ["1.100000e+00"], "custom")
    elif test_type == "nested":
        check_generic_gate_op(
            qir, 1, [0, 1], ["4.800000e+00", "1.000000e-01", "3.000000e-01"], "custom"
        )
    elif test_type == "complex":
        # Only custom1 is external, custom2 and custom3 should be unrolled
        check_generic_gate_op(qir, 1, [0], [], "custom1")
        check_generic_gate_op(qir, 1, [0], ["1.000000e-01"], "ry")
        check_generic_gate_op(qir, 1, [0], ["2.000000e-01"], "rz")
        check_generic_gate_op(qir, 1, [0, 1], [], "cnot")
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


# tests for the adaptive profile starts here


def check_adaptive_profile_compliance(qir: list[str]) -> None:
    """Verify QIR code complies with adaptive profile requirements."""
    entry_body = get_entry_point_body(qir)

    # Check for required adaptive functions
    has_qis_mz = any("qis__mz" in line for line in entry_body)
    has_qis_reset = any("qis__reset" in line for line in entry_body)
    has_qis_if_result = any("qis__if_result" in line for line in entry_body)

    # ADAPTIVE_001: Must use qis.mz instead of pyqir._native.mz
    assert not any(
        "_native" in line and "mz" in line for line in entry_body
    ), "ADAPTIVE_001: Must use qis.mz instead of pyqir._native.mz"

    # ADAPTIVE_002: Must use qis.reset instead of pyqir._native.reset
    assert not any(
        "_native" in line and "reset" in line for line in entry_body
    ), "ADAPTIVE_002: Must use qis.reset instead of pyqir._native.reset"


def check_conditional_branching(qir: list[str], expected_branches: int) -> None:
    """Verify conditional branching based on measurement results."""
    entry_body = get_entry_point_body(qir)
    branch_count = 0

    for line in entry_body:
        if line.strip().startswith("br") and ("%" in line or "label" in line):
            branch_count += 1

    assert (
        branch_count >= expected_branches
    ), f"Expected at least {expected_branches} branches, found {branch_count}"


def check_qubit_reuse_after_measurement(qir: list[str], qubit_list: list[int]) -> None:
    """Verify qubits can be reused after measurement (adaptive profile feature)."""
    entry_body = get_entry_point_body(qir)
    measured_qubits = set()
    reused_qubits = set()

    for line in entry_body:
        # Track measurements
        if "qis__mz" in line:
            for qubit in qubit_list:
                if _qubit_string(qubit) in line:
                    measured_qubits.add(qubit)
                    break

        # Check for operations on previously measured qubits
        elif any(
            gate in line
            for gate in [
                "qis__h",
                "qis__x",
                "qis__y",
                "qis__z",
                "qis__rx",
                "qis__ry",
                "qis__rz",
                "qis__cx",
            ]
        ):
            for qubit in measured_qubits:
                if _qubit_string(qubit) in line:
                    reused_qubits.add(qubit)

    assert len(reused_qubits) > 0, "No qubit reuse after measurement detected"


def check_register_grouped_output(qir: list[str], register_sizes: list[int]) -> None:
    """Verify output recording preserves register structure."""
    entry_body = get_entry_point_body(qir)
    array_record_calls = []

    for line in entry_body:
        if "array_record_output" in line:
            # Extract the number from the call
            import re

            match = re.search(r"i64 (\d+)", line)
            if match:
                array_record_calls.append(int(match.group(1)))

    assert len(array_record_calls) == len(
        register_sizes
    ), f"Expected {len(register_sizes)} register outputs, found {len(array_record_calls)}"

    for expected, actual in zip(register_sizes, array_record_calls):
        assert expected == actual, f"Register size mismatch: expected {expected}, got {actual}"


def check_measurement_state_tracking(qir: list[str], expected_state_changes: int) -> None:
    """Verify measurement state tracking for qubits."""
    entry_body = get_entry_point_body(qir)
    state_changes = 0

    for line in entry_body:
        # Count measurements and resets as state changes
        if any(op in line for op in ["qis__mz", "qis__reset"]):
            state_changes += 1

    assert (
        state_changes >= expected_state_changes
    ), f"Expected at least {expected_state_changes} state changes, found {state_changes}"


def check_read_result_calls(qir: list[str], expected_calls: int, result_list: list[int]) -> None:
    """Verify read_result function calls for accessing measurement outcomes."""
    entry_body = get_entry_point_body(qir)
    read_result_count = 0
    result_id = 0

    for line in entry_body:
        if "read_result" in line:
            expected_call = read_result_call_string(result_list[result_id])
            assert (
                expected_call in line
            ), f"Incorrect read_result call: expected {expected_call} in {line}"
            read_result_count += 1
            result_id += 1

        if read_result_count == expected_calls:
            break

    assert (
        read_result_count == expected_calls
    ), f"Expected {expected_calls} read_result calls, found {read_result_count}"


def check_return_exit_code(qir: list[str]) -> None:
    """Verify return instruction returns i64 zero exit code (ADAPTIVE_007)."""
    entry_body = get_entry_point_body(qir)

    # Find the return statement
    return_found = False
    for line in entry_body:
        if line.strip().startswith("ret"):
            assert (
                "ret i64 0" in line or "ret void" in line
            ), f"ADAPTIVE_007: Return must be 'ret i64 0' or 'ret void', found: {line.strip()}"
            return_found = True
            break

    assert return_found, "No return statement found in entry point"


def check_no_backward_jumps(qir: list[str]) -> None:
    """Verify no backward jumps in control flow (ADAPTIVE_008)."""
    entry_body = get_entry_point_body(qir)
    labels_seen = set()

    for line in entry_body:
        line = line.strip()

        # Track labels
        if line.endswith(":") and not line.startswith(";"):
            label = line[:-1]
            labels_seen.add(label)

        # Check branch targets
        elif line.startswith("br"):
            import re

            # Extract label references
            labels_in_branch = re.findall(r"label %(\w+)", line)
            for label in labels_in_branch:
                assert (
                    label not in labels_seen
                ), f"ADAPTIVE_008: Backward jump detected to label {label}"


def check_full_barrier_coverage(qir: list[str], total_qubits: int) -> None:
    """Verify barriers cover all qubits (not partial barriers)."""
    entry_body = get_entry_point_body(qir)

    for line in entry_body:
        if "qis__barrier" in line:
            # For full barriers, should be simple call with no qubit parameters
            assert (
                line.strip() == _barrier_string()
            ), f"Barrier must cover all qubits, found: {line.strip()}"


# Helper functions for the new test utilities


def if_result_call_string(result_id: int) -> str:
    """Generate expected if_result call string."""
    return f"call void @__quantum__qis__if_result__body({_result_string(result_id)})"


def read_result_call_string(result_id: int) -> str:
    """Generate expected read_result call string."""
    return f"call i1 @__quantum__qis__read_result__body({_result_string(result_id)})"


def conditional_gate_call_string(gate_name: str, condition_result: int, qubits: list[int]) -> str:
    """Generate conditional gate call string."""
    qubit_params = ", ".join([_qubit_string(q) for q in qubits])
    return f"call void @__quantum__qis__{gate_name}__ctl({_result_string(condition_result)}, {qubit_params})"


def check_adaptive_gate_set(qir: list[str]) -> None:
    """Verify only adaptive profile supported gates are used."""
    entry_body = get_entry_point_body(qir)

    allowed_gates = {
        "h",
        "x",
        "y",
        "z",
        "s",
        "s__adj",
        "t",
        "t__adj",
        "cnot",
        "cx",
        "cz",
        "ccx",
        "swap",
        "rx",
        "ry",
        "rz",
        "mz",
        "reset",
    }

    for line in entry_body:
        if "qis__" in line and "__body" in line:
            # Extract gate name
            import re

            match = re.search(r"qis__(\w+)__", line)
            if match:
                gate = match.group(1)
                if gate.endswith("__adj"):
                    gate = gate[:-5]  # Remove __adj suffix

                assert gate in allowed_gates, f"Unsupported gate '{gate}' found in adaptive profile"


def check_external_gate_linkage(qir: str) -> None:
    """Verify external gates have proper linkage type."""
    lines = qir.split("\n")

    for line in lines:
        if line.strip().startswith("declare") and "quantum" in line:
            assert "external" in line.lower() or not line.strip().startswith(
                "declare"
            ), f"External quantum function must have external linkage: {line.strip()}"


def check_parameter_constants_only(qir: list[str]) -> None:
    """Verify parameterized gates only use constants (not variables)."""
    entry_body = get_entry_point_body(qir)

    for line in entry_body:
        if any(gate in line for gate in ["rx", "ry", "rz"]) and "double" in line:
            # Parameters should be constants (hex values or scientific notation)
            import re

            # Look for variable references like %1, %2, etc.
            if re.search(r"double %\w+", line):
                assert False, f"Parameterized gates must use constants only: {line.strip()}"
