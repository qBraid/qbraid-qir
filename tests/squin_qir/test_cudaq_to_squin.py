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

"""Unit tests for CUDAQ to Squin conversion functions."""

import cudaq

from qbraid_qir.squin import load

from .test_qir_to_squin import _validate_statement_order


def test_bell_state():
    @cudaq.kernel
    def bell():
        q = cudaq.qvector(2)
        h(q[0])  # pylint: disable=undefined-variable
        cx(q[0], q[1])  # pylint: disable=undefined-variable

    qir_str = cudaq.translate(bell, format="qir-base")
    squin_kernel = load(qir_str)
    _validate_statement_order(
        squin_kernel,
        [
            "qubit_new",
            "qubit_new",
            "h",
            "cx",
            "constant_none",
            "return",
        ],
    )


def test_ghz_state():
    @cudaq.kernel
    def ghz():
        q = cudaq.qvector(3)
        h(q[0])  # pylint: disable=undefined-variable
        for j in range(2):
            cx(q[j], q[j + 1])  # pylint: disable=undefined-variable

    qir_str = cudaq.translate(ghz, format="qir-base")
    squin_kernel = load(qir_str)
    _validate_statement_order(
        squin_kernel,
        [
            "qubit_new",
            "qubit_new",
            "qubit_new",
            "h",
            "cx",
            "cx",
            "constant_none",
            "return",
        ],
    )
