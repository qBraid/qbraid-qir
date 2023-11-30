# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module containing unit tests for Cirq to QIR conversion functions.

"""
import hashlib

import cirq
import pytest

from qbraid_qir.cirq.conversions import cirq_to_qir, generate_module_id
from qbraid_qir.exceptions import QirConversionError

from .qir_utils import assert_equal_qir


def test_cirq_to_qir_type_error():
    """Test raising exception for bad input type."""
    with pytest.raises(TypeError):
        cirq_to_qir(None)


def test_cirq_to_qir_conversion_error():
    """Test raising exception for conversion error."""
    circuit = cirq.Circuit()
    with pytest.raises(QirConversionError):
        cirq_to_qir(circuit)


def test_generate_module_id_format(cirq_bell):
    """Test generating module ID for a Cirq circuit fits expected format."""
    module_id = generate_module_id(cirq_bell)
    assert module_id.startswith("circuit-")
    assert len(module_id) == 15


def test_generate_module_id_hex(cirq_bell):
    """Test if generated module ID is consistent with manual SHA-256 computation."""
    module_id = generate_module_id(cirq_bell)
    serialized_circuit = cirq.to_json(cirq_bell)
    hash_object = hashlib.sha256(serialized_circuit.encode())
    hash_hex = hash_object.hexdigest()
    alphanumeric_hash = "".join(filter(str.isalnum, hash_hex))
    truncated_hash = alphanumeric_hash[:7]

    expected_id = f"circuit-{truncated_hash}"
    assert module_id == expected_id


def test_verify_qir_bell_fixture(pyqir_bell):
    """Test that pyqir fixture generates code equal to test_qir_bell.ll file."""
    assert_equal_qir(pyqir_bell.ir(), "test_qir_bell")


@pytest.mark.skip(reason="Not implemented yet")
def test_convert_bell_compare_file(cirq_bell):
    """Test converting Cirq bell circuit to QIR."""
    test_name = "test_qir_bell"
    generator = cirq_to_qir(cirq_bell, name=test_name)
    assert_equal_qir(generator.ir(), test_name)
