from .convert import qasm3_to_qir, Qasm3ConversionError
import pytest

adaptive_only_qasm = """
OPENQASM 3;
qubit[1] q;
bit[1] b;
reset q;
h q[0];
measure q[0] -> b[0];
if (b[0]) {
    x q[0];
}
"""

def test_adaptive_profile_accepts_control_flow():
    try:
        qir_module = qasm3_to_qir(adaptive_only_qasm, profile="adaptive")
        assert qir_module is not None
    except Exception as e:
        pytest.fail(f"Adaptive profile failed: {e}")

    # try:
    #     qir_module = qasm3_to_qir(adaptive_only_qasm, profile="base")
    #     assert qir_module is not None
    # except Exception as e:
    #     pytest.fail(f"Base profile failed: {e}")

# def test_base_profile_rejects_control_flow():
#     with pytest.raises(Exception):  # ideally Qasm3ConversionError
#         qasm3_to_qir(adaptive_only_qasm, profile="base")
