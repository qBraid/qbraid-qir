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
