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
Module containing unit tests for QIR to Squin error handlers.

"""

import os
import tempfile
from plistlib import InvalidFileException

import pytest
from pyqir import BasicQisBuilder, Context, Module, SimpleModule

from qbraid_qir.qasm3.convert import qasm3_to_qir
from qbraid_qir.squin import load
from qbraid_qir.squin.exceptions import InvalidSquinInput


def test_load_invalid_input_type():
    """Test invalid input types."""
    with pytest.raises(InvalidSquinInput, match="Invalid input.*expected 'str \\| pyqir.Module'"):
        load(None)


def test_load_invalid_file_extension():
    """Test files with invalid extensions."""
    # Create a temporary file with an invalid extension
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("some content")
        temp_file = f.name

    try:
        with pytest.raises(
            InvalidFileException, match="Expected file extension \\.ll or \\.bc but got"
        ):
            load(temp_file)
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_load_invalid_qir_ir_text():
    """Test invalid QIR IR text strings."""
    invalid_qir_text = "this is not valid QIR IR text"
    with pytest.raises(
        InvalidSquinInput, match="Invalid input.*String must be a valid QIR IR text"
    ):
        load(invalid_qir_text)


def test_load_module_without_entry_point():
    """Test when a module has no entry point."""
    ctx = Context()
    mod = Module(ctx, "NoEntry")
    with pytest.raises(InvalidSquinInput, match="No entry point found in pyqir module"):
        load(mod)


def test_load_module_with_zero_qubits():
    """Test when a module has zero qubits."""
    mod = SimpleModule("zero_qubits", num_qubits=0, num_results=0)
    _qis = BasicQisBuilder(mod.builder)
    with pytest.raises(
        InvalidSquinInput, match="Invalid number of qubits 0, must be greater than 0"
    ):
        load(mod._module)


def test_unsupported_gate():
    """Test unsupported gates."""
    qasm3 = """
    OPENQASM 3.0;
    include "stdgates.inc";
    qubit[1] q;
    bit[1] c; 
    c[0] = measure q[0];
    """

    qir_mod = qasm3_to_qir(qasm3)
    with pytest.raises(InvalidSquinInput, match="Unsupported gate: __quantum__qis__mz__body"):
        load(str(qir_mod))


def test_no_instructions_in_basic_block():
    """Test when a basic block has no instructions."""
    mod = SimpleModule("main", num_qubits=1, num_results=1)
    _qis = BasicQisBuilder(mod.builder)
    with pytest.raises(InvalidSquinInput, match="No instructions found in basic block"):
        load(mod._module)
