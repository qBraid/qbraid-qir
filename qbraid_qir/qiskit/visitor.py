# Copyright 2026 qBraid
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

# pylint: disable=line-too-long
# Portions of this module are adapted from microsoft/qiskit-qir
# (https://github.com/microsoft/qiskit-qir), with modifications by qBraid.
# The original MIT license notice is reproduced in NOTICE.md.
# pylint: enable=line-too-long

"""
Module defining QiskitVisitor for QIR conversion.

"""

import logging
from abc import ABCMeta, abstractmethod
from typing import Union

import pyqir
from pyqir import (
    BasicBlock,
    Builder,
    Constant,
    IntType,
    PointerType,
    entry_point,
    qis,
    rt,
)
from qiskit import ClassicalRegister, QuantumRegister
from qiskit.circuit import Clbit, Qubit
from qiskit.circuit.instruction import Instruction

from qbraid_qir._pyqir_compat import pointer_id

from .elements import QiskitModule
from .exceptions import QiskitConversionError
from .maps import (
    NOOP_INSTRUCTIONS,
    PYQIR_MEASUREMENT_OP_MAP,
    PYQIR_ONE_QUBIT_OP_MAP,
    PYQIR_ONE_QUBIT_ROTATION_MAP,
    PYQIR_THREE_QUBIT_OP_MAP,
    PYQIR_TWO_QUBIT_OP_MAP,
    SUPPORTED_INSTRUCTIONS,
)

logger = logging.getLogger(__name__)


class QuantumCircuitElementVisitor(metaclass=ABCMeta):
    """Abstract base class for quantum circuit element visitors."""

    @abstractmethod
    def visit_register(self, register):
        """Visit a register element."""

    @abstractmethod
    def visit_instruction(self, instruction, qargs, cargs):
        """Visit an instruction element."""


