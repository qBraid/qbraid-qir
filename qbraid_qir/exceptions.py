# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module defining exceptions for errors raised by qBraid QIR.

"""


class QbraidQirError(Exception):
    """Base class for errors raised by qbraid-qir."""


class QirConversionError(QbraidQirError):
    """Class for errors raised when converting quantum program to QIR."""