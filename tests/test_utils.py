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
from typing import List

from pyqir import Context, Function, Module, is_entry_point


def _qubit_string(qubit: int) -> str:
    if qubit == 0:
        return "%Qubit* null"
    return f"%Qubit* inttoptr (i64 {qubit} to %Qubit*)"


def initialize_call_string() -> str:
    return "call void @__quantum__rt__initialize(i8* null)"


def single_op_call_string(name: str, qb: int) -> str:
    return f"call void @__quantum__qis__{name}__body({_qubit_string(qb)})"


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


def return_string() -> str:
    return "ret void"
