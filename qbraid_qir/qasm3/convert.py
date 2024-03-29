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
Module containing OpenQASM to QIR conversion functions

"""
from typing import Optional, Union

import openqasm3
from pyqir import Context, Module, qir_module

from .elements import Qasm3Module, generate_module_id
from .exceptions import Qasm3ConversionError
from .visitor import BasicQasmVisitor


def qasm3_to_qir(
    program: Union[openqasm3.ast.Program, str], name: Optional[str] = None, **kwargs
) -> Module:
    """Converts an OpenQASM 3 program to a PyQIR module.

    Args:
        program (openqasm3.ast.Program or str): The OpenQASM 3 program to convert.
        name (str, optional): Identifier for created QIR module. Auto-generated if not provided.

    Keyword Args:
        initialize_runtime (bool): Whether to perform quantum runtime environment initialization,
                                   default `True`.
        record_output (bool): Whether to record output calls for registers, default `True`

    Returns:
        The QIR ``pyqir.Module`` representation of the input OpenQASM 3 program.

    Raises:
        TypeError: If the input is not a valid OpenQASM 3 program.
        Qasm3ConversionError: If the conversion fails.
    """
    if isinstance(program, str):
        program = openqasm3.parse(program)

    elif not isinstance(program, openqasm3.ast.Program):
        raise TypeError("Input quantum program must be of type openqasm3.ast.Program or str.")

    if name is None:
        name = generate_module_id()

    llvm_module = qir_module(Context(), name)
    module = Qasm3Module.from_program(program, llvm_module)

    visitor = BasicQasmVisitor(**kwargs)
    module.accept(visitor)

    err = llvm_module.verify()
    if err is not None:
        raise Qasm3ConversionError(err)
    return llvm_module
