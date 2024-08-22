# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining exceptions for errors raised during QASM3 conversions.

"""
import logging
from typing import Optional

from openqasm3.ast import Span

from qbraid_qir.exceptions import QirConversionError


class Qasm3ConversionError(QirConversionError):
    """Class for errors raised when converting an OpenQASM 3 program to QIR."""


def raise_qasm3_error(
    message: str, err_type: Exception = Qasm3ConversionError, span: Optional[Span] = None
):
    """Raises a QASM3 conversion error.

    Args:
        message: The error message.
        err_type: The error type.
        span: The span of the error.

    Raises:
        err_type: The error type with the specified message
    """
    if span:
        logging.error(
            "Error at line %s, column %s in QASM file", span.start_line, span.start_column
        )

    raise err_type(message)
