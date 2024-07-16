# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module defining exceptions for errors raised during Cirq conversions.

"""
from qbraid_qir.exceptions import QirConversionError


class CirqConversionError(QirConversionError):
    """Class for errors raised when converting Cirq program to QIR."""
