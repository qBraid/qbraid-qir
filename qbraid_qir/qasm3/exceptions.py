# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module defining exceptions for errors raised during QASM3 conversions.

"""
from qbraid_qir.exceptions import QirConversionError


class Qasm3ConversionError(QirConversionError):
    """Class for errors raised when converting an OpenQASM 3 program to QIR."""
