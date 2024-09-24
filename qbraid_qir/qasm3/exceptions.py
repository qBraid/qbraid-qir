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
from enum import Enum
from typing import Optional, Type

from openqasm3.ast import Span

from qbraid_qir.exceptions import QirConversionError

logging.basicConfig(level=logging.WARNING, format="%(levelname)s - %(message)s")


class WarnType(Enum):
    """Enum for different qasm3 semantic warnings."""

    UNUSED_VAR = "unused"
    IMPLICIT_CAST = "implicit_cast"
    UNUSED_FUNCTION = "unused_function"
    UNUSED_GATE = "unused_gate"


class Qasm3ConversionError(QirConversionError):
    """Class for errors raised when converting an OpenQASM 3 program to QIR."""


def raise_qasm3_error(
    message: Optional[str] = None,
    err_type: Type[Exception] = Qasm3ConversionError,
    span: Optional[Span] = None,
    raised_from: Optional[Exception] = None,
) -> None:
    """Raises a QASM3 conversion error with optional chaining from another exception.

    Args:
        message: The error message. If not provided, a default message will be used.
        err_type: The type of error to raise.
        span: The span (location) in the QASM file where the error occurred.
        raised_from: Optional exception from which this error was raised (chaining).

    Raises:
        err_type: The error type initialized with the specified message and chained exception.
    """
    if span:
        logging.error(
            "Error at line %s, column %s in QASM file", span.start_line, span.start_column
        )

    if raised_from:
        raise err_type(message) from raised_from
    raise err_type(message)


def emit_qasm3_warning(
    warning_type: WarnType,
    message: Optional[str] = None,
    span: Optional[Span] = None,
):
    """Emits a QASM3 conversion warning.

    Args:
        warning_type: The type of warning.
        message: The warning message.
        span: The span (location) in the QASM file where the warning occurred.

    Returns:
        None
    """
    err_message = "No message provided."
    if span:
        err_message = (
            f"Warning at line {span.start_line}, column {span.start_column} in QASM file. "
        )

    if message:
        err_message = message if not span else f"{err_message} {message}"

    logging.warning(f"{warning_type} warning emitted: {err_message}")
