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
from typing import Optional

import numpy as np

import cirq
from pyqir import Context, Module, qir_module

from qbraid_qir.cirq.elements import CirqModule, generate_module_id
from qbraid_qir.cirq.visitor import BasicQisVisitor
from qbraid_qir.exceptions import QirConversionError
from qbraid_qir.cirq.opsets import CIRQ_GATES


def cirq_to_qir(circuit: cirq.Circuit, name: Optional[str] = None, **kwargs) -> Module:
    """
    Converts a Cirq circuit to a PyQIR module.

    Args:
        circuit (cirq.Circuit): The Cirq circuit to convert.
        name (str, optional): Identifier for created QIR module. Auto-generated if not provided.

    Returns:
        The QIR ``pyqir.Module`` representation of the input Cirq circuit.

    Raises:
        TypeError: If the input is not a Cirq circuit.
        QirConversionError: If the conversion fails.
    """
    if not isinstance(circuit, cirq.Circuit):
        raise TypeError("Input quantum program must be of type cirq.Circuit.")

    if name is None:
        name = generate_module_id(circuit)

    # create a variable for circuit.unitary that we will use to create assertions later
    input_unitary = circuit.unitary()
    
    # do some preprocessing here that ensures that the circuit is composed only of supported gates and operation:

    # for moment in circuit:
    #     for op in moment:
    
    
    # according to the gateset in CIRQ_GATES, perform gate decomposition;
    for moment in circuit:
        for op in moment:
            if op.gate in CIRQ_GATES:
                op.gate = CIRQ_GATES[op.gate]
                op.gate.validate_args(op.qubits)
            else:
                raise QirConversionError(f"Unsupported gate {op.gate} in circuit.")
    
    
    # ensure that input/output circuit.unitary() are equivalent.
    output_unitary = circuit.unitary()
    if not np.allclose(input_unitary, output_unitary):
        raise QirConversionError("Cirq circuit unitary changed during conversion.")


    llvm_module = qir_module(Context(), name)
    module = CirqModule.from_circuit(circuit, llvm_module)


    visitor = BasicQisVisitor(**kwargs)
    module.accept(visitor)

    err = llvm_module.verify()
    if err is not None:
        raise QirConversionError(err)
    return llvm_module
