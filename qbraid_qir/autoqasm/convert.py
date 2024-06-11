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
Module containing AutoQASM to qBraid QIR conversion functions

"""
import re
from typing import TYPE_CHECKING

import qbraid.transforms.qasm3.compat as qasm3_compat

from qbraid_qir.qasm3 import qasm3_to_qir

if TYPE_CHECKING:
    from autoqasm.program import MainProgram
    from pyqir import Module


def _process_qasm(qasm: str) -> str:
    """
    Convert OpenQASM 3 string to a format that
    will be accepted by the qbraid-qir converter.

    Args:
        qasm (str): The input QASM string to process.

    Returns:
        The processed QASM string.

    """
    # Regular expression to remove initialization to zeros
    pattern = r'(bit\[\d+\] +__bit_\d+__)\s+=\s+"[0]+"(;)'

    # Transform each line, removing zero initializations
    transformed_lines = [re.sub(pattern, r"\1\2", line) for line in qasm.split("\n")]

    # Rejoin the transformed lines back into a single string
    qasm = "\n".join(transformed_lines)

    # Replace specific keywords with comments in a single step to avoid multiple replacements
    qasm = re.sub(r"^(output|return_value =)", r"// \1", qasm, flags=re.MULTILINE)

    # Insert and replace various gate definitions for compatibility
    qasm = qasm3_compat._add_stdgates_include(qasm)
    qasm = qasm3_compat._insert_gate_defs(qasm)

    return qasm


def autoqasm_to_qir(program: "MainProgram", **kwargs) -> "Module":
    """
    Converts an AutoQASM program to a PyQIR module.

    Args:
        program (cirq.Circuit): The Cirq circuit to convert.

    Returns:
        The QIR ``pyqir.Module`` representation of the input AutoQASM program.

    """
    qasm = program.build().to_ir()

    processed_qasm = _process_qasm(qasm)

    return qasm3_to_qir(processed_qasm, **kwargs)
