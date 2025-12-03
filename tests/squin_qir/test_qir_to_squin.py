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
Module containing unit tests for QIR to Squin conversion functions.

"""
import os

from kirin import ir

from qbraid_qir.qasm3.convert import qasm3_to_qir
from qbraid_qir.squin import load

RESOURCES_DIR = os.path.join(os.path.dirname(__file__), "resources")


def resources_file(filename: str) -> str:
    return os.path.join(RESOURCES_DIR, filename)


def test_all_supported_gates():
    """Test the conversion of all supported gates from QIR to Squin."""
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

    qir_mod = qasm3_to_qir(qasm3)
    squin_kernel = load(str(qir_mod), kernel_name="test_clifford")
    # Validate that squin_kernel is of the correct type (kirin.ir.Method)
    assert isinstance(
        squin_kernel, ir.Method
    ), f"Expected squin_kernel to be ir.Method, got {type(squin_kernel)}"

    squin_kernel.print()


def test_bell_state():
    """Test the conversion of the Bell state from QIR to Squin."""
    squin_kernel = load(resources_file("bell_pair.ll"), register_as_argument=True)
    assert isinstance(
        squin_kernel, ir.Method
    ), f"Expected squin_kernel to be ir.Method, got {type(squin_kernel)}"

    squin_kernel.print()


def test_ghz_state():
    """Test the conversion of the GHZ state from QIR to Squin."""
    squin_kernel = load(resources_file("ghz_4.bc"))
    assert isinstance(
        squin_kernel, ir.Method
    ), f"Expected squin_kernel to be ir.Method, got {type(squin_kernel)}"
    squin_kernel.print()
