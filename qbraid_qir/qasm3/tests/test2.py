from .convert import qasm3_to_qir

qasm3_module = """
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

qir_module = qasm3_to_qir(qasm3_module, profile="adaptive")

print(qir_module)