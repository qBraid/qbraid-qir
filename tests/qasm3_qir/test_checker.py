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
Tests the checker module of qasm3

"""

import pytest

from qbraid_qir.qasm3.checker import validate_qasm, QasmValidationError


def test_correct_check():
    assert validate_qasm("OPENQASM 3; include 'stdgates.inc'; qubit q;") is None


def test_incorrect_check():
    with pytest.raises(QasmValidationError):
        validate_qasm(
            """
            //semantically incorrect program
            OPENQASM 3;
            include 'stdgates.inc';
            qubit q;
            for int[32] i in [0:10] {
            h q;
            }
            rx(3.14) q[2];
            """
        )


def test_incorrect_program_type():
    with pytest.raises(
        TypeError, match="Input quantum program must be of type 'str' or 'openqasm3.ast.Program'."
    ):
        validate_qasm(1234)
