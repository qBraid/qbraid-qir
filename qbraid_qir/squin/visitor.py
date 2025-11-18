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

# pylint: disable-all
# type: ignore

import os
from dataclasses import dataclass, field
from plistlib import InvalidFileException
from typing import Any

import numpy as np
import pyqir
from bloqade import qubit
from bloqade.squin import gate, kernel, qalloc
from kirin import ir, lowering, types
from kirin.dialects import func, ilist, py
from kirin.rewrite import CFGCompactify, Walk

from qbraid_qir.qasm3.maps import (
    PYQIR_MEASUREMENT_OP_MAP,
    PYQIR_ONE_QUBIT_OP_MAP,
    PYQIR_ONE_QUBIT_ROTATION_MAP,
    PYQIR_TWO_QUBIT_OP_MAP,
)

from .exceptions import InvalidSquinInput

# Combined map for efficient gate lookup
PYQIR_ALL_GATES_MAP = {
    **PYQIR_ONE_QUBIT_OP_MAP,
    **PYQIR_ONE_QUBIT_ROTATION_MAP,
    **PYQIR_TWO_QUBIT_OP_MAP,
    **PYQIR_MEASUREMENT_OP_MAP,
}


def load(
    module: str | pyqir.Module,
    **kwargs,
):
    """Converts a PyQIR module into a squin kernel.

    Args:
        module (str | pyqir.Module): PyQIR code or path to the .ll or .bc file, or a PyQIR Module object.

    Keyword Args:
        kernel_name (str): The name of the kernel to load. Defaults to "main".
        dialects (ir.DialectGroup): The dialects to use. Defaults to `squin.kernel`.
        register_as_argument (bool): Determine whether the resulting kernel function should accept
            a single `ilist.IList[Qubit, Any]` argument that is a list of qubits used within the
            function. This allows you to compose kernel functions generated from circuits.
            Defaults to `False`.
        return_register (bool): Determine whether the resulting kernel function returns a
            single value of type `ilist.IList[Qubit, Any]` that is the list of qubits used
            in the kernel function. Useful when you want to compose multiple kernel functions
            generated from circuits. Defaults to `False`.
        register_argument_name (str): The name of the argument that represents the qubit register.
            Only used when `register_as_argument=True`. Defaults to "q".
        globals (dict[str, Any] | None): The global variables to use. Defaults to None.
        file (str | None): The file name for error reporting. Defaults to None.
        lineno_offset (int): The line number offset for error reporting. Defaults to 0.
        col_offset (int): The column number offset for error reporting. Defaults to 0.
        compactify (bool): Whether to compactify the output. Defaults to True.

    """

    # Extract parameters from kwargs with defaults
    kernel_name: str = kwargs.pop("kernel_name", "main")
    dialects: ir.DialectGroup = kwargs.pop("dialects", kernel)
    register_as_argument: bool = kwargs.pop("register_as_argument", False)
    return_register: bool = kwargs.pop("return_register", False)
    register_argument_name: str = kwargs.pop("register_argument_name", "q")
    globals: dict[str, Any] | None = kwargs.pop("globals", None)
    file: str | None = kwargs.pop("file", None)
    lineno_offset: int = kwargs.pop("lineno_offset", 0)
    col_offset: int = kwargs.pop("col_offset", 0)
    compactify: bool = kwargs.pop("compactify", True)

    # Raise error if unexpected kwargs are provided
    if kwargs:
        unexpected = ", ".join(f"'{k}'" for k in kwargs.keys())
        raise TypeError(f"load() got unexpected keyword argument(s): {unexpected}")

    # Validate input type at the start
    if not isinstance(module, (str, pyqir.Module)):
        raise InvalidSquinInput(f"Invalid input {type(module)}, expected 'str | pyqir.Module'")

    # If module is a string, interpret as path to a file (.ll or .bc for QIR IR/bitcode)
    # or as QIR IR text that can be parsed
    if isinstance(module, str):
        if os.path.exists(module):
            _, ext = os.path.splitext(module)
            if ext.lower() == ".ll":
                # Load LLVM IR (text) file as a PyQIR module
                with open(module, "r", encoding="utf-8") as f:
                    ir_text = f.read()
                module = pyqir.Module.from_ir(ir_text)
            elif ext.lower() == ".bc":
                # Load LLVM bitcode as a PyQIR module
                with open(module, "rb") as f:
                    bitcode_bytes = f.read()
                module = pyqir.Module.from_bitcode(bitcode_bytes)
            else:
                raise InvalidFileException(f"Expected file extension .ll or .bc but got {ext!r}")
        else:
            # Try to parse string as QIR IR text
            try:
                module = pyqir.Module.from_ir(pyqir.Context(), module, name=kernel_name)
            except Exception as exc:
                raise InvalidSquinInput(
                    f"Invalid input {type(module)}, expected 'str | pyqir.Module'. "
                    f"String must be a valid file path (.ll or .bc) or valid QIR IR text."
                ) from exc
    elif not isinstance(module, pyqir.Module):
        raise InvalidSquinInput(f"Invalid input {type(module)}, expected 'pyqir.Module'")

    target = SquinVisitor(dialects=dialects, module=module)
    body = target.run(
        module,
        file=file,
        globals=globals,
        lineno_offset=lineno_offset,
        col_offset=col_offset,
        compactify=compactify,
        register_as_argument=register_as_argument,
        register_argument_name=register_argument_name,
    )

    if return_register:
        return_value = target.qreg
    else:
        return_value = func.ConstantNone()
        body.blocks[0].stmts.append(return_value)

    return_node = func.Return(value_or_stmt=return_value)
    body.blocks[0].stmts.append(return_node)

    self_arg_name = kernel_name + "_self"
    arg_names = [self_arg_name]
    if register_as_argument:
        args = (target.qreg.type,)
        arg_names.append(register_argument_name)
    else:
        args = ()

    signature = func.Signature(args, return_node.value.type)
    body.blocks[0].args.insert_from(
        0,
        types.Generic(ir.Method, types.Tuple.where(signature.inputs), signature.output),
        self_arg_name,
    )

    code = func.Function(
        sym_name=kernel_name,
        signature=signature,
        body=body,
    )

    mt = ir.Method(
        sym_name=kernel_name,
        arg_names=arg_names,
        dialects=dialects,
        code=code,
    )

    assert (run_pass := kernel.run_pass) is not None
    run_pass(mt, typeinfer=True)

    return mt