class BasicQiskitVisitor(  # pylint: disable=too-many-instance-attributes
    QuantumCircuitElementVisitor
):
    """A visitor for basic Qiskit circuit elements.

    This class traverses and converts Qiskit circuit elements to QIR.

    Args:
        initialize_runtime: If True, quantum runtime will be initialized. Defaults to True.
        record_output: If True, output of the circuit will be recorded. Defaults to True.
        emit_barrier_calls: If True, barrier instructions will be emitted. Defaults to False.
    """

    def __init__(
        self,
        initialize_runtime: bool = True,
        record_output: bool = True,
        emit_barrier_calls: bool = False,
    ):
        self._module: pyqir.Module = None  # type: ignore[assignment]
        self._qiskit_module: QiskitModule | None = None
        self._builder: pyqir.Builder = None  # type: ignore[assignment]
        self._entry_point: str = ""
        self._qubit_labels: dict[Qubit, int] = {}
        self._clbit_labels: dict[Clbit, int] = {}
        self._measured_qubits: dict[int, bool] = {}
        self._initialize_runtime = initialize_runtime
        self._record_output = record_output
        self._emit_barrier_calls = emit_barrier_calls

    def visit_qiskit_module(self, module: QiskitModule) -> None:
        """Visit a QiskitModule and initialize the QIR builder.

        Args:
            module: The QiskitModule to visit.
        """
        logger.debug(
            "Visiting Qiskit module '%s' (%d qubits, %d clbits)",
            module.name,
            module.num_qubits,
            module.num_clbits,
        )
        self._qubit_labels.clear()
        self._clbit_labels.clear()
        self._measured_qubits.clear()

        if module.module is None:
            raise ValueError("QiskitModule must have a PyQIR module set before visiting.")
        self._module = module.module
        self._qiskit_module = module
        context = self._module.context
        entry = entry_point(self._module, module.name, module.num_qubits, module.num_clbits)

        self._entry_point = entry.name
        self._builder = Builder(context)
        self._builder.insert_at_end(BasicBlock(context, "entry", entry))

        if self._initialize_runtime:
            i8p = PointerType(IntType(context, 8))
            nullptr = Constant.null(i8p)
            rt.initialize(self._builder, nullptr)

    @property
    def entry_point(self) -> str:
        """Return the entry point name."""
        return self._entry_point

    def _check_initialized(self) -> None:
        """Raise if the visitor has not been initialized via visit_qiskit_module."""
        if self._module is None or self._builder is None:
            raise RuntimeError(
                "Visitor has not been initialized. Call visit_qiskit_module() first."
            )

    def finalize(self) -> None:
        """Finalize the QIR module by adding a return instruction."""
        self._check_initialized()
        self._builder.ret(None)

    def record_output(self, module: QiskitModule) -> None:
        """Record output for classical registers.

        Args:
            module: The QiskitModule containing register information.
        """
        if not self._record_output:
            return
        self._check_initialized()

        i8p = PointerType(IntType(self._module.context, 8))

        # Qiskit inverts the ordering of results within each register
        # but keeps the overall register ordering
        logical_id_base = 0
        for size in module.reg_sizes:
            rt.array_record_output(
                self._builder,
                pyqir.const(IntType(self._module.context, 64), size),
                Constant.null(i8p),
            )
            for index in range(size - 1, -1, -1):
                result_ref = pyqir.result(self._module.context, logical_id_base + index)
                rt.result_record_output(self._builder, result_ref, Constant.null(i8p))
            logical_id_base += size

    def visit_register(self, register: Union[QuantumRegister, ClassicalRegister]) -> None:
        """Visit a register and assign labels to its bits.

        Args:
            register: The quantum or classical register to visit.
        """
        logger.debug("Visiting register '%s'", register.name)
        if isinstance(register, QuantumRegister):
            self._qubit_labels.update(
                {bit: n + len(self._qubit_labels) for n, bit in enumerate(register)}
            )
            logger.debug("Added labels for qubits %s", list(register))
        elif isinstance(register, ClassicalRegister):
            self._clbit_labels.update(
                {bit: n + len(self._clbit_labels) for n, bit in enumerate(register)}
            )
        else:
            raise QiskitConversionError(f"Register of type {type(register)} not supported.")

    def _process_composite_instruction(
        self,
        instruction: Instruction,
        qargs: tuple[Qubit, ...],
        cargs: tuple[Clbit, ...],
    ) -> None:
        """Process a composite (decomposable) instruction.

        Args:
            instruction: The composite instruction.
            qargs: Qubit arguments.
            cargs: Classical bit arguments.
        """
        subcircuit = instruction.definition
        logger.debug(
            "Processing composite instruction %s with qubits %s",
            instruction.name,
            qargs,
        )

        if len(qargs) != subcircuit.num_qubits:
            raise QiskitConversionError(
                f"Composite instruction {instruction.name} called with wrong number of qubits; "
                f"{subcircuit.num_qubits} expected, {len(qargs)} provided"
            )
        if len(cargs) != subcircuit.num_clbits:
            raise QiskitConversionError(
                f"Composite instruction {instruction.name} called with wrong number of clbits; "
                f"{subcircuit.num_clbits} expected, {len(cargs)} provided"
            )

        # Process sub-instructions with mapped bits
        for circuit_instruction in subcircuit.data:
            inst = circuit_instruction.operation
            i_qargs = circuit_instruction.qubits
            i_cargs = circuit_instruction.clbits
            mapped_qbits = tuple(qargs[subcircuit.qubits.index(i)] for i in i_qargs)
            mapped_clbits = tuple(cargs[subcircuit.clbits.index(i)] for i in i_cargs)
            logger.debug(
                "Processing sub-instruction %s with mapped qubits %s",
                inst.name,
                mapped_qbits,
            )
            self.visit_instruction(inst, mapped_qbits, mapped_clbits)

    def visit_instruction(
        self,
        instruction: Instruction,
        qargs: tuple[Qubit, ...],
        cargs: tuple[Clbit, ...],
    ) -> None:
        """Visit and convert an instruction to QIR.

        Args:
            instruction: The instruction to visit.
            qargs: Qubit arguments.
            cargs: Classical bit arguments.
        """
        qlabels = [self._qubit_labels[bit] for bit in qargs]
        clabels = [self._clbit_labels[bit] for bit in cargs]
        qubits = [pyqir.qubit(self._module.context, n) for n in qlabels]
        results = [pyqir.result(self._module.context, n) for n in clabels]

        labels_str = ", ".join([str(label) for label in qlabels + clabels])
        logger.debug("Visiting instruction '%s' (%s)", instruction.name, labels_str)

        op_name = instruction.name.lower()

        if op_name in NOOP_INSTRUCTIONS:
            return

        if op_name in PYQIR_MEASUREMENT_OP_MAP:
            for qubit, result in zip(qubits, results, strict=True):
                qubit_id = pointer_id(qubit)
                if qubit_id is not None:
                    self._measured_qubits[qubit_id] = True
                qis.mz(self._builder, qubit, result)
        elif op_name == "barrier":
            if self._emit_barrier_calls:
                qis.barrier(self._builder)
        elif op_name in PYQIR_ONE_QUBIT_OP_MAP:
            PYQIR_ONE_QUBIT_OP_MAP[op_name](self._builder, qubits[0])
        elif op_name in PYQIR_ONE_QUBIT_ROTATION_MAP:
            PYQIR_ONE_QUBIT_ROTATION_MAP[op_name](
                self._builder, float(instruction.params[0]), qubits[0]
            )
        elif op_name in PYQIR_TWO_QUBIT_OP_MAP:
            PYQIR_TWO_QUBIT_OP_MAP[op_name](self._builder, qubits[0], qubits[1])
        elif op_name in PYQIR_THREE_QUBIT_OP_MAP:
            PYQIR_THREE_QUBIT_OP_MAP[op_name](self._builder, *qubits)
        elif instruction.definition is not None:
            self._process_composite_instruction(instruction, qargs, cargs)
        else:
            raise QiskitConversionError(
                f"Gate '{instruction.name}' is not supported. "
                f"Please transpile using supported gates: {SUPPORTED_INSTRUCTIONS}"
            )

    def ir(self) -> str:
        """Return the QIR as a string."""
        self._check_initialized()
        return str(self._module)

    def bitcode(self) -> bytes:
        """Return the QIR as bitcode."""
        self._check_initialized()
        return self._module.bitcode
