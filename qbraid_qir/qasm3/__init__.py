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
   QasmQIRVisitor

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   Qasm3ConversionError

"""

from .convert import qasm3_to_qir
from .elements import QasmQIRModule
from .exceptions import Qasm3ConversionError
from .visitor import QasmQIRVisitor

__all__ = [
    "qasm3_to_qir",
    "QasmQIRModule",
    "Qasm3ConversionError",
    "QasmQIRVisitor",
]
