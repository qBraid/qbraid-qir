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
