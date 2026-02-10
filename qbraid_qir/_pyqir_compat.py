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
Compatibility layer for different pyqir versions.

PyQIR 0.12+ uses opaque pointers (QIR 2.0) and removed qubit_id/result_id/qubit_type/result_type,
replacing them with ptr_id and PointerType. This module provides a single API that works
with both pyqir 0.10.x (typed pointers) and 0.12+ (opaque pointers).
"""

from typing import Any, Optional

import pyqir


def _uses_opaque_pointers() -> bool:
    """True if this pyqir build uses opaque pointers (0.12+)."""
    return getattr(pyqir, "ptr_id", None) is not None


def pointer_id(value: Any) -> Optional[int]:
    """
    Extract a static pointer id from a value (qubit or result).

    Uses ptr_id on pyqir 0.12+, or qubit_id/result_id on 0.10.x (for qubit/result constants).
    """
    if _uses_opaque_pointers():
        return pyqir.ptr_id(value)
    # 0.10.x: qubit_id for qubit constants, result_id for result constants
    out = pyqir.qubit_id(value)
    if out is not None:
        return out
    return pyqir.result_id(value)


def qubit_pointer_type(context: Any) -> Any:
    """
    Return the LLVM type for a qubit pointer in this pyqir version.

    Uses PointerType(Type.void(context)) on 0.12+, or qubit_type(context) on 0.10.x.
    """
    if _uses_opaque_pointers():
        return pyqir.PointerType(pyqir.Type.void(context))
    return pyqir.qubit_type(context)


def pyqir_uses_opaque_pointers() -> bool:
    """
    Return True if the installed pyqir uses opaque pointers (QIR 2.0 / pyqir 0.12+).

    Useful in tests to choose expected IR format (ptr vs %Qubit* / i8*).
    """
    return _uses_opaque_pointers()
