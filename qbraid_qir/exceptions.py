# Copyright (C) 2024 qBraid
#
# This file is part of qbraid-qir
#
# Qbraid-qir is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for qbraid-qir, as per Section 15 of the GPL v3.

"""
Module defining exceptions for errors raised by qBraid QIR.

"""


class QbraidQirError(Exception):
    """Base class for errors raised by qbraid-qir."""


class QirConversionError(QbraidQirError):
    """Class for errors raised when converting quantum program to QIR."""
