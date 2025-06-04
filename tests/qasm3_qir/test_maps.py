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
Unit tests for qbraid_qir.qasm3.maps module.
"""

import pytest

from qbraid_qir.qasm3.exceptions import Qasm3ConversionError
from qbraid_qir.qasm3.maps import (
    PYQIR_ONE_QUBIT_OP_MAP,
    PYQIR_ONE_QUBIT_ROTATION_MAP,
    PYQIR_THREE_QUBIT_OP_MAP,
    PYQIR_TWO_QUBIT_OP_MAP,
    map_qasm_op_to_pyqir_callable,
)


def test_map_qasm_op_to_pyqir_callable():
    """Test mapping QASM operations to PyQIR callables."""
    for op_name, op_func in PYQIR_ONE_QUBIT_OP_MAP.items():
        callable_func, qubit_count = map_qasm_op_to_pyqir_callable(op_name)
        assert callable_func == op_func
        assert qubit_count == 1

    for op_name, op_func in PYQIR_ONE_QUBIT_ROTATION_MAP.items():
        callable_func, qubit_count = map_qasm_op_to_pyqir_callable(op_name)
        assert callable_func == op_func
        assert qubit_count == 1

    for op_name, op_func in PYQIR_TWO_QUBIT_OP_MAP.items():
        callable_func, qubit_count = map_qasm_op_to_pyqir_callable(op_name)
        assert callable_func == op_func
        assert qubit_count == 2

    for op_name, op_func in PYQIR_THREE_QUBIT_OP_MAP.items():
        callable_func, qubit_count = map_qasm_op_to_pyqir_callable(op_name)
        assert callable_func == op_func
        assert qubit_count == 3

    with pytest.raises(Qasm3ConversionError):
        map_qasm_op_to_pyqir_callable("unsupported_op")


def test_map_qasm_op_to_pyqir_callable_edge_cases():
    """Test edge cases for map_qasm_op_to_pyqir_callable function."""
    assert map_qasm_op_to_pyqir_callable("cx")[0] == map_qasm_op_to_pyqir_callable("CX")[0]
    assert map_qasm_op_to_pyqir_callable("cnot")[0] == map_qasm_op_to_pyqir_callable("cx")[0]
    assert map_qasm_op_to_pyqir_callable("ccnot")[0] == map_qasm_op_to_pyqir_callable("ccx")[0]
    with pytest.raises(Qasm3ConversionError, match="Unsupported / undeclared QASM operation"):
        map_qasm_op_to_pyqir_callable("not_a_real_gate")
