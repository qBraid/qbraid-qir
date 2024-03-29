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

   QbraidQirError
   QirConversionError

"""
from ._version import __version__
from .exceptions import QbraidQirError, QirConversionError
from .serialization import dumps

__all__ = [
    "__version__",
    "QbraidQirError",
    "QirConversionError",
    "dumps",
]

_lazy_mods = ["cirq", "qasm3", "runner"]


def __getattr__(name):
    if name in _lazy_mods:
        import importlib  # pylint: disable=import-outside-toplevel

        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(__all__ + _lazy_mods)
