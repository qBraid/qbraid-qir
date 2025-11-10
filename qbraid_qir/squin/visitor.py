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
import re
import struct
from dataclasses import dataclass, field
from plistlib import InvalidFileException
from typing import Any

import pyqir
from bloqade import qubit
from bloqade.squin import gate, kernel, qalloc
from kirin import ir, lowering, types
from kirin.dialects import func, ilist, py
from kirin.rewrite import CFGCompactify, Walk

from qbraid_qir.exceptions import InvalidSquinInput


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
    elif isinstance(module, pyqir.Module):
        # Already a valid PyQIR module, no conversion needed
        pass

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

    # NOTE: add _self as argument; need to know signature before so do it after lowering
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
        mod=None,
        py_func=None,
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

    def extract_gates_from_module_functions(self, module):
        """
        Extract gate information by directly accessing PyQIR function instructions.

        Args:
            module: PyQIR module object

        Returns:
            list: List of dictionaries containing gate information with name, qubit_indices, and parameters
        """
        gates = []

        # Find the entry point function
        entry_func = None
        for func in module.functions:
            if pyqir.is_entry_point(func):
                entry_func = func
                break

        if not entry_func:
            return gates

        # Process each basic block in the entry function
        for block in entry_func.basic_blocks:
            for instruction in block.instructions:
                # Check if this is a quantum instruction call
                if hasattr(instruction, "callee") and instruction.callee:
                    callee_name = str(instruction.callee)

                    # Extract gate name from quantum instruction calls
                    if "__quantum__qis__" in callee_name and "__body" in callee_name:
                        gate_name = callee_name.split("__quantum__qis__")[1].split("__body")[0]

                        # Extract operands
                        qubit_indices = []
                        cbit_indices = []
                        parameters = []

                        for operand in instruction.operands:
                            operand_str = str(operand)

                            # Extract qubit indices
                            if "inttoptr" in operand_str and "Qubit" in operand_str:
                                # Extract the integer value
                                import re

                                match = re.search(
                                    r"inttoptr \(i64 (\d+) to %Qubit\*\)", operand_str
                                )
                                if match:
                                    qubit_indices.append(int(match.group(1)))
                                elif "null" in operand_str:
                                    qubit_indices.append(0)

                            # Extract classical bit indices
                            elif "inttoptr" in operand_str and "Result" in operand_str:
                                match = re.search(
                                    r"inttoptr \(i64 (\d+) to %Result\*\)", operand_str
                                )
                                if match:
                                    cbit_indices.append(int(match.group(1)))
                                elif "null" in operand_str:
                                    cbit_indices.append(0)

                            # Extract parameters (double values)
                            elif "double" in operand_str:
                                match = re.search(r"double ([0-9.e+-]+)", operand_str)
                                if match:
                                    parameters.append(float(match.group(1)))
                                else:
                                    # Handle hex double values
                                    hex_match = re.search(r"double 0x([0-9a-fA-F]+)", operand_str)
                                    if hex_match:
                                        try:
                                            int_val = int(hex_match.group(1), 16)
                                            float_val = struct.unpack(
                                                "d", struct.pack("Q", int_val)
                                            )[0]
                                            parameters.append(float_val)
                                        except:
                                            parameters.append(f"0x{hex_match.group(1)}")

                        gate_info = {
                            "gate_name": gate_name,
                            "qubit_indices": qubit_indices,
                            "cbit_indices": cbit_indices,
                            "parameters": parameters,
                        }

                        gates.append(gate_info)

        return gates

    def get_num_qubits(self, module):
        """
        Extract the number of qubits from the pyqir module.

        Args:
            module: PyQIR module object

        Returns:
            int: Number of qubits
        """
        # Find the entry point function
        entry_func = None
        for func in module.functions:
            if pyqir.is_entry_point(func):
                entry_func = func
                break

        if not entry_func:
            return 0

        # Get the required number of qubits and results (classical bits)
        qubits = pyqir.required_num_qubits(entry_func)
        num_cbits = pyqir.required_num_results(entry_func)

        return qubits

    def get_gate_operation(self, instruction: pyqir.Instruction):
        str_instruction = str(instruction)
        if "call void @__quantum__qis__" in str_instruction and "__body(" in str_instruction:
            gate_match = re.search(r"@__quantum__qis__(\w+)__body", str_instruction)
            if gate_match:
                gate_name = gate_match.group(1)
                return gate_name
        elif "call void @__quantum__qis__" in str_instruction and "__adj(" in str_instruction:
            gate_match = re.search(r"@__quantum__qis__(\w+)__adj", str_instruction)
            if gate_match:
                gate_name = gate_match.group(1)
                return gate_name + "__adj"
        elif "call void @__quantum__rt__" in str_instruction:
            return "rt"

    def lower_qubit_getindex(self, state: lowering.State[pyqir.Module], qid: int):
        index = qid
        index_ssa = state.current_frame.push(py.Constant(index)).result
        qbit_getitem = state.current_frame.push(py.GetItem(self.qreg, index_ssa))
        return qbit_getitem.result

    def lower_qubit_getindices(self, state: lowering.State[pyqir.Module], qids: list[int]):
        qbits_getitem = [self.lower_qubit_getindex(state, qid) for qid in qids]
        qbits = state.current_frame.push(ilist.New(values=qbits_getitem))
        return qbits.result

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

            # NOTE: need a register of qubits before lowering statements
            if register_as_argument:
                # NOTE: register as argument to the kernel; we have freedom of choice for the name here
                frame.curr_block.args.append_from(
                    ilist.IListType[qubit.QubitType, types.Any],
                    name=register_argument_name,
                )
                self.qreg = frame.curr_block.args[0]
            else:
                # NOTE: create a new register of appropriate size
                self.num_qubits = self.get_num_qubits(module)
                n = frame.push(py.Constant(self.num_qubits))
                self.qreg = frame.push(func.Invoke((n.result,), callee=qalloc, kwargs=())).result

            self.visit(state, module)

            if compactify:
                Walk(CFGCompactify()).rewrite(frame.curr_region)

            region = frame.curr_region

        return region

    def visit(self, state: lowering.State[pyqir.Module], node: pyqir.Module) -> lowering.Result:
        name = node.__class__.__name__
        return getattr(self, f"visit_{name}", self.generic_visit)(state, node)

    def generic_visit(
        self, state: lowering.State[pyqir.Module], node: pyqir.Module | pyqir.Function
    ):
        if isinstance(node, (pyqir.Function, pyqir.Module)):
            raise lowering.BuildError(f"Cannot lower {node.__class__.__name__} node: {node}")
        raise lowering.BuildError(f"Cannot lower {node}")

    def lower_literal(self, state: lowering.State[pyqir.Module], value) -> ir.SSAValue:
        raise lowering.BuildError("Literals not supported in pyqir module")

    def lower_global(
        self, state: lowering.State[pyqir.Module], node: pyqir.Module
    ) -> lowering.LoweringABC.Result:
        raise lowering.BuildError("Globals not supported in pyqir module")

    def measure_all_qubits(self, state: lowering.State[pyqir.Module]):
        m_qargs = self.lower_qubit_getindices(state, self.measurements)
        state.current_frame.push(qubit.stmts.Measure(m_qargs))
        self.measurements.clear()

    def visit_Module(
        self, state: lowering.State[pyqir.Module], node: pyqir.Module
    ) -> lowering.Result:
        return self.visit_Function(state, node)

    def visit_Function(
        self, state: lowering.State[pyqir.Module], node: pyqir.Module
    ) -> lowering.Result:
        for fun in node.functions:
            if pyqir.is_entry_point(fun):
                for block in fun.basic_blocks:
                    for instruction in block.instructions:
                        if isinstance(instruction, pyqir.Call):
                            self.visit_gate_operation(state, instruction)
                    if len(self.measurements) > 0:
                        self.measure_all_qubits(state)

    def visit_gate_operation(self, state: lowering.State[pyqir.Module], node: pyqir.Instruction):
        gate_name = self.get_gate_operation(node)
        if gate_name != "mz" and len(self.measurements) > 0:
            self.measure_all_qubits(state)
        if gate_name == "rt":
            return None
        return getattr(self, f"visit_{gate_name}", self.generic_visit)(state, node)

    def extract_qubit_indices(self, args_str: str) -> list[int]:
        """Extract qubit indices from PyQIR instruction arguments string."""
        qubit_indices = []
        # Handle null qubits (which represent qubit 0)
        null_qubit_count = args_str.count("%Qubit* null")
        for _ in range(null_qubit_count):
            qubit_indices.append(0)

        # Extract explicit qubit indices
        qubit_pattern = r"%Qubit\* inttoptr \(i64 (\d+) to %Qubit\*\)"
        qubit_matches = re.findall(qubit_pattern, args_str)
        if qubit_matches:
            qubit_indices.extend([int(idx) for idx in qubit_matches])

        return qubit_indices

    def extract_cbit_indices(self, args_str: str) -> list[int]:
        """Extract classical bit indices from PyQIR instruction arguments string."""
        cbit_indices = []
        # Handle null results (which represent result 0)
        null_result_count = args_str.count("%Result* null")
        for _ in range(null_result_count):
            cbit_indices.append(0)

        # Extract explicit result indices
        cbit_pattern = r"%Result\* inttoptr \(i64 (\d+) to %Result\*\)"
        cbit_matches = re.findall(cbit_pattern, args_str)
        if cbit_matches:
            cbit_indices.extend([int(idx) for idx in cbit_matches])

        return cbit_indices

    def extract_args_string(self, node: pyqir.Instruction) -> str:
        """Extract the arguments string from a PyQIR instruction."""
        str_node = str(node)
        args_match = re.search(r"__body\s*\((.*)\)", str_node)
        if not args_match:
            args_match = re.search(r"__adj\s*\((.*)\)", str_node)
        return args_match.group(1) if args_match else ""

    def extract_parameter(self, args_str: str) -> float:
        """Extract the parameter from the PyQIR instruction arguments string."""
        num = 0.0
        hex_parameter_match = re.search(r"double\s+0x([^\s,)\]]+)", args_str)
        float_parameter_match = re.search(r"double\s+(?!0x)([^\s,)\]]+)", args_str)
        if hex_parameter_match:
            num = int(hex_parameter_match.group(1), 16)
            num = struct.unpack("d", struct.pack("Q", num))[0]
        elif float_parameter_match:
            num = float(float_parameter_match.group(1))
        return num

    def visit_single_qubit_gate(
        self, state: lowering.State[pyqir.Module], node: pyqir.Instruction, gate_name: str
    ):
        args_str = self.extract_args_string(node)
        qubit_indices = self.extract_qubit_indices(args_str)
        qargs = self.lower_qubit_getindices(state, qubit_indices)
        return qargs

    def visit_h(self, state: lowering.State[pyqir.Module], node: pyqir.Instruction):
        qargs = self.visit_single_qubit_gate(state, node, "h")
        return state.current_frame.push(gate.stmts.H(qargs))

    def visit_x(self, state: lowering.State[pyqir.Module], node: pyqir.Instruction):
        qargs = self.visit_single_qubit_gate(state, node, "x")
        return state.current_frame.push(gate.stmts.X(qargs))

    def visit_y(self, state: lowering.State[pyqir.Module], node: pyqir.Instruction):
        qargs = self.visit_single_qubit_gate(state, node, "y")
        return state.current_frame.push(gate.stmts.Y(qargs))

    def visit_z(self, state: lowering.State[pyqir.Module], node: pyqir.Instruction):
        qargs = self.visit_single_qubit_gate(state, node, "z")
        return state.current_frame.push(gate.stmts.Z(qargs))

    def visit_s(self, state: lowering.State[pyqir.Module], node: pyqir.Instruction):
        qargs = self.visit_single_qubit_gate(state, node, "s")
        return state.current_frame.push(gate.stmts.S(qargs))

    def visit_t(self, state: lowering.State[pyqir.Module], node: pyqir.Instruction):
        qargs = self.visit_single_qubit_gate(state, node, "t")
        return state.current_frame.push(gate.stmts.T(qargs))

    def visit_s__adj(self, state: lowering.State[pyqir.Module], node: pyqir.Instruction):
        qargs = self.visit_single_qubit_gate(state, node, "s__adj")
        return state.current_frame.push(gate.stmts.S(adjoint=True, qubits=qargs))

    def visit_t__adj(self, state: lowering.State[pyqir.Module], node: pyqir.Instruction):
        qargs = self.visit_single_qubit_gate(state, node, "t__adj")
        return state.current_frame.push(gate.stmts.T(adjoint=True, qubits=qargs))

    def visit_two_qubit_gate(
        self, state: lowering.State[pyqir.Module], node: pyqir.Instruction, gate_name: str
    ):
        args_str = self.extract_args_string(node)
        split_args = args_str.split(",")

        # Extract control qubit (first argument)
        control_args = split_args[0].strip() if len(split_args) > 0 else ""
        control_qubit_indices = self.extract_qubit_indices(control_args)
        control_qargs = self.lower_qubit_getindices(state, control_qubit_indices)

        # Extract target qubit (second argument)
        target_args = split_args[1].strip() if len(split_args) > 1 else ""
        target_qubit_indices = self.extract_qubit_indices(target_args)
        target_qargs = self.lower_qubit_getindices(state, target_qubit_indices)

        return control_qargs, target_qargs

    def visit_cnot(self, state: lowering.State[pyqir.Module], node: pyqir.Instruction):
        control_qargs, target_qargs = self.visit_two_qubit_gate(state, node, "cnot")
        return state.current_frame.push(gate.stmts.CX(control_qargs, target_qargs))

    def visit_cz(self, state: lowering.State[pyqir.Module], node: pyqir.Instruction):
        control_qargs, target_qargs = self.visit_two_qubit_gate(state, node, "cz")
        return state.current_frame.push(gate.stmts.CZ(control_qargs, target_qargs))

    def visit_single_qubit_rotation(
        self, state: lowering.State[pyqir.Module], node: pyqir.Instruction, gate_name: str
    ):
        args_str = self.extract_args_string(node)
        split_args = args_str.split(",")

        # Extract parameter (first argument)
        parameter = self.extract_parameter(split_args[0].strip() if len(split_args) > 0 else "")

        # Extract qubit (second argument)
        qubit_args = split_args[1].strip() if len(split_args) > 1 else ""
        qubit_indices = self.extract_qubit_indices(qubit_args)

        qargs = self.lower_qubit_getindices(state, qubit_indices)

        return qargs, parameter

    def visit_rx(self, state: lowering.State[pyqir.Module], node: pyqir.Instruction):
        qargs, parameter = self.visit_single_qubit_rotation(state, node, "rx")
        angle = state.current_frame.push(py.Constant(value=parameter))
        return state.current_frame.push(gate.stmts.Rx(angle=angle.result, qubits=qargs))

    def visit_ry(self, state: lowering.State[pyqir.Module], node: pyqir.Instruction):
        qargs, parameter = self.visit_single_qubit_rotation(state, node, "ry")
        angle = state.current_frame.push(py.Constant(value=parameter))
        return state.current_frame.push(gate.stmts.Ry(angle=angle.result, qubits=qargs))

    def visit_rz(self, state: lowering.State[pyqir.Module], node: pyqir.Instruction):
        qargs, parameter = self.visit_single_qubit_rotation(state, node, "rz")
        angle = state.current_frame.push(py.Constant(value=parameter))
        return state.current_frame.push(gate.stmts.Rz(angle=angle.result, qubits=qargs))

    def visit_mz(self, state: lowering.State[pyqir.Module], node: pyqir.Instruction):
        args_str = self.extract_args_string(node)
        split_args = args_str.split(",")

        # Extract qubit (first argument)
        qubit_args = split_args[0].strip() if len(split_args) > 0 else ""
        qubit_indices = self.extract_qubit_indices(qubit_args)
        for q in qubit_indices:
            self.measurements.append(q)
        # qargs = self.lower_qubit_getindices(state, qubit_indices)
        # Extract classical bit (second argument)
        # cbit_args = split_args[1].strip() if len(split_args) > 1 else ""
        # cbit_indices = self.extract_cbit_indices(cbit_args)
        # return state.current_frame.push(qubit.stmts.Measure(qargs))
