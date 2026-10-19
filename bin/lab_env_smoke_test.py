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
Smoke test for a qbraid-qir Lab environment. Run it with the environment's own Python.

Usage:
    <env>/pyenv/bin/python bin/lab_env_smoke_test.py VERSION

"""

import platform
import sys

# Lab needs ipykernel to start the kernel. The rest come from the installed extras.
# pylint: disable=unused-import
import cirq
import ipykernel  # noqa: F401
import qiskit

import qbraid_qir
from qbraid_qir import cirq_to_qir, qasm3_to_qir, qiskit_to_qir
from qbraid_qir.squin import load

# pylint: enable=unused-import

PROGRAM = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
h q[0];
cx q[0], q[1];
"""


def main() -> None:
    """Check the qbraid-qir version, then convert a Bell circuit from each input format."""
    expected = sys.argv[1]
    if qbraid_qir.__version__ != expected:
        sys.exit(f"qbraid-qir {qbraid_qir.__version__} installed, expected {expected}")

    # The qasm3 extra.
    module = qasm3_to_qir(PROGRAM, name="bell")
    print(module)

    # The cirq extra.
    q0, q1 = cirq.LineQubit.range(2)
    cirq_to_qir(cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1)), name="bell")

    # The qiskit extra.
    circuit = qiskit.QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    qiskit_to_qir(circuit, name="bell")

    # The squin extra: load the QIR back as a squin kernel.
    load(str(module), kernel_name="main")

    print(
        f"qbraid-qir {qbraid_qir.__version__}, Python {platform.python_version()}, "
        f"{platform.machine()}"
    )


if __name__ == "__main__":
    main()