@dataclass
class SquinVisitor(lowering.LoweringABC[pyqir.Module]):
    """convert a pyqir module to a squin kernel"""

    module: pyqir.Module
    qreg: ir.SSAValue = field(init=False)
    num_qubits: int = field(init=False)
    measurements: list[int] = field(default_factory=list, init=False)

    def lower_qubit_getindex(self, state: lowering.State[pyqir.Module], qid: int):
        index = qid
        index_ssa = state.current_frame.push(py.Constant(index)).result
        qbit_getitem = state.current_frame.push(py.GetItem(self.qreg, index_ssa))
        return qbit_getitem.result

    def lower_qubit_getindices(self, state: lowering.State[pyqir.Module], qids: list[int]):
        qbits_getitem = [self.lower_qubit_getindex(state, qid) for qid in qids]
        qbits = state.current_frame.push(ilist.New(values=qbits_getitem))
        return qbits.result

    def lower_literal(self, state: lowering.State[pyqir.Module], value) -> ir.SSAValue:
        raise lowering.BuildError("Literals not supported in pyqir module")

    def lower_global(
        self, state: lowering.State[pyqir.Module], node: pyqir.Module
    ) -> lowering.LoweringABC.Result:
        raise lowering.BuildError("Globals not supported in pyqir module")

    def run(
        self,
        module: pyqir.Module,
        *,
        globals: dict[str, Any] | None = None,
        file: str | None = None,
        lineno_offset: int = 0,
        col_offset: int = 0,
        compactify: bool = True,
        register_as_argument: bool = False,
        register_argument_name: str = "q",
    ) -> ir.Region:

        state = lowering.State(
            self,
            file=file,
            lineno_offset=lineno_offset,
            col_offset=col_offset,
        )

        with state.frame([module], globals=globals, finalize_next=False) as frame:

            if register_as_argument:
                frame.curr_block.args.append_from(
                    ilist.IListType[qubit.QubitType, types.Any],
                    name=register_argument_name,
                )
                self.qreg = frame.curr_block.args[0]
            else:
                # NOTE: create a new register of appropriate size
                self.entry_point = next(filter(pyqir.is_entry_point, module.functions), None)
                if not self.entry_point:
                    raise InvalidSquinInput("No entry point found in pyqir module")
                self.num_qubits = pyqir.required_num_qubits(self.entry_point)
                n = frame.push(py.Constant(self.num_qubits))
                self.qreg = frame.push(func.Invoke((n.result,), callee=qalloc)).result

            self.visit_block(state, module)

            if compactify:
                Walk(CFGCompactify()).rewrite(frame.curr_region)

            region = frame.curr_region

        return region

    def visit_block(
        self, state: lowering.State[pyqir.Module], node: pyqir.Module
    ) -> lowering.Result:
        # There could be multiple basic blocks in the entry point
        for block in self.entry_point.basic_blocks:
            for instruction in block.instructions:
                self.visit_instruction(state, instruction)
            if len(self.measurements) > 0:
                self.visit_measurement_gate(state, self.measurements)
                self.measurements.clear()

    def visit_instruction(
        self, state: lowering.State[pyqir.Module], instruction: pyqir.Instruction
    ) -> lowering.Result:
        if isinstance(instruction, pyqir.Call):
            gate = instruction.callee.name.removeprefix("__quantum__qis__").removesuffix("__body")
            args = instruction.args
            if gate in PYQIR_ALL_GATES_MAP:
                return self.visit(state, gate, args)

    def visit(
        self, state: lowering.State[pyqir.Module], instruction: str, args: list[pyqir.Value]
    ) -> lowering.Result:
        if instruction not in PYQIR_MEASUREMENT_OP_MAP and len(self.measurements) > 0:
            self.visit_measurement_gate(state, self.measurements)
            self.measurements.clear()

        return getattr(self, f"visit_{instruction}")(state, args)

    # One qubit gate
    def visit_one_qubit_gate(
        self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]
    ) -> lowering.Result:
        qubit_indices = [0 if arg.is_null else pyqir.qubit_id(arg) for arg in args]
        qargs = self.lower_qubit_getindices(state, qubit_indices)
        return qargs

    def visit_h(self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]):
        qargs = self.visit_one_qubit_gate(state, args)
        return state.current_frame.push(gate.stmts.H(qargs))

    def visit_x(self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]):
        qargs = self.visit_one_qubit_gate(state, args)
        return state.current_frame.push(gate.stmts.X(qargs))

    def visit_y(self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]):
        qargs = self.visit_one_qubit_gate(state, args)
        return state.current_frame.push(gate.stmts.Y(qargs))

    def visit_z(self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]):
        qargs = self.visit_one_qubit_gate(state, args)
        return state.current_frame.push(gate.stmts.Z(qargs))

    def visit_s(self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]):
        qargs = self.visit_one_qubit_gate(state, args)
        return state.current_frame.push(gate.stmts.S(qargs))

    def visit_t(self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]):
        qargs = self.visit_one_qubit_gate(state, args)
        return state.current_frame.push(gate.stmts.T(qargs))

    def visit_s__adj(self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]):
        qargs = self.visit_one_qubit_gate(state, args)
        return state.current_frame.push(gate.stmts.S(adjoint=True, qubits=qargs))

    def visit_t__adj(self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]):
        qargs = self.visit_one_qubit_gate(state, args)
        return state.current_frame.push(gate.stmts.T(adjoint=True, qubits=qargs))

    # Two qubit gate
    def visit_two_qubit_gate(
        self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]
    ) -> lowering.Result:
        control_qubit_indices = [0 if args[0].is_null else pyqir.qubit_id(args[0])]
        target_qubit_indices = [0 if args[1].is_null else pyqir.qubit_id(args[1])]
        control_qargs = self.lower_qubit_getindices(state, control_qubit_indices)
        target_qargs = self.lower_qubit_getindices(state, target_qubit_indices)
        return control_qargs, target_qargs

    def visit_cnot(self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]):
        control_qargs, target_qargs = self.visit_two_qubit_gate(state, args)
        return state.current_frame.push(gate.stmts.CX(control_qargs, target_qargs))

    def visit_cz(self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]):
        control_qargs, target_qargs = self.visit_two_qubit_gate(state, args)
        return state.current_frame.push(gate.stmts.CZ(control_qargs, target_qargs))

    # One qubit rotation gate
    def visit_one_qubit_rotation_gate(
        self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]
    ) -> lowering.Result:
        parameter = args[0].value
        qubit_indices = [0 if args[1].is_null else pyqir.qubit_id(args[1])]
        qargs = self.lower_qubit_getindices(state, qubit_indices)
        return 0.5 * (parameter / np.pi), qargs

    def visit_rx(self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]):
        parameter, qargs = self.visit_one_qubit_rotation_gate(state, args)
        angle = state.current_frame.push(py.Constant(value=parameter))
        return state.current_frame.push(gate.stmts.Rx(angle=angle.result, qubits=qargs))

    def visit_ry(self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]):
        parameter, qargs = self.visit_one_qubit_rotation_gate(state, args)
        angle = state.current_frame.push(py.Constant(value=parameter))
        return state.current_frame.push(gate.stmts.Ry(angle=angle.result, qubits=qargs))

    def visit_rz(self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]):
        parameter, qargs = self.visit_one_qubit_rotation_gate(state, args)
        angle = state.current_frame.push(py.Constant(value=parameter))
        return state.current_frame.push(gate.stmts.Rz(angle=angle.result, qubits=qargs))

    # Measurement gate
    def visit_measurement_gate(
        self, state: lowering.State[pyqir.Module], qubit_indices: list[int]
    ) -> lowering.Result:
        qargs = self.lower_qubit_getindices(state, qubit_indices)
        state.current_frame.push(qubit.stmts.Measure(qargs))
        self.measurements.clear()

    def visit_mz(self, state: lowering.State[pyqir.Module], args: list[pyqir.Value]):
        qubit_indices = [0 if args[0].is_null else pyqir.qubit_id(args[0])]
        for q in qubit_indices:
            self.measurements.append(q)
