"""
Module containing unit tests for QASM3 gate maps and decompositions.
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
    check_three_qubit_gate_op,
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


def test_sx_and_sxdg_gates():
    """Test sqrt(X) and its dagger implementation"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    sx q[0];
    sxdg q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # sx is implemented as rx(pi/2)
    check_single_qubit_rotation_op(generated_qir, 1, [0], [np.pi/2], "rx")
    # sxdg is implemented as rx(-pi/2)
    check_single_qubit_rotation_op(generated_qir, 1, [1], [-np.pi/2], "rx")


def test_gpi_and_gpi2_gates():
    """Test GPI and GPI2 gate implementations"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    gpi(0.5) q[0];
    gpi2(0.5) q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # gpi is implemented as rz
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.5], "rz")
    # gpi2 is implemented as rx
    check_single_qubit_rotation_op(generated_qir, 1, [1], [0.5], "rx")


def test_phaseshift_gate():
    """Test phase shift gate implementation"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit q;
    phaseshift(0.5) q;
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 1, 0)
    # phaseshift is implemented as h-rx-h
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.5], "rx")
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")


def test_xx_gate():
    """Test XX gate implementation"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    xx(0.5) q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # Check XX gate decomposition
    check_single_qubit_gate_op(generated_qir, 2, [0, 1], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cz")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.5], "rx")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cz")
    check_single_qubit_gate_op(generated_qir, 2, [0, 1], "h")


def test_xy_gate():
    """Test XY gate implementation"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    xy(0.5) q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # Check XY gate decomposition
    check_single_qubit_rotation_op(generated_qir, 1, [0], [-0.5/2], "rx")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [0.5/2], "ry")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.5/2], "ry")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.5/2], "rx")
    check_two_qubit_gate_op(generated_qir, 1, [[1, 0]], "cx")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [-0.5/2], "ry")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [-0.5/2], "ry")
    check_two_qubit_gate_op(generated_qir, 1, [[1, 0]], "cx")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.5/2], "rx")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [-0.5/2], "ry")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [0.5/2], "ry")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [-0.5/2], "rx")


def test_yy_gate():
    """Test YY gate implementation"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    yy(0.5) q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # Check YY gate decomposition
    check_single_qubit_rotation_op(generated_qir, 2, [0, 1], [0.5/2], "rx")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cz")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [0.5], "rx")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cz")
    check_single_qubit_rotation_op(generated_qir, 2, [0, 1], [-0.5/2], "rx")


def test_zz_gate():
    """Test ZZ gate implementation"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    zz(0.5) q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # Check ZZ gate decomposition
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cz")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [0.5], "rz")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cz")


def test_cv_gate():
    """Test controlled-V gate implementation"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    cv q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # Check CV gate decomposition
    check_single_qubit_gate_op(generated_qir, 1, [0], "x")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [np.pi/4], "rx")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_gate_op(generated_qir, 1, [0], "t_adj")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_single_qubit_gate_op(generated_qir, 1, [0], "x")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [-np.pi/4], "rz")


def test_cy_gate():
    """Test controlled-Y gate implementation"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    cy q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # Check CY gate decomposition
    check_single_qubit_gate_op(generated_qir, 1, [1], "s_adj")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_gate_op(generated_qir, 1, [1], "s")


def test_pswap_gate():
    """Test parameterized SWAP gate implementation"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    pswap(0.5) q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # Check PSWAP gate decomposition
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "swap")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [0.5], "rz")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")


def test_cphaseshift_gates():
    """Test controlled phase shift gates and variants"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    cphaseshift(0.5) q[0], q[1];
    cphaseshift00(0.5) q[0], q[1];
    cphaseshift01(0.5) q[0], q[1];
    cphaseshift10(0.5) q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    
    # Check cphaseshift decomposition
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.5], "rx")
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")
    
    # Check cphaseshift00 decomposition
    check_single_qubit_gate_op(generated_qir, 2, [0, 1], "x")
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.5], "rx")
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")
    check_single_qubit_gate_op(generated_qir, 2, [0, 1], "x")
    
    # Check cphaseshift01 decomposition
    check_single_qubit_gate_op(generated_qir, 1, [0], "x")
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.5], "rx")
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")
    check_single_qubit_gate_op(generated_qir, 1, [0], "x")
    
    # Check cphaseshift10 decomposition
    check_single_qubit_gate_op(generated_qir, 1, [1], "x")
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.5], "rx")
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")
    check_single_qubit_gate_op(generated_qir, 1, [1], "x")


