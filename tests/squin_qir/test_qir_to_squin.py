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

"""Unit tests for QIR to Squin conversion functions."""
import os
import re

from kirin import ir

from qbraid_qir.qasm3.convert import qasm3_to_qir
from qbraid_qir.squin import load

_RESOURCES = os.path.join(os.path.dirname(__file__), "resources")


def _compare_output(kernel: ir.Method, expected: list[str]) -> None:
    """Compare the output of the kernel to the expected output."""
    actual = kernel.print_str()
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    plain_output = ansi_escape.sub("", actual)
    assert (
        plain_output == expected
    ), f"Output mismatch.\nExpected: {expected}\nActual: {plain_output}"


def test_all_supported_gates():
    """Test conversion of all supported gates from QIR to Squin."""
    qasm3 = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[2] qb;
    h qb;
    x qb[0];
    y qb[1];
    z qb[0];
    s qb[1];
    t qb[0];
    sdg qb[1];
    tdg qb[0];
    rx(pi) qb[1];
    ry(pi/2) qb[0];
    rz(pi/4) qb[1];
    cx qb[0], qb[1];
    cz qb[0], qb[1];
    """

    expected_output = """func.func @test_clifford() -> !py.NoneType {
  ^0(%test_clifford_self):
  │  %0 = func.invoke new() : !py.Qubit maybe_pure=False
  │  %1 = func.invoke new() : !py.Qubit maybe_pure=False
  │  %2 = func.invoke h(%0) : !py.NoneType maybe_pure=False
  │  %3 = func.invoke h(%1) : !py.NoneType maybe_pure=False
  │  %4 = func.invoke x(%0) : !py.NoneType maybe_pure=False
  │  %5 = func.invoke y(%1) : !py.NoneType maybe_pure=False
  │  %6 = func.invoke z(%0) : !py.NoneType maybe_pure=False
  │  %7 = func.invoke s(%1) : !py.NoneType maybe_pure=False
  │  %8 = func.invoke t(%0) : !py.NoneType maybe_pure=False
  │  %9 = func.invoke s_adj(%1) : !py.NoneType maybe_pure=False
  │ %10 = func.invoke t_adj(%0) : !py.NoneType maybe_pure=False
  │ %11 = py.constant.constant 3.141592653589793 : !py.float
  │ %12 = func.invoke rx(%11, %1) : !py.NoneType maybe_pure=False
  │ %13 = py.constant.constant 1.5707963267948966 : !py.float
  │ %14 = func.invoke ry(%13, %0) : !py.NoneType maybe_pure=False
  │ %15 = py.constant.constant 0.7853981633974483 : !py.float
  │ %16 = func.invoke rz(%15, %1) : !py.NoneType maybe_pure=False
  │ %17 = func.invoke cx(%0, %1) : !py.NoneType maybe_pure=False
  │ %18 = func.invoke cz(%0, %1) : !py.NoneType maybe_pure=False
  │ %19 = func.const.none() : !py.NoneType
  │       func.return %19
} // func.func test_clifford
"""

    kernel = load(str(qasm3_to_qir(qasm3)), kernel_name="test_clifford")
    _compare_output(kernel, expected_output)


def test_bell_state():
    """Test conversion of Bell state from QIR to Squin.

    This test demonstrates using the 'register_as_argument' option in the load() function,
    which causes the kernel to accept the qubit register as an argument rather than
    allocating new qubits inside the kernel. The generated Squin kernel will have the register
    argument (%q), and the qubits will be accessed from this register.
    """
    expected_output = """func.func @main() -> !py.NoneType {
  ^0(%main_self, %q):
  │ %0 = py.constant.constant 0 : !py.int
  │ %1 = py.indexing.getitem(%q : !py.IList[!py.Qubit, !Any], %0) : !py.Qubit
  │ %2 = py.constant.constant 1 : !py.int
  │ %3 = py.indexing.getitem(%q : !py.IList[!py.Qubit, !Any], %2) : !py.Qubit
  │ %4 = func.invoke h(%1) : !py.NoneType maybe_pure=False
  │ %5 = func.invoke cx(%1, %3) : !py.NoneType maybe_pure=False
  │ %6 = func.const.none() : !py.NoneType
  │      func.return %6
} // func.func main
"""

    kernel = load(os.path.join(_RESOURCES, "bell_pair.ll"), register_as_argument=True)
    _compare_output(kernel, expected_output)


def test_ghz_state():
    """Test conversion of GHZ state from QIR to Squin."""
    expected_output = """func.func @main() -> !py.NoneType {
  ^0(%main_self):
  │ %0 = func.invoke new() : !py.Qubit maybe_pure=False
  │ %1 = func.invoke new() : !py.Qubit maybe_pure=False
  │ %2 = func.invoke new() : !py.Qubit maybe_pure=False
  │ %3 = func.invoke new() : !py.Qubit maybe_pure=False
  │ %4 = func.invoke h(%0) : !py.NoneType maybe_pure=False
  │ %5 = func.invoke cx(%0, %1) : !py.NoneType maybe_pure=False
  │ %6 = func.invoke cx(%1, %2) : !py.NoneType maybe_pure=False
  │ %7 = func.invoke cx(%2, %3) : !py.NoneType maybe_pure=False
  │ %8 = func.const.none() : !py.NoneType
  │      func.return %8
} // func.func main
"""

    kernel = load(os.path.join(_RESOURCES, "ghz_4.bc"))
    _compare_output(kernel, expected_output)
