# Copyright 2026 qBraid
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

# pylint: disable=line-too-long
# Portions of this module are adapted from microsoft/qiskit-qir
# (https://github.com/microsoft/qiskit-qir), with modifications by qBraid.
# The original MIT license notice is reproduced in NOTICE.md.
# pylint: enable=line-too-long

"""
Module containing Qiskit QIR functionality.

.. currentmodule:: qbraid_qir.qiskit

Functions
-----------

.. autosummary::
   :toctree: ../stubs/

   qiskit_to_qir


Classes
---------

.. autosummary::
   :toctree: ../stubs/

   QiskitModule
   BasicQiskitVisitor

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   QiskitConversionError

"""

from .convert import qiskit_to_qir
from .elements import QiskitModule
from .exceptions import QiskitConversionError
from .visitor import BasicQiskitVisitor

__all__ = ["qiskit_to_qir", "QiskitModule", "QiskitConversionError", "BasicQiskitVisitor"]