def test_ecr_gate():
    """Test ECR gate implementation"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    ecr q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # Check ECR gate decomposition
    check_single_qubit_gate_op(generated_qir, 1, [1], "s")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_single_qubit_gate_op(generated_qir, 1, [1], "s_adj")


def test_ms_gate():
    """Test Mølmer-Sørensen gate implementation"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    ms(0.1, 0.2, 0.3) q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # Check MS gate decomposition
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.1], "rz")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [0.2], "rz")
    check_single_qubit_gate_op(generated_qir, 2, [0, 1], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cz")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [0.3], "rx")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cz")
    check_single_qubit_gate_op(generated_qir, 2, [0, 1], "h")


def test_cswap_gate():
    """Test controlled-SWAP (Fredkin) gate implementation"""
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[3] q;
    cswap q[0], q[1], q[2];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 3, 0)
    # Check CSWAP gate decomposition
    check_two_qubit_gate_op(generated_qir, 1, [[2, 1]], "cx")
    check_single_qubit_gate_op(generated_qir, 1, [2], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[1, 2]], "cx")
    check_single_qubit_gate_op(generated_qir, 1, [2], "t_adj")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 2]], "cx")
    check_single_qubit_gate_op(generated_qir, 1, [2], "t")
    check_two_qubit_gate_op(generated_qir, 1, [[1, 2]], "cx")
    check_single_qubit_gate_op(generated_qir, 1, [1], "t")
    check_single_qubit_gate_op(generated_qir, 1, [2], "t_adj")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 2]], "cx")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_gate_op(generated_qir, 1, [2], "t")
    check_single_qubit_gate_op(generated_qir, 1, [0], "t")
    check_single_qubit_gate_op(generated_qir, 1, [1], "t_adj")
    check_single_qubit_gate_op(generated_qir, 1, [2], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_two_qubit_gate_op(generated_qir, 1, [[2, 1]], "cx")


def test_map_qasm_op_to_pyqir_callable():
    """Test mapping QASM operations to PyQIR callables"""
    # Test single qubit gates
    func, num_qubits = map_qasm_op_to_pyqir_callable("x")
    assert num_qubits == 1
    assert func.__name__ == "x"

    func, num_qubits = map_qasm_op_to_pyqir_callable("h")
    assert num_qubits == 1
    assert func.__name__ == "h"

    # Test two qubit gates
    func, num_qubits = map_qasm_op_to_pyqir_callable("cx")
    assert num_qubits == 2
    assert func.__name__ == "cx"

    func, num_qubits = map_qasm_op_to_pyqir_callable("cz")
    assert num_qubits == 2
    assert func.__name__ == "cz"

    # Test three qubit gates
    func, num_qubits = map_qasm_op_to_pyqir_callable("ccx")
    assert num_qubits == 3
    assert func.__name__ == "ccx"

    # Test invalid gate
    with pytest.raises(Qasm3ConversionError):
        map_qasm_op_to_pyqir_callable("invalid_gate")


def test_edge_cases():
    """Test edge cases and error conditions"""
    # Test gates with invalid parameters
    with pytest.raises(Exception):  # Should raise some kind of error
        qasm3_string = """
        OPENQASM 3;
        include "stdgates.inc";
        qubit q;
        rx(invalid) q;
        """
        qasm3_to_qir(qasm3_string)

    # Test gates with missing parameters
    with pytest.raises(Exception):  # Should raise some kind of error
        qasm3_string = """
        OPENQASM 3;
        include "stdgates.inc";
        qubit q;
        rx q;
        """
        qasm3_to_qir(qasm3_string)

    # Test gates with wrong number of qubits
    with pytest.raises(Exception):  # Should raise some kind of error
        qasm3_string = """
        OPENQASM 3;
        include "stdgates.inc";
        qubit[2] q;
        x q[0], q[1];
        """
        qasm3_to_qir(qasm3_string)

    # Test gates with out of range qubit indices
    with pytest.raises(Exception):  # Should raise some kind of error
        qasm3_string = """
        OPENQASM 3;
        include "stdgates.inc";
        qubit[2] q;
        x q[2];
        """
        qasm3_to_qir(qasm3_string)


def test_parameter_edge_cases():
    """Test edge cases for gate parameters"""
    # Test gates with zero parameters
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    rx(0) q[0];
    ry(0) q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0], "rx")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [0], "ry")

    # Test gates with very large parameters
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    rx(1000000) q[0];
    ry(1000000) q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    check_single_qubit_rotation_op(generated_qir, 1, [0], [1000000], "rx")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [1000000], "ry")

    # Test gates with negative parameters
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    rx(-0.5) q[0];
    ry(-0.5) q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    check_single_qubit_rotation_op(generated_qir, 1, [0], [-0.5], "rx")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [-0.5], "ry")


