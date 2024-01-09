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
This top level module contains the main qBraid QIR functionality.

.. currentmodule:: qbraid_qir

Functions
-----------

.. autosummary::
   :toctree: ../stubs/

   dumps

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   QirConversionError

"""
from ._version import __version__
from .cirq import cirq_to_qir
from .exceptions import QirConversionError
from .serialization import dumps
