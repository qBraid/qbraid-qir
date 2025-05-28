from .convert import qasm3_to_qir

qasm3_module = """

OPENQASM 3;
qubit[3] q;
bit[3] measurement_results;
bit[1] single_bit;
bit[5] larger_array;

reset q;
h q[0];
cx q[0], q[1];
cx q[1], q[2];

measure q[0] -> measurement_results[0];
measure q[1] -> measurement_results[1];
measure q[2] -> measurement_results[2];

h q[0];
measure q[0] -> single_bit[0];

if (measurement_results[0] == 1) {
    x q[1];
}

if (measurement_results[1] == 1) {
    if (measurement_results[2] == 1) {
        z q[0];
    }
}

if (measurement_results[0] == 1) {
    larger_array[0] = 1;
} else {
    larger_array[0] = 0;
}
if (measurement_results[1] == 1) {
    larger_array[1] = 1;
} else {
    larger_array[1] = 0;
}
if (measurement_results[2] == 1) {
    larger_array[2] = 1;
} else {
    larger_array[2] = 0;
}

// Skip XOR unless backend supports it
larger_array[4] = single_bit[0];

measure q -> measurement_results;

"""

qir_module = qasm3_to_qir(qasm3_module, profile="adaptive")

print(qir_module)