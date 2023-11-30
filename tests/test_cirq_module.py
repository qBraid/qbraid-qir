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
Module containing unit tests for CirqModule and Module elements.

"""
import hashlib

import cirq

from qbraid_qir.cirq.elements import generate_module_id


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
