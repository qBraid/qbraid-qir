# Copyright (C) 2024 qBraid
#
# This file is part of qbraid-qir
#
# Qbraid-qir is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for qbraid-qir, as per Section 15 of the GPL v3.

"""
Module containing unit tests for linalg.py functions.

"""
import numpy as np

from qbraid_qir.qasm3.linalg import _kak_canonicalize_vector


def test_kak_canonicalize_vector():
    """Test _kak_canonicalize_vector function."""
    x, y, z = -1, -2, -1
    result = _kak_canonicalize_vector(x, y, z)
    assert result["single_qubit_operations_before"][0][0][0] == -np.sqrt(2) / 2 * 1j

    x, y, z = 1, 2, 1
    result = _kak_canonicalize_vector(x, y, z)
    assert result["single_qubit_operations_before"][0][0][0] == -np.sqrt(2) / 2
