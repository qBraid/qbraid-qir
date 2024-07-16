# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module containing AutoQASM to qBraid QIR conversion functions

"""
import re
from typing import TYPE_CHECKING

from qbraid.passes.qasm3.compat import add_stdgates_include, insert_gate_def

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
    qasm = add_stdgates_include(qasm)
    qasm = insert_gate_def(qasm, "iswap")
    qasm = insert_gate_def(qasm, "sxdg")

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
