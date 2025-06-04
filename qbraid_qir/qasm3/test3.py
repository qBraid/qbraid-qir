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

from .convert import qasm3_to_qir, Profile

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

qasm = """
    OPENQASM 3;
    include "stdgates.inc";
    gate custom a, b{
        cx a, b;
        h a;
    }
    qubit[4] q;
    bit[4] c;
    bit[4] c0;

    h q;
    measure q -> c0;
    if(c0[0]){
        x q[0];
        cx q[0], q[1];
        if (c0[1]){
            cx q[1], q[2];
        }
    }
    if (c[0]){
        custom q[2], q[3];
    }
"""

qasm1 = """
    OPENQASM 3;
    include "stdgates.inc";
    
    qubit[3] q;
    bit[3] c;
    
    h q[0];
    c[0] = measure q[0];
    
    if (c[0]) {
        x q[1];
        h q[2];
    }
    
    c[1] = measure q[1];
    c[2] = measure q[2];
    """

qir_module = qasm3_to_qir(qasm1, profile="adaptive")

print(qir_module)
