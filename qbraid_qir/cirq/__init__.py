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

__all__ = ["cirq_to_qir", "CirqModule", "CirqConversionError", "BasicCirqVisitor"]
