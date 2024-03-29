# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for qir-runner Python simulator wrapper.

"""
from qbraid_qir.runner import Simulator

output = """
START
METADATA        entry_point
METADATA        output_labeling_schema
METADATA        qir_profiles    custom
METADATA        required_num_qubits     2
METADATA        required_num_results    2
OUTPUT  RESULT  1
OUTPUT  RESULT  1
END     0
START
METADATA        entry_point
METADATA        output_labeling_schema
METADATA        qir_profiles    custom
METADATA        required_num_qubits     2
METADATA        required_num_results    2
OUTPUT  RESULT  1
OUTPUT  RESULT  1
END     0
START
METADATA        entry_point
METADATA        output_labeling_schema
METADATA        qir_profiles    custom
METADATA        required_num_qubits     2
METADATA        required_num_results    2
OUTPUT  RESULT  1
OUTPUT  RESULT  1
END     0
START
METADATA        entry_point
METADATA        output_labeling_schema
METADATA        qir_profiles    custom
METADATA        required_num_qubits     2
METADATA        required_num_results    2
OUTPUT  RESULT  0
OUTPUT  RESULT  0
END     0
START
METADATA        entry_point
METADATA        output_labeling_schema
METADATA        qir_profiles    custom
METADATA        required_num_qubits     2
METADATA        required_num_results    2
OUTPUT  RESULT  1
OUTPUT  RESULT  1
END     0
"""


def test_process_data():
    """Test the process_data method of the Simulator class."""
    results = Simulator._parse_results(output)
    assert results == {"qubit_0": [1, 1, 1, 0, 1], "qubit_1": [1, 1, 1, 0, 1]}
