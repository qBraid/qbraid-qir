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
