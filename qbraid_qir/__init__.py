# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
import importlib
from typing import TYPE_CHECKING

from ._version import __version__
from .exceptions import QbraidQirError, QirConversionError
from .serialization import dumps

__all__ = [
    "__version__",
    "QbraidQirError",
    "QirConversionError",
    "dumps",
    "qasm3_to_qir",
    "cirq_to_qir",
]

_lazy = {"cirq": "cirq_to_qir", "qasm3": "qasm3_to_qir"}

if TYPE_CHECKING:
    from .cirq import cirq_to_qir
    from .qasm3 import qasm3_to_qir


def __getattr__(name):
    for mod_name, objects in _lazy.items():
        if name == mod_name:
            module = importlib.import_module(f".{mod_name}", __name__)
            globals()[mod_name] = module
            return module

        if name in objects:
            module = importlib.import_module(f".{mod_name}", __name__)
            obj = getattr(module, name)
            globals()[name] = obj
            return obj

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(
        __all__ + list(_lazy.keys()) + [item for sublist in _lazy.values() for item in sublist]
    )