def test_qubit_edge_cases():
    """Test edge cases for qubit handling"""
    # Test single qubit gate on all qubits in register
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[3] q;
    x q;
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 3, 0)
    check_single_qubit_gate_op(generated_qir, 3, [0, 1, 2], "x")

    # Test two qubit gate on all qubit pairs in register
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[3] q;
    cx q[0], q[1];
    cx q[1], q[2];
    cx q[0], q[2];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 3, 0)
    check_two_qubit_gate_op(generated_qir, 3, [[0, 1], [1, 2], [0, 2]], "cx")

    # Test three qubit gate on all qubit triplets in register
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[4] q;
    ccx q[0], q[1], q[2];
    ccx q[1], q[2], q[3];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 4, 0)
    check_three_qubit_gate_op(generated_qir, 2, [[0, 1, 2], [1, 2, 3]], "ccx")


def test_pyqasm_gate_decompositions():
    """Test gate decompositions that are used in pyqasm"""
    # Test U3 gate decomposition
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit q;
    u3(0.1, 0.2, 0.3) q;
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 1, 0)
    # U3 decomposition: rz(λ) - rx(π/2) - rz(θ+π) - rx(π/2) - rz(φ+π)
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.3], "rz")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [np.pi/2], "rx")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.1 + np.pi], "rz")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [np.pi/2], "rx")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.2 + np.pi], "rz")

    # Test U2 gate decomposition
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit q;
    u2(0.1, 0.2) q;
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 1, 0)
    # U2 is U3(π/2, φ, λ)
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.2], "rz")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [np.pi/2], "rx")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [np.pi/2 + np.pi], "rz")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [np.pi/2], "rx")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [0.1 + np.pi], "rz")

    # Test controlled phase gates
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    cp(0.5) q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # CP decomposition: rz(θ/2) q[1]; cx q[0],q[1]; rz(-θ/2) q[1]; cx q[0],q[1]
    check_single_qubit_rotation_op(generated_qir, 1, [1], [0.5/2], "rz")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [-0.5/2], "rz")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")

    # Test controlled-sqrt(X) gate
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    csx q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # CSX decomposition: h q[1]; cx q[0],q[1]; h q[1]; t q[1]; h q[1]; cx q[0],q[1]; t_adj q[1]; h q[1]
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_single_qubit_gate_op(generated_qir, 1, [1], "t")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_gate_op(generated_qir, 1, [1], "t_adj")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")

    # Test controlled-H gate
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    ch q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # CH decomposition: sdg q[1]; h q[1]; t q[1]; cx q[0],q[1]; t_adj q[1]; h q[1]; s q[1]
    check_single_qubit_gate_op(generated_qir, 1, [1], "s_adj")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_single_qubit_gate_op(generated_qir, 1, [1], "t")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_gate_op(generated_qir, 1, [1], "t_adj")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_single_qubit_gate_op(generated_qir, 1, [1], "s")


