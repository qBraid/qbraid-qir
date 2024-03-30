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
Unit tests for qir-runner Python result wrapper.

"""
import numpy as np

from qbraid_qir.runner.result import Result

stdout = """
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


def test_result():
    """Test the Result class."""
    result = Result(stdout, execution_duration=100)
    parsed_expected = {"q0": [1, 1, 1, 0, 1], "q1": [1, 1, 1, 0, 1]}
    measurements_expected = np.array([[1, 1], [1, 1], [1, 1], [0, 0], [1, 1]])
    counts_expected = {"00": 1, "11": 4}
    counts_decimal_expected = {0: 1, 3: 4}
    probabilities_expected = {"00": 0.2, "11": 0.8}
    metadata_expected = {
        "num_shots": 5,
        "num_qubits": 2,
        "execution_duration": 100,
        "measurements": measurements_expected,
        "measurement_counts": counts_expected,
        "measurement_probabilities": probabilities_expected,
    }
    assert result._parsed_data == parsed_expected
    assert np.array_equal(result.measurements, measurements_expected)
    assert result.measurement_counts() == counts_expected
    assert result.measurement_counts(decimal=True) == counts_decimal_expected
    assert result.measurement_probabilities() == probabilities_expected

    metadata_out = result.metadata()
    assert metadata_out["num_shots"] == metadata_expected["num_shots"]
    assert metadata_out["num_qubits"] == metadata_expected["num_qubits"]
    assert metadata_out["execution_duration"] == metadata_expected["execution_duration"]
    assert repr(result).startswith("Result")
