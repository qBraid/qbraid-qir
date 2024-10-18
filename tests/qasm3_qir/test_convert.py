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
Tests the convert module of qasm3 to qir

"""

import pytest

from qbraid_qir.qasm3.convert import qasm3_to_qir


def test_correct_conversion():
    _ = qasm3_to_qir("OPENQASM 3; include 'stdgates.inc'; qubit q;")


def test_incorrect_conversion():
    with pytest.raises(
        TypeError, match="Input quantum program must be of type openqasm3.ast.Program or str."
    ):
        _ = qasm3_to_qir(1234)
