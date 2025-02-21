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
Module mapping supported QASM gates/operations to pyqir functions.

"""
from typing import Callable, Union

import numpy as np
import pyqir
from pyqasm.linalg import kak_decomposition_angles

from .exceptions import Qasm3ConversionError


def id_gate(builder, qubits):
    pyqir._native.x(builder, qubits)
    pyqir._native.x(builder, qubits)


def u3_gate(
    builder,
    theta: Union[int, float],
    phi: Union[int, float],
    lam: Union[int, float],
    qubits,
):
    """
    Implements the U3 gate using the following decomposition:
         https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.UGate
         https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.PhaseGate

    Args:
        builder (pyqir._native.QirBuilder): The QIR builder.
        theta (Union[int, float]): The theta angle.
        phi (Union[int, float]): The phi angle.
        lam (Union[int, float]): The lambda angle.
        qubits: The qubits on which the gate is applied.

    Returns:
        None
    """
    pyqir._native.rz(builder, lam, qubits)
    pyqir._native.rx(builder, CONSTANTS_MAP["pi"] / 2, qubits)
    pyqir._native.rz(builder, theta + CONSTANTS_MAP["pi"], qubits)
    pyqir._native.rx(builder, CONSTANTS_MAP["pi"] / 2, qubits)
    pyqir._native.rz(builder, phi + CONSTANTS_MAP["pi"], qubits)
    # global phase - e^(i*(phi+lambda)/2) is missing in the above implementation


def u3_inv_gate(
    builder,
    theta: Union[int, float],
    phi: Union[int, float],
    lam: Union[int, float],
    qubits,
):
    """
    Implements the inverse of the U3 gate using the decomposition present in
    the u3_gate function.
    """
    pyqir._native.rz(builder, -1.0 * (phi + CONSTANTS_MAP["pi"]), qubits)
    pyqir._native.rx(builder, -1.0 * (CONSTANTS_MAP["pi"] / 2), qubits)
    pyqir._native.rz(builder, -1.0 * (theta + CONSTANTS_MAP["pi"]), qubits)
    pyqir._native.rx(builder, -1.0 * (CONSTANTS_MAP["pi"] / 2), qubits)
    pyqir._native.rz(builder, -1.0 * lam, qubits)


def u2_gate(builder, phi, lam, qubits):
    """
    Implements the U2 gate using the following decomposition:
        https://docs.quantum.ibm.com/api/qiskit/qiskit.circuit.library.U2Gate
    """
    u3_gate(builder, CONSTANTS_MAP["pi"] / 2, phi, lam, qubits)


def u2_inv_gate(builder, phi, lam, qubits):
    """
    Implements the inverse of the U2 gate using the decomposition present in
    the u2_gate function.
    """
    u3_inv_gate(builder, CONSTANTS_MAP["pi"] / 2, phi, lam, qubits)


def sx_gate(builder, qubits):
    """
    Implements the Sqrt(X) gate as a decomposition of other gates.
    """
    pyqir._native.rx(builder, CONSTANTS_MAP["pi"] / 2, qubits)


def sxdg_gate(builder, qubits):
    """
    Implements the conjugate transpose of the Sqrt(X) gate as a decomposition of other gates.
    """
    pyqir._native.rx(builder, -CONSTANTS_MAP["pi"] / 2, qubits)


def cv_gate(builder, qubit0, qubit1):
    """
    Implements the controlled V gate as a decomposition of other gates.
    """
    pyqir._native.x(builder, qubit0)
    pyqir._native.h(builder, qubit1)
    pyqir._native.cx(builder, qubit0, qubit1)
    pyqir._native.h(builder, qubit1)
    pyqir._native.rx(builder, CONSTANTS_MAP["pi"] / 4, qubit1)
    pyqir._native.h(builder, qubit1)
    pyqir._native.cx(builder, qubit0, qubit1)
    pyqir._native.t_adj(builder, qubit0)
    pyqir._native.h(builder, qubit1)
    pyqir._native.x(builder, qubit0)
    pyqir._native.rz(builder, -CONSTANTS_MAP["pi"] / 4, qubit1)


def cy_gate(builder, qubit0, qubit1):
    """
    Implements the CY gate as a decomposition of other gates.
    """
    pyqir._native.s_adj(builder, qubit1)
    pyqir._native.cx(builder, qubit0, qubit1)
    pyqir._native.s(builder, qubit1)


def xx_gate(builder, theta, qubit0, qubit1):
    """
    Implements the XX gate as a decomposition of other gates.
    """
    qubits = [qubit0, qubit1]
    pyqir._native.h(builder, qubits[0])
    pyqir._native.h(builder, qubits[1])
    pyqir._native.cz(builder, qubits[0], qubits[1])
    pyqir._native.h(builder, qubits[1])
    pyqir._native.rx(builder, theta, qubits[0])
    pyqir._native.h(builder, qubits[1])
    pyqir._native.cz(builder, qubits[0], qubits[1])
    pyqir._native.h(builder, qubits[0])
    pyqir._native.h(builder, qubits[1])


def xy_gate(builder, theta, qubit0, qubit1):
    """
    Implements the XY gate as a decomposition of other gates.
    """
    qubits = [qubit0, qubit1]
    pyqir._native.rx(builder, -theta / 2, qubits[0])
    pyqir._native.ry(builder, theta / 2, qubits[1])
    pyqir._native.ry(builder, theta / 2, qubits[0])
    pyqir._native.rx(builder, theta / 2, qubits[0])
    pyqir._native.cx(builder, qubits[1], qubits[0])
    pyqir._native.ry(builder, -theta / 2, qubits[0])
    pyqir._native.ry(builder, -theta / 2, qubits[1])
    pyqir._native.cx(builder, qubits[1], qubits[0])
    pyqir._native.rx(builder, theta / 2, qubits[0])
    pyqir._native.ry(builder, -theta / 2, qubits[1])
    pyqir._native.ry(builder, theta / 2, qubits[1])
    pyqir._native.rx(builder, -theta / 2, qubits[0])


def yy_gate(builder, theta, qubit0, qubit1):
    """
    Implements the YY gate as a decomposition of other gates.
    """
    qubits = [qubit0, qubit1]
    pyqir._native.rx(builder, theta / 2, qubits[0])
    pyqir._native.rx(builder, theta / 2, qubits[1])
    pyqir._native.cz(builder, qubits[0], qubits[1])
    pyqir._native.h(builder, qubits[1])
    pyqir._native.rx(builder, theta, qubits[1])
    pyqir._native.h(builder, qubits[1])
    pyqir._native.cz(builder, qubits[0], qubits[1])
    pyqir._native.rx(builder, -theta / 2, qubits[0])
    pyqir._native.rx(builder, -theta / 2, qubits[1])


def zz_gate(builder, theta, qubit0, qubit1):
    """
    Implements the ZZ gate as a decomposition of other gates.
    """
    qubits = [qubit0, qubit1]
    pyqir._native.cz(builder, qubits[0], qubits[1])
    pyqir._native.h(builder, qubits[1])
    pyqir._native.rz(builder, theta, qubits[1])
    pyqir._native.h(builder, qubits[1])
    pyqir._native.cz(builder, qubits[0], qubits[1])


def phaseshift_gate(builder, theta, qubit):
    """
    Implements the phase shift gate as a decomposition of other gates.
    """
    pyqir._native.h(builder, qubit)
    pyqir._native.rx(builder, theta, qubit)
    pyqir._native.h(builder, qubit)


def cswap_gate(builder, qubit0, qubit1, qubit2):
    """
    Implements the CSWAP gate as a decomposition of other gates.
    """
    qubits = [qubit0, qubit1, qubit2]
    pyqir._native.cx(builder, qubits[2], qubits[1])
    pyqir._native.h(builder, qubits[2])
    pyqir._native.cx(builder, qubits[1], qubits[2])
    pyqir._native.t_adj(builder, qubits[2])
    pyqir._native.cx(builder, qubits[0], qubits[2])
    pyqir._native.t(builder, qubits[2])
    pyqir._native.cx(builder, qubits[1], qubits[2])
    pyqir._native.t(builder, qubits[1])
    pyqir._native.t_adj(builder, qubits[2])
    pyqir._native.cx(builder, qubits[0], qubits[2])
    pyqir._native.cx(builder, qubits[0], qubits[1])
    pyqir._native.t(builder, qubits[2])
    pyqir._native.t(builder, qubits[0])
    pyqir._native.t_adj(builder, qubits[1])
    pyqir._native.h(builder, qubits[2])
    pyqir._native.cx(builder, qubits[0], qubits[1])
    pyqir._native.cx(builder, qubits[2], qubits[1])


def pswap_gate(builder, theta, qubit0, qubit1):
    """
    Implements the PSWAP gate as a decomposition of other gates.

    """
    qubits = [qubit0, qubit1]
    pyqir._native.swap(builder, qubits[0], qubits[1])
    pyqir._native.cx(builder, qubits[0], qubits[1])
    u3_gate(builder, 0, 0, theta, qubits[1])
    pyqir._native.cx(builder, qubits[0], qubits[1])


def cphaseshift_gate(builder, theta, qubit0, qubit1):
    """
    Implements the controlled phase shift gate as a decomposition of other gates.
    """
    qubits = [qubit0, qubit1]
    pyqir._native.h(builder, qubits[0])
    pyqir._native.rx(builder, theta / 2, qubits[0])
    pyqir._native.h(builder, qubits[0])
    pyqir._native.cx(builder, qubits[0], qubits[1])
    pyqir._native.h(builder, qubits[1])
    pyqir._native.rx(builder, -theta / 2, qubits[0])
    pyqir._native.h(builder, qubits[1])
    pyqir._native.cx(builder, qubits[0], qubits[1])
    pyqir._native.h(builder, qubits[1])
    pyqir._native.rx(builder, theta / 2, qubits[1])
    pyqir._native.h(builder, qubits[1])


def cphaseshift00_gate(builder, theta, qubit0, qubit1):
    """
    Implements the controlled phase shift 00 gate as a decomposition of other gates.

    """
    qubits = [qubit0, qubit1]
    pyqir._native.x(builder, qubits[0])
    pyqir._native.x(builder, qubits[1])
    u3_gate(builder, 0, 0, theta / 2, qubits[0])
    u3_gate(builder, 0, 0, theta / 2, qubits[1])
    pyqir._native.cx(builder, qubits[0], qubits[1])
    u3_gate(builder, 0, 0, -theta / 2, qubits[1])
    pyqir._native.cx(builder, qubits[0], qubits[1])
    pyqir._native.x(builder, qubits[0])
    pyqir._native.x(builder, qubits[1])


def cphaseshift01_gate(builder, theta, qubit0, qubit1):
    """
    Implements the controlled phase shift 01 gate as a decomposition of other gates.

    """
    qubits = [qubit0, qubit1]
    pyqir._native.x(builder, qubits[0])
    u3_gate(builder, 0, 0, theta / 2, qubits[1])
    u3_gate(builder, 0, 0, theta / 2, qubits[0])
    pyqir._native.cx(builder, qubits[0], qubits[1])
    u3_gate(builder, 0, 0, -theta / 2, qubits[1])
    pyqir._native.cx(builder, qubits[0], qubits[1])
    pyqir._native.x(builder, qubits[0])


def cphaseshift10_gate(builder, theta, qubit0, qubit1):
    """
    Implements the controlled phase shift 10 gate as a decomposition of other gates.

    """
    qubits = [qubit0, qubit1]
    u3_gate(builder, 0, 0, theta / 2, qubits[0])
    pyqir._native.x(builder, qubits[1])
    u3_gate(builder, 0, 0, theta / 2, qubits[1])
    pyqir._native.cx(builder, qubits[0], qubits[1])
    u3_gate(builder, 0, 0, -theta / 2, qubits[1])
    pyqir._native.cx(builder, qubits[0], qubits[1])
    pyqir._native.x(builder, qubits[1])


def gpi_gate(builder, phi, qubit):
    """
    Implements the gpi gate as a decomposition of other gates.
    """
    theta_0 = CONSTANTS_MAP["pi"]
    phi_0 = phi
    lambda_0 = -phi_0 + CONSTANTS_MAP["pi"]
    u3_gate(builder, theta_0, phi_0, lambda_0, qubit)


def gpi2_gate(builder, phi, qubit):
    """
    Implements the gpi2 gate as a decomposition of other gates.
    """
    theta_0 = CONSTANTS_MAP["pi"] / 2
    phi_0 = phi + 3 * CONSTANTS_MAP["pi"] / 2
    lambda_0 = -phi_0 + CONSTANTS_MAP["pi"] / 2
    u3_gate(builder, theta_0, phi_0, lambda_0, qubit)


# pylint: disable-next=too-many-arguments
def ms_gate(builder, phi0, phi1, theta, qubit0, qubit1):
    """
    Implements the Molmer Sorenson gate as a decomposition of other gates.
    """
    mat = np.array(
        [
            [
                np.cos(np.pi * theta),
                0,
                0,
                -1j * np.exp(-1j * 2 * np.pi * (phi0 + phi1)) * np.sin(np.pi * theta),
            ],
            [
                0,
                np.cos(np.pi * theta),
                -1j * np.exp(-1j * 2 * np.pi * (phi0 - phi1)) * np.sin(np.pi * theta),
                0,
            ],
            [
                0,
                -1j * np.exp(1j * 2 * np.pi * (phi0 - phi1)) * np.sin(np.pi * theta),
                np.cos(np.pi * theta),
                0,
            ],
            [
                -1j * np.exp(1j * 2 * np.pi * (phi0 + phi1)) * np.sin(np.pi * theta),
                0,
                0,
                np.cos(np.pi * theta),
            ],
        ]
    )
    angles = kak_decomposition_angles(mat)
    qubits = [qubit0, qubit1]

    u3_gate(builder, angles[0][0], angles[0][1], angles[0][2], qubits[0])
    u3_gate(builder, angles[1][0], angles[1][1], angles[1][2], qubits[1])
    sx_gate(builder, qubits[0])
    pyqir._native.cx(builder, qubits[0], qubits[1])
    pyqir._native.rx(builder, ((1 / 2) - 2 * theta) * CONSTANTS_MAP["pi"], qubits[0])
    pyqir._native.rx(builder, CONSTANTS_MAP["pi"] / 2, qubits[1])
    pyqir._native.cx(builder, qubits[1], qubits[0])
    sxdg_gate(builder, qubits[1])
    pyqir._native.s(builder, qubits[1])
    pyqir._native.cx(builder, qubits[0], qubits[1])
    u3_gate(builder, angles[2][0], angles[2][1], angles[2][2], qubits[0])
    u3_gate(builder, angles[3][0], angles[3][1], angles[3][2], qubits[1])


def ecr_gate(builder, qubit0, qubit1):
    """
    Implements the ECR gate as a decomposition of other gates.

    """
    qubits = [qubit0, qubit1]
    pyqir._native.s(builder, qubits[0])
    pyqir._native.rx(builder, CONSTANTS_MAP["pi"] / 2, qubits[1])
    pyqir._native.cx(builder, qubits[0], qubits[1])
    pyqir._native.x(builder, qubits[0])


def prx_gate(builder, theta, phi, qubit):
    """
    Implements the PRX gate as a decomposition of other gates.
    """
    theta_0 = theta
    phi_0 = CONSTANTS_MAP["pi"] / 2 - phi
    lambda_0 = -phi_0
    u3_gate(builder, theta_0, phi_0, lambda_0, qubit)


PYQIR_ONE_QUBIT_OP_MAP = {
    "id": id_gate,
    "h": pyqir._native.h,
    "x": pyqir._native.x,
    "y": pyqir._native.y,
    "z": pyqir._native.z,
    "s": pyqir._native.s,
    "t": pyqir._native.t,
    "sdg": pyqir._native.s_adj,
    "si": pyqir._native.s_adj,
    "tdg": pyqir._native.t_adj,
    "ti": pyqir._native.t_adj,
    "v": sx_gate,
    "sx": sx_gate,
    "vi": sxdg_gate,
    "sxdg": sxdg_gate,
}

PYQIR_ONE_QUBIT_ROTATION_MAP = {
    "rx": pyqir._native.rx,
    "ry": pyqir._native.ry,
    "rz": pyqir._native.rz,
    "u": u3_gate,
    "U": u3_gate,
    "u3": u3_gate,
    "U3": u3_gate,
    "U2": u2_gate,
    "u2": u2_gate,
    "prx": prx_gate,
    "phaseshift": phaseshift_gate,
    "p": phaseshift_gate,
    "gpi": gpi_gate,
    "gpi2": gpi2_gate,
}

PYQIR_TWO_QUBIT_OP_MAP = {
    "cx": pyqir._native.cx,
    "CX": pyqir._native.cx,
    "cnot": pyqir._native.cx,
    "cz": pyqir._native.cz,
    "swap": pyqir._native.swap,
    "cv": cv_gate,
    "cy": cy_gate,
    "xx": xx_gate,
    "xy": xy_gate,
    "yy": yy_gate,
    "zz": zz_gate,
    "pswap": pswap_gate,
    "cp": cphaseshift_gate,
    "cphaseshift": cphaseshift_gate,
    "cp00": cphaseshift00_gate,
    "cphaseshift00": cphaseshift00_gate,
    "cp01": cphaseshift01_gate,
    "cphaseshift01": cphaseshift01_gate,
    "cp10": cphaseshift10_gate,
    "cphaseshift10": cphaseshift10_gate,
    "ecr": ecr_gate,
    "ms": ms_gate,
}

PYQIR_THREE_QUBIT_OP_MAP = {
    "ccx": pyqir._native.ccx,
    "ccnot": pyqir._native.ccx,
    "cswap": cswap_gate,
}


def map_qasm_op_to_pyqir_callable(op_name: str) -> tuple[Callable, int]:
    """
    Map a QASM operation to a PyQIR callable.

    Args:
        op_name (str): The QASM operation name.

    Returns:
        tuple: A tuple containing the PyQIR callable and the number of qubits the operation acts on.

    Raises:
        Qasm3ConversionError: If the QASM operation is unsupported or undeclared.
    """
    qasm_op_mappings: list[tuple[dict, int]] = [
        (PYQIR_ONE_QUBIT_OP_MAP, 1),
        (PYQIR_ONE_QUBIT_ROTATION_MAP, 1),
        (PYQIR_TWO_QUBIT_OP_MAP, 2),
        (PYQIR_THREE_QUBIT_OP_MAP, 3),
    ]

    for mapping, qubits in qasm_op_mappings:
        if op_name in mapping:
            return mapping[op_name], qubits

    raise Qasm3ConversionError(f"Unsupported / undeclared QASM operation: {op_name}")


CONSTANTS_MAP = {
    "π": 3.141592653589793,
    "pi": 3.141592653589793,
    "ℇ": 2.718281828459045,
    "euler": 2.718281828459045,
    "τ": 6.283185307179586,
    "tau": 6.283185307179586,
}
