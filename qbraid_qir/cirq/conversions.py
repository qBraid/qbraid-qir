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
import hashlib
from typing import Optional

import cirq

from qbraid_qir.exceptions import QirConversionError


def generate_module_id(circuit: cirq.Circuit) -> str:
    """
    Generates a QIR module ID from a given Cirq circuit.

    This function serializes the Cirq circuit into a JSON string, computes its SHA-256 hash, and then converts
    the hash into an alphanumeric string. The final name is a truncated version of this alphanumeric string,
    prefixed with 'circuit-', ensuring a concise and semi-unique identifier.

    Args:
        circuit (cirq.Circuit): The Cirq circuit for which a unique name is to be generated.

    Returns:
        str: Alphanumeric module ID for the Cirq circuit

    """
    serialized_circuit = cirq.to_json(circuit)
    hash_object = hashlib.sha256(serialized_circuit.encode())
    hash_hex = hash_object.hexdigest()
    alphanumeric_hash = "".join(filter(str.isalnum, hash_hex))
    truncated_hash = alphanumeric_hash[:7]
    return f"circuit-{truncated_hash}"


# Example: https://github.com/qir-alliance/pyqir/blob/main/examples/mock_to_qir.py
def cirq_to_qir(
    circuit: cirq.Circuit, output_file: Optional[str] = None, name: Optional[str] = None
) -> Optional[str]:
    """Converts a Cirq circuit to QIR code.

    Args:
        circuit (cirq.Circuit): The Cirq circuit to convert.
        output_file (str, optional): The output file to write the QIR code to. Defaults to None.
        name (str, optional): The name of the QIR function. Defaults to None.

    Returns:
        str: The QIR code.

    Raises:
        TypeError: If the input is not a Cirq circuit.
        QirConversionError: If the conversion fails.
    """
    if not isinstance(circuit, cirq.Circuit):
        raise TypeError("Input quantum program must be of type cirq.Circuit.")

    if not name:
        name = generate_module_id(circuit)

    try:
        generated_qir = None  # TODO: Convert Cirq circuit to QIR code

        raise NotImplementedError
    except Exception as e:
        raise QirConversionError("Cirq") from e

    if output_file is not None:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(generated_qir)

        return None

    return generated_qir
