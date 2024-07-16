# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module defining exceptions for errors raised during AutoQASM conversions.

"""
from qbraid_qir.exceptions import QirConversionError


class AutoQasmConversionError(QirConversionError):
    """Class for errors raised when converting AutoQASM program to QIR."""
