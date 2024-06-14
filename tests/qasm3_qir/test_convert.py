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
Tests the convert module of qasm3 to qir

"""

import pytest

from openqasm3_qir.convert import qasm3_to_qir


def test_correct_conversion():
    _ = qasm3_to_qir("OPENQASM 3; include 'stdgates.inc'; qubit q;")


def test_incorrect_conversion():
    with pytest.raises(
        TypeError, match="Input quantum program must be of type openqasm3.ast.Program or str."
    ):
        _ = qasm3_to_qir(1234)
