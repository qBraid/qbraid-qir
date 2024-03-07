# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.


# can use this -
# https://github.com/qBraid/qBraid/blob/eec41d1d4a2cbda0385191d041884fbe2965328e/qbraid/programs/qasm3.py#L108


# run simulations with both qasm3 and qir programs and compare the results for final tests


# can use rigetti simulator for qir programs and qiskit for qasm3 programs


# what are some problems which we face?

# 1. let us just unfold the gates once.
# assumption - we do not define any variables inside the gate
# - gate parameters are directly passed on to other gate calls
# - no if else conditions inside the gate
# - no loops inside the gate
# - no function calls inside the gate

# eg. gate x2(a,b,c) p, q {
#     h p;
#     h q;
#     rx(a) p;
#     ry(b) q;
#     rz(c) p;
#     cx p, q;
# }
#    qubit[2] q;
#    x2(1,2,3) q[0], q[1];

# will be converted to

# qubit[2] q;
# h q[0];
# h q[1];
# rx(1) q[0];
# ry(2) q[1];
# rz(3) q[0];
# cx q[0], q[1];
