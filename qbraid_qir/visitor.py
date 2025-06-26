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
Abstract base class for QIR visitor.

"""

from abc import ABC
from typing import Optional

import pyqir


class QIRVisitor(ABC):
    """Abstract base class for QIR visitors."""

    def __init__(self) -> None:
        self._record_output: bool = True
        self._llvm_module: Optional[pyqir.Module] = None
        self._builder: Optional[pyqir.Builder] = None
        self._clbit_labels: dict[str, int] = {}
        self._global_creg_size_map: dict[str, int] = {}
