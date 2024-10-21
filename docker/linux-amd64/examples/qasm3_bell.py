# Copyright (C) 2024 qBraid
#
# This file is part of qbraid-qir
#
# Qbraid-qir is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for qbraid-qir, as per Section 15 of the GPL v3.

"""
Example of running an OpenQASM 3 program on the QIR bytecode runner.

"""

from qbraid.runtime import QirRunner

from qbraid_qir.qasm3 import qasm3_to_qir

program = """
OPENQASM 3;
include "stdgates.inc";
qubit[2] q;
bit[2] c;
h q[0];
cx q[0], q[1];
c = measure q;
"""

print(f"Program: \n{program}")

module = qasm3_to_qir(program, name="bell")

sim = QirRunner()

print(f"\nRunning on: {repr(sim)}")

result = sim.run(module.bitcode, shots=10)

print(f"\nResult: {result}")
