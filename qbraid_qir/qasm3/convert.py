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
Module containing OpenQASM to QIR conversion functions

"""
from typing import Optional, Union

import openqasm3
import pyqasm
from pyqir import Context, Module, qir_module

from .elements import QasmQIRModule, generate_module_id
from .exceptions import Qasm3ConversionError
from .visitor import QasmQIRVisitor
from .adaptive_support import QasmQIRAdaptiveVisitor


def qasm3_to_qir(
    program: Union[openqasm3.ast.Program, str],
    name: Optional[str] = None,
    external_gates: Optional[list[str]] = None,
    profile: str = "base",
    **kwargs,
) -> Module:
    """Converts an OpenQASM 3 program to a PyQIR module.

    Args:
        program (openqasm3.ast.Program or str): The OpenQASM 3 program to convert.
        name (str, optional): Identifier for created QIR module. Auto-generated if not provided.
        external_gates (list[str], optional): A list of custom gate names that are not natively
            recognized by pyqasm but should be treated as valid during program unrolling.

    Keyword Args:
        initialize_runtime (bool): Whether to perform quantum runtime environment initialization,
            defaults to `True`.
        record_output (bool): Whether to record output calls for registers, defaults to `True`.

    Returns:
        The QIR ``pyqir.Module`` representation of the input OpenQASM 3 program.

    Raises:
        TypeError: If the input is not a valid OpenQASM 3 program.
        Qasm3ConversionError: If the conversion fails.
    """
    if isinstance(program, openqasm3.ast.Program):
        program = openqasm3.dumps(program)

    elif not isinstance(program, str):
        raise TypeError("Input quantum program must be of type openqasm3.ast.Program or str.")

    qasm3_module = pyqasm.load(program)
    qasm3_module.unroll()
    if name is None:
        name = generate_module_id()
    llvm_module = qir_module(Context(), name)

    final_module = QasmQIRModule(name, qasm3_module, llvm_module)

    profile = profile.lower()
    if profile == "adaptive":
        visitor = QasmQIRAdaptiveVisitor(external_gates=external_gates, **kwargs)
    elif profile == "base":
        visitor = QasmQIRVisitor(external_gates=external_gates, **kwargs)
    else:
        raise ValueError(f"Invalid profile: {profile}")

    final_module.accept(visitor)

    err = llvm_module.verify()
    if err is not None:
        raise Qasm3ConversionError(err)
    return llvm_module
