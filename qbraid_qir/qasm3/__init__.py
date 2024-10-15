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
Module containing OpenQASM 3 QIR functionality.

.. currentmodule:: qbraid_qir.qasm3

Functions
-----------

.. autosummary::
   :toctree: ../stubs/

   qasm3_to_qir

Classes
---------

.. autosummary::
   :toctree: ../stubs/

   QasmQIRModule
   BasicQasmVisitor

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   Qasm3ConversionError

"""
from .convert import qasm3_to_qir
from .elements import QasmQIRModule
from .exceptions import Qasm3ConversionError
from .visitor import BasicQasmVisitor

__all__ = [
    "qasm3_to_qir",
    "QasmQIRModule",
    "Qasm3ConversionError",
    "BasicQasmVisitor",
]
