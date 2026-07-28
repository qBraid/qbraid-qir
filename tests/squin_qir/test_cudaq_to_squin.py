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

"""Unit tests for CUDAQ to Squin conversion functions."""

import pytest

from qbraid_qir._pyqir_compat import pyqir_uses_opaque_pointers

cudaq = pytest.importorskip("cudaq")

# cudaq 0.15+ emits opaque-pointer QIR (QIR 2.0) with no option to emit typed pointers,
# and pyqir 0.11.x (LLVM 14) cannot parse opaque pointers -- so pyqir.Module.from_ir
# rejects cudaq's output on the typed-pointer leg. This is a hard capability requirement,
# not a workaround: the cudaq->squin path only exists on pyqir 0.12+. The squin loader
# itself is still exercised on the typed-pointer leg by test_qir_to_squin.py, which loads
# a committed typed-pointer fixture (parseable by both pyqir versions).
pytestmark = pytest.mark.skipif(
    not pyqir_uses_opaque_pointers(),
    reason="cudaq emits opaque-pointer QIR that requires pyqir 0.12+ to parse",
)

# Imports after importorskip so optional dependency is not required at import time.
from qbraid_qir.squin import load  # pylint: disable=wrong-import-position

from .test_qir_to_squin import _compare_output  # pylint: disable=wrong-import-position


def test_bell_state():

    expected_output = """func.func @main() -> !py.NoneType {
  ^0(%main_self):
  │ %0 = func.invoke new() : !py.Qubit maybe_pure=False
  │ %1 = func.invoke new() : !py.Qubit maybe_pure=False
  │ %2 = func.invoke h(%0) : !py.NoneType maybe_pure=False
  │ %3 = func.invoke cx(%0, %1) : !py.NoneType maybe_pure=False
  │ %4 = func.const.none() : !py.NoneType
  │      func.return %4
} // func.func main
"""

    @cudaq.kernel
    def bell():
        q = cudaq.qvector(2)
        h(q[0])  # pylint: disable=undefined-variable
        cx(q[0], q[1])  # pylint: disable=undefined-variable

    qir_str = cudaq.translate(bell, format="qir-base")
    squin_kernel = load(qir_str)
    _compare_output(squin_kernel, expected_output)


def test_ghz_state():

    expected_output = """func.func @main() -> !py.NoneType {
  ^0(%main_self):
  │ %0 = func.invoke new() : !py.Qubit maybe_pure=False
  │ %1 = func.invoke new() : !py.Qubit maybe_pure=False
  │ %2 = func.invoke new() : !py.Qubit maybe_pure=False
  │ %3 = func.invoke h(%0) : !py.NoneType maybe_pure=False
  │ %4 = func.invoke cx(%0, %1) : !py.NoneType maybe_pure=False
  │ %5 = func.invoke cx(%1, %2) : !py.NoneType maybe_pure=False
  │ %6 = func.const.none() : !py.NoneType
  │      func.return %6
} // func.func main
"""

    @cudaq.kernel
    def ghz():
        q = cudaq.qvector(3)
        h(q[0])  # pylint: disable=undefined-variable
        for j in range(2):
            cx(q[j], q[j + 1])  # pylint: disable=undefined-variable

    qir_str = cudaq.translate(ghz, format="qir-base")
    squin_kernel = load(qir_str)
    _compare_output(squin_kernel, expected_output)
