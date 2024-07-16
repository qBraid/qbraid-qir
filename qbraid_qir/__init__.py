# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

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

_lazy_mods = ["cirq", "qasm3", "autoqasm"]


def __getattr__(name):
    if name in _lazy_mods:
        import importlib  # pylint: disable=import-outside-toplevel

        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(__all__ + _lazy_mods)