def test_remaining_gate_decompositions():
    """Test remaining gate decompositions"""
    # Test iSwap gate
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    iswap q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # iSwap decomposition: s q[0]; s q[1]; h q[1]; cx q[0],q[1]; cx q[1],q[0]; h q[0]
    check_single_qubit_gate_op(generated_qir, 1, [0], "s")
    check_single_qubit_gate_op(generated_qir, 1, [1], "s")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_two_qubit_gate_op(generated_qir, 1, [[1, 0]], "cx")
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")

    # Test Rxx gate
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    rxx(0.5) q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # Rxx decomposition: h q[0]; h q[1]; cx q[0],q[1]; rz(θ) q[1]; cx q[0],q[1]; h q[0]; h q[1]
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [0.5], "rz")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_gate_op(generated_qir, 1, [0], "h")
    check_single_qubit_gate_op(generated_qir, 1, [1], "h")

    # Test Ryy gate
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    ryy(0.5) q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # Ryy decomposition: rx(π/2) q[0]; rx(π/2) q[1]; cx q[0],q[1]; rz(θ) q[1]; cx q[0],q[1]; rx(-π/2) q[0]; rx(-π/2) q[1]
    check_single_qubit_rotation_op(generated_qir, 1, [0], [np.pi/2], "rx")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [np.pi/2], "rx")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [0.5], "rz")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_rotation_op(generated_qir, 1, [0], [-np.pi/2], "rx")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [-np.pi/2], "rx")

    # Test Rzz gate
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    rzz(0.5) q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # Rzz decomposition: cx q[0],q[1]; rz(θ) q[1]; cx q[0],q[1]
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [0.5], "rz")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")

    # Test controlled-U1 gate
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    cu1(0.5) q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # CU1 decomposition: rz(θ/2) q[1]; cx q[0],q[1]; rz(-θ/2) q[1]; cx q[0],q[1]
    check_single_qubit_rotation_op(generated_qir, 1, [1], [0.5/2], "rz")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")
    check_single_qubit_rotation_op(generated_qir, 1, [1], [-0.5/2], "rz")
    check_two_qubit_gate_op(generated_qir, 1, [[0, 1]], "cx")

    # Test controlled-U3 gate
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    cu3(0.1, 0.2, 0.3) q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)
    # CU3 decomposition is complex, just verify the number of operations
    # The exact decomposition should be verified in a separate unit test
    assert len([line for line in generated_qir if "call" in line]) > 5


def test_kak_decomposition():
    """Test KAK decomposition used in some gates"""
    # Test arbitrary two-qubit gate using KAK decomposition
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    // This is a custom gate that would use KAK decomposition
    // The actual gate doesn't matter as we just want to test the decomposition
    xx(0.5) q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)

    # KAK decomposition should result in a sequence of:
    # 1. Single-qubit gates (h, rx, ry, rz)
    # 2. Two-qubit gates (cx, cz)
    # 3. More single-qubit gates
    
    # Count the number of each type of operation
    single_qubit_ops = len([line for line in generated_qir if any(op in line for op in ["h", "rx", "ry", "rz"])])
    two_qubit_ops = len([line for line in generated_qir if any(op in line for op in ["cx", "cz"])])
    
    # KAK decomposition typically uses around 3-4 two-qubit gates
    assert 1 <= two_qubit_ops <= 4, f"Expected 1-4 two-qubit gates, got {two_qubit_ops}"
    
    # And several single-qubit gates
    assert single_qubit_ops >= 4, f"Expected at least 4 single-qubit gates, got {single_qubit_ops}"

    # Test another gate that uses KAK decomposition
    qasm3_string = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    // Another custom gate using KAK decomposition
    xy(0.5) q[0], q[1];
    """
    result = qasm3_to_qir(qasm3_string)
    generated_qir = str(result).splitlines()
    check_attributes(generated_qir, 2, 0)

    # Similar checks for the second gate
    single_qubit_ops = len([line for line in generated_qir if any(op in line for op in ["h", "rx", "ry", "rz"])])
    two_qubit_ops = len([line for line in generated_qir if any(op in line for op in ["cx", "cz"])])
    
    assert 1 <= two_qubit_ops <= 4, f"Expected 1-4 two-qubit gates, got {two_qubit_ops}"
    assert single_qubit_ops >= 4, f"Expected at least 4 single-qubit gates, got {single_qubit_ops}" 