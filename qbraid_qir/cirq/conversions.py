# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module containing Cirq to qBraid QIR conversion functions

"""
import cirq

from qbraid_qir.exceptions import QirConversionError


def cirq_to_qir(circuit: cirq.Circuit) -> str:
    """Converts a Cirq circuit to QIR code.

    Args:
        circuit (cirq.Circuit): The Cirq circuit to convert.

    Returns:
        str: The QIR code.

    Raises:
        TypeError: If the input is not a Cirq circuit.
        QirConversionError: If the conversion fails.
    """
    if not isinstance(circuit, cirq.Circuit):
        raise TypeError("Input quantum program must be of type cirq.Circuit.")

    try:
        raise NotImplementedError
    except Exception as e:
        raise QirConversionError("Failed to convert Cirq circuit to QIR code.") from e
