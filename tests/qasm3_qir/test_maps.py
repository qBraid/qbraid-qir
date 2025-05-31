"""
Module containing unit tests for QASM3 native gate maps.
"""
import numpy as np
import pytest

from qbraid_qir.qasm3 import qasm3_to_qir
from qbraid_qir.qasm3.maps import map_qasm_op_to_pyqir_callable
from qbraid_qir.qasm3.exceptions import Qasm3ConversionError
from tests.qir_utils import (
    check_attributes,
    check_single_qubit_gate_op,
    check_single_qubit_rotation_op,
    check_two_qubit_gate_op,
)


def test_id_gate():
    """Test identity gate implementation"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit q;
    id q;
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 1, 0)
    # id_gate is implemented as two x gates
    check_single_qubit_gate_op(generated_qir, 2, [0, 0], "x")


def test_single_qubit_gates():
    """Test native single-qubit gates"""
    # Map QASM gate names to their QIR implementations
    gates = {
        "x": "x",
        "y": "y",
        "z": "z",
        "h": "h",
        "s": "s",
        "sdg": "s__adj",  # Changed to match QIR implementation
        "t": "t",
        "tdg": "t__adj"  # Changed to match QIR implementation
    }
    
    for gate_name, qir_name in gates.items():
        qasm3_string = f"""
        OPENQASM 3;
        include "stdgates.inc";
        qubit q;
        {gate_name} q;
        """
        result = qasm3_to_qir(qasm3_string)
        generated_qir = str(result).splitlines()
        print(f"\nTesting gate {gate_name} -> {qir_name}")
        print("Generated QIR:")
        for line in generated_qir:
            print(line)
        check_attributes(generated_qir, 1, 0)
        check_single_qubit_gate_op(generated_qir, 1, [0], qir_name)


def test_two_qubit_gates():
    """Test native two-qubit gates"""
    gates = {
        "cx": "cx",
        "cz": "cz",
        "swap": "swap"
    }
    
    for gate_name, qir_name in gates.items():
        qasm3_string = f"""
        OPENQASM 3;
        include "stdgates.inc";
        qubit[2] q;
        {gate_name} q[0], q[1];
        """
        result = qasm3_to_qir(qasm3_string)
        generated_qir = str(result).splitlines()
        check_attributes(generated_qir, 2, 0)
        check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], qir_name)


def test_rotation_gates():
    """Test native rotation gates"""
    gates = ["rx", "ry", "rz"]
    angle = 0.5
    
    for gate_name in gates:
        qasm3_string = f"""
        OPENQASM 3;
        include "stdgates.inc";
        qubit q;
        {gate_name}({angle}) q;
        """
        result = qasm3_to_qir(qasm3_string)
        generated_qir = str(result).splitlines()
        check_attributes(generated_qir, 1, 0)
        check_single_qubit_rotation_op(generated_qir, 1, [0], [angle], gate_name)


def test_map_qasm_op_to_pyqir_callable():
    """Test mapping QASM operations to PyQIR callables"""
    # Test valid native gates
    valid_gates = [
        "id", "x", "y", "z", "h", "s", "sdg", "t", "tdg",  # single-qubit
        "cx", "cz", "swap",  # two-qubit
        "rx", "ry", "rz"  # rotation
    ]
    
    for gate in valid_gates:
        callable_info = map_qasm_op_to_pyqir_callable(gate)
        assert callable_info is not None
        assert isinstance(callable_info, tuple)
        assert len(callable_info) == 2
        assert callable(callable_info[0])
        assert isinstance(callable_info[1], int)
        
    # Test invalid gate
    with pytest.raises(Qasm3ConversionError):
        map_qasm_op_to_pyqir_callable("invalid_gate")


def test_edge_cases():
    """Test edge cases and error handling"""
    # Empty operation name
    with pytest.raises(Qasm3ConversionError):
        map_qasm_op_to_pyqir_callable("")
    
    # None operation name
    with pytest.raises(TypeError):
        map_qasm_op_to_pyqir_callable(None)
    
    # Non-string operation name
    with pytest.raises(TypeError):
        map_qasm_op_to_pyqir_callable(123) 