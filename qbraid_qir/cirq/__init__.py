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
Module containing Cirq QIR functionality.

.. currentmodule:: qbraid_qir.cirq

Functions
-----------

.. autosummary::
   :toctree: ../stubs/

   cirq_to_qir


Classes
---------

.. autosummary::
   :toctree: ../stubs/

   CirqModule
   BasicCirqVisitor

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   CirqConversionError

"""
from .convert import cirq_to_qir
from .elements import CirqModule
from .exceptions import CirqConversionError
from .visitor import BasicCirqVisitor
