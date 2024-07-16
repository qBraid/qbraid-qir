# Copyright (c) 2024, qBraid Development Team
# All rights reserved.

"""
Module containing AutoQASM QIR functionality.

.. currentmodule:: qbraid_qir.autoqasm

Functions
-----------

.. autosummary::
   :toctree: ../stubs/

   autoqasm_to_qir

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   AutoQasmConversionError

"""
from .convert import autoqasm_to_qir
from .exceptions import AutoQasmConversionError