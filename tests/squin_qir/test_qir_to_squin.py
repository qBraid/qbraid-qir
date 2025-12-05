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
from typing import Any

from bloqade import qubit
from bloqade import squin as squin_gates
from kirin import ir
from kirin.dialects import func, py

from qbraid_qir.qasm3.convert import qasm3_to_qir
from qbraid_qir.squin import load

_RESOURCES = os.path.join(os.path.dirname(__file__), "resources")
_GATE_TYPE_MAP = {
    qubit.new: "qubit_new",
    squin_gates.h: "h",
    squin_gates.x: "x",
    squin_gates.y: "y",
    squin_gates.z: "z",
    squin_gates.s: "s",
    squin_gates.t: "t",
    squin_gates.s_adj: "sdg",
    squin_gates.t_adj: "tdg",
    squin_gates.rx: "rx",
    squin_gates.ry: "ry",
    squin_gates.rz: "rz",
    squin_gates.cx: "cx",
    squin_gates.cz: "cz",
}
_TYPE_MAP = {
    py.GetItem: "qubit_getitem",
    func.Return: "return",
    func.ConstantNone: "constant_none",
    py.Constant: "constant",
}


def _identify_statement_type(stmt: Any) -> str | None:
    """Identify the type of a statement."""
    if isinstance(stmt, func.Invoke):
        return _GATE_TYPE_MAP.get(stmt.callee)
    stmt_type = type(stmt)
    if stmt_type in _TYPE_MAP:
        return _TYPE_MAP[stmt_type]
    name = stmt_type.__name__.lower()
    if "getitem" in name or "indexing" in name:
        return "qubit_getitem"
    if "ilist" in name and "new" in name:
        return "ilist_new"
    return None


def _validate_statement_order(kernel: ir.Method, expected: list[str]) -> None:
    """Validate that statements in kernel match expected order."""
    actual = [
        t
        for s in kernel.code.body.blocks[0].stmts
        if (t := _identify_statement_type(s)) is not None
    ]
    assert actual == expected, f"Statement order mismatch.\nExpected: {expected}\nActual: {actual}"


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
    kernel = load(str(qasm3_to_qir(qasm3)), kernel_name="test_clifford")
    _validate_statement_order(
        kernel,
        [
            "qubit_new",
            "qubit_new",
            "h",
            "h",
            "x",
            "y",
            "z",
            "s",
            "t",
            "sdg",
            "tdg",
            "constant",
            "rx",
            "constant",
            "ry",
            "constant",
            "rz",
            "cx",
            "cz",
            "constant_none",
            "return",
        ],
    )


def test_bell_state():
    """Test conversion of Bell state from QIR to Squin."""
    kernel = load(os.path.join(_RESOURCES, "bell_pair.ll"), register_as_argument=True)
    _validate_statement_order(
        kernel,
        [
            "constant",
            "qubit_getitem",
            "constant",
            "qubit_getitem",
            "h",
            "cx",
            "constant_none",
            "return",
        ],
    )


def test_ghz_state():
    """Test conversion of GHZ state from QIR to Squin."""
    kernel = load(os.path.join(_RESOURCES, "ghz_4.bc"))
    _validate_statement_order(
        kernel,
        [
            "qubit_new",
            "qubit_new",
            "qubit_new",
            "qubit_new",
            "h",
            "cx",
            "cx",
            "cx",
            "constant_none",
            "return",
        ],
    )
