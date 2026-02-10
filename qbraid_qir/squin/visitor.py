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
This module contains the functionality to convert a PyQIR module into a squin kernel.
"""

from __future__ import annotations

import os
from plistlib import InvalidFileException
from typing import TYPE_CHECKING, Any, Callable, TypedDict

import pyqir
from bloqade import qubit

from qbraid_qir._pyqir_compat import pointer_id
from bloqade.squin import kernel
from kirin import ir, lowering, types
from kirin.dialects import func, ilist, py
from kirin.rewrite import CFGCompactify, Walk

from .exceptions import InvalidSquinInput
from .maps import PYQIR_TO_SQUIN_GATES_MAP, QIR_TO_SQUIN_UNSUPPORTED_STATEMENTS_MAP

if TYPE_CHECKING:
    from typing import Unpack


class LoadKwargs(TypedDict, total=False):
    """Type definition for keyword arguments to the load function."""

    kernel_name: str
    dialects: ir.DialectGroup
    register_as_argument: bool
    return_measurements: list[int] | None
    register_argument_name: str
    globals: dict[str, Any] | None
    file: str | None
    lineno_offset: int
    col_offset: int
    compactify: bool


# pylint: disable=too-many-locals, too-many-statements
def load(
    module: str | pyqir.Module,
    **kwargs: Unpack[LoadKwargs],
):
    """Converts a PyQIR module into a squin kernel.

    Args:
        module (str | pyqir.Module): PyQIR code or path to the .ll or .bc file,
                                     or a PyQIR Module object.

    Keyword Args:
        kernel_name (str): The name of the kernel to load. Defaults to "main".
        dialects (ir.DialectGroup): The dialects to use. Defaults to `squin.kernel`.
        register_as_argument (bool): Determine whether the resulting kernel function should accept
            a single `ilist.IList[Qubit, Any]` argument that is a list of qubits used within the
            function. This allows you to compose kernel functions generated from circuits.
            Defaults to `False`.
        return_measurements (list[int] | None): Which measured qubit results to return. Default:None
        register_argument_name (str): The name of the argument that represents the qubit register.
            Only used when `register_as_argument=True`. Defaults to "q".
        globals (dict[str, Any] | None): The global variables to use. Defaults to None.
        file (str | None): The file name for error reporting. Defaults to None.
        lineno_offset (int): The line number offset for error reporting. Defaults to 0.
        col_offset (int): The column number offset for error reporting. Defaults to 0.
        compactify (bool): Whether to compactify the output. Defaults to True.

    """

    kernel_name: str = kwargs.pop("kernel_name", "main")
    dialects: ir.DialectGroup = kwargs.pop("dialects", kernel)
    register_as_argument: bool = kwargs.pop("register_as_argument", False)
    # TODO:return_measurements: list[int] | None = kwargs.pop("return_measurements", None)
    register_argument_name: str = kwargs.pop("register_argument_name", "q")
    globals: dict[str, Any] | None = kwargs.pop(  # pylint: disable=redefined-builtin
        "globals", None
    )
    file: str | None = kwargs.pop("file", None)
    lineno_offset: int = kwargs.pop("lineno_offset", 0)
    col_offset: int = kwargs.pop("col_offset", 0)
    compactify: bool = kwargs.pop("compactify", True)

    if kwargs:
        unexpected = ", ".join(f"'{k}'" for k in kwargs)
        raise InvalidSquinInput(f"load() got unexpected keyword argument(s): {unexpected}")

    # Validate input type
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
                module = pyqir.Module.from_ir(pyqir.Context(), ir_text, name=kernel_name)
            elif ext.lower() == ".bc":
                # Load LLVM bitcode as a PyQIR module
                with open(module, "rb") as f:
                    bitcode_bytes = f.read()
                module = pyqir.Module.from_bitcode(pyqir.Context(), bitcode_bytes, name=kernel_name)
            else:
                raise InvalidFileException(f"Expected file extension .ll or .bc but got {ext!r}")
        else:
            # Try to parse string as QIR IR text
            try:
                module = pyqir.Module.from_ir(pyqir.Context(), module, name=kernel_name)
            except Exception as exc:
                raise InvalidSquinInput(
                    f"Invalid input {type(module)}, String must be a valid QIR IR text."
                ) from exc

    target = SquinVisitor(  # pylint: disable=unexpected-keyword-arg
        dialects=dialects, module=module
    )
    body = target.run(
        module,
        file=file,
        globals=globals,
        lineno_offset=lineno_offset,
        col_offset=col_offset,
        compactify=compactify,
        register_as_argument=register_as_argument,
        register_argument_name=register_argument_name,
        # TODO: return_measurements=return_measurements,
    )

    # TODO: Determine what to return based on return_measurements parameter
    # if return_measurements and len(return_measurements) > 0:
    #     # Return measurement results for specified qubits
    #     measurement_results = []
    #     for qid in return_measurements:
    #         # Validate qubit index is in range
    #         if qid < 0 or qid >= target.num_qubits:
    #             raise InvalidSquinInput(
    #                 f"Cannot return measurement for qubit {qid}: "
    #                 f"qubit index out of range [0, {target.num_qubits})"
    #             )
    #         # Check if qubit was measured
    #         if qid in target.measurement_results:
    #             measurement_results.append(target.measurement_results[qid])
    #         else:
    #             raise InvalidSquinInput(
    #                 f"Cannot return measurement for qubit {qid}: qubit was not measured"
    #             )

    #     if len(measurement_results) == 1:
    #         # Single measurement result - return directly
    #         return_value = measurement_results[0]
    #     else:
    #         # Multiple measurement results - create tuple (py.tuple.New requires tuple, not list)
    #         tuple_stmt = py.tuple.New(values=tuple(measurement_results))
    #         body.blocks[0].stmts.append(tuple_stmt)
    #         return_value = tuple_stmt.result
    # else:

    # Return None
    return_value = func.ConstantNone()
    body.blocks[0].stmts.append(return_value)

    return_node = func.Return(value_or_stmt=return_value)
    body.blocks[0].stmts.append(return_node)  # pylint: disable=no-member

    self_arg_name = kernel_name + "_self"
    arg_names = [self_arg_name]
    if register_as_argument:
        args = (target.qreg.type,)
        arg_names.append(register_argument_name)
        # Include argument name in slots so it appears in the printed signature
        slots = (register_argument_name,)
    else:
        args = ()  # type: ignore
        slots = ()  # type: ignore

    signature = func.Signature(args, return_node.value.type)
    body.blocks[0].args.insert_from(
        0,
        types.Generic(ir.Method, types.Tuple.where(signature.inputs), signature.output),
        self_arg_name,
    )

    # pylint: disable-next=unexpected-keyword-arg
    code = func.Function(
        sym_name=kernel_name,
        signature=signature,
        slots=slots,
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


class SquinVisitor(lowering.LoweringABC[pyqir.Module]):
    """convert a pyqir module to a squin kernel"""

    def __init__(self, dialects: ir.DialectGroup, module: pyqir.Module):
        """Initialize the SquinVisitor.

        Args:
            dialects: The dialects to use for lowering.
            module: The PyQIR module to convert.
        """
        super().__init__(dialects=dialects)
        self.module = module
        self.qreg: ir.SSAValue = None  # type: ignore
        self.num_qubits: int | None = None
        self.qubit_ssa_map: dict[int, ir.SSAValue] = {}
        self.visit_map: dict[
            type, Callable[[lowering.State[pyqir.Module], Any], lowering.Result]
        ] = {
            pyqir.Call: self.visit_call,
            pyqir.BasicBlock: self.visit_basic_block,
            pyqir.Constant: self.visit_constant,
            pyqir.FloatConstant: self.visit_constant,
            pyqir.IntConstant: self.visit_constant,
        }

    # Abstract/Required Methods
    def lower_literal(self, state: lowering.State[pyqir.Module], value) -> ir.SSAValue:
        raise lowering.BuildError("Literals not supported in pyqir module")

    def lower_global(
        self, state: lowering.State[pyqir.Module], node: pyqir.Module
    ) -> lowering.LoweringABC.Result:
        raise lowering.BuildError("Globals not supported in pyqir module")

    # pylint: disable-next=too-many-arguments
    def run(
        self,
        module: pyqir.Module,
        *,
        globals: dict[str, Any] | None = None,  # pylint: disable=redefined-builtin
        file: str | None = None,
        lineno_offset: int = 0,
        col_offset: int = 0,
        compactify: bool = True,
        register_as_argument: bool = False,
        register_argument_name: str = "q",
        # return_measurements: list[int] | None = None,
    ) -> ir.Region:
        """Run the visitor on a PyQIR module."""
        state = lowering.State(
            self,
            file=file,
            lineno_offset=lineno_offset,
            col_offset=col_offset,
        )

        with state.frame([module], globals=globals, finalize_next=False) as frame:

            self.entry_point = next(  # pylint: disable=attribute-defined-outside-init
                filter(pyqir.is_entry_point, module.functions), None
            )
            if self.entry_point is None:
                raise InvalidSquinInput("No entry point found in pyqir module")
            self.num_qubits = pyqir.required_num_qubits(self.entry_point)

            if self.num_qubits is None or self.num_qubits < 1:
                raise InvalidSquinInput(
                    f"Invalid number of qubits {self.num_qubits}, must be greater than 0"
                )

            if register_as_argument:
                frame.curr_block.args.append_from(
                    ilist.IListType[qubit.QubitType, types.Literal(self.num_qubits)],
                    name=register_argument_name,
                )
                self.qreg = frame.curr_block.args[0]
                # Extract individual qubit SSA values from the register and store in map
                for qid in range(self.num_qubits):
                    index_ssa = frame.push(py.Constant(qid)).result
                    qbit_getitem = frame.push(
                        py.GetItem(self.qreg, index_ssa)  # pylint: disable=too-many-function-args
                    )
                    self.qubit_ssa_map[qid] = qbit_getitem.result
            else:
                # Create individual qubits using qubit.new() and store SSA values directly in map
                for qid in range(self.num_qubits):
                    squin_qubit = frame.push(
                        func.Invoke(  # pylint: disable=unexpected-keyword-arg, too-many-function-args
                            (), callee=qubit.new
                        )
                    )
                    self.qubit_ssa_map[qid] = squin_qubit.result

            self.visit(state)

            if compactify:
                Walk(CFGCompactify()).rewrite(frame.curr_region)

            region = frame.curr_region

        return region

    def visit(self, state: lowering.State[pyqir.Module]) -> lowering.Result:
        """Visit a PyQIR module.

        Args:
            state (lowering.State[pyqir.Module]): The state of the visitor.

        Returns:
            lowering.Result: The result of the visitor.
        """
        # There could be multiple basic blocks in the entry point
        assert isinstance(self.entry_point.basic_blocks, list)  # type: ignore
        for block in self.entry_point.basic_blocks:  # type: ignore
            self.visit_node(state, block)

    def visit_node(self, state: lowering.State[pyqir.Module], node: Any) -> lowering.Result | None:
        """Visit a PyQIR node.

        Args:
            state (lowering.State[pyqir.Module]): The state of the visitor.
            node (Any): The node to visit.

        Returns:
            lowering.Result: The result of the visitor.
        """
        visitor_function = self.visit_map.get(type(node))
        if visitor_function:
            return visitor_function(state, node)

        return None

    def visit_basic_block(
        self, state: lowering.State[pyqir.Module], block: pyqir.BasicBlock
    ) -> lowering.Result:
        """Visit a PyQIR basic block.

        Args:
            state (lowering.State[pyqir.Module]): The state of the visitor.
            block (pyqir.BasicBlock): The basic block to visit.

        Returns:
            lowering.Result: The result of the visitor.
        """

        if len(block.instructions) < 1:
            raise InvalidSquinInput("No instructions found in basic block")
        for instruction in block.instructions:
            self.visit_node(state, instruction)

    def visit_call(
        self, state: lowering.State[pyqir.Module], call: pyqir.Call
    ) -> lowering.Result | None:
        """Visit a PyQIR Call instruction.

        Args:
            state (lowering.State[pyqir.Module]): The state of the visitor.
            call (pyqir.Call): The call instruction to visit.

        Returns:
            lowering.Result: The result of the visitor.
        """

        gate_name = call.callee.name
        args = call.args

        if gate_name in QIR_TO_SQUIN_UNSUPPORTED_STATEMENTS_MAP:
            return None
        if gate_name not in PYQIR_TO_SQUIN_GATES_MAP:
            raise InvalidSquinInput(f"Unsupported gate: {gate_name}")
        assert isinstance(args, list)
        return self.visit_gate(state, gate_name, args)

    def visit_gate(
        self,
        state: lowering.State[pyqir.Module],
        gate_name: str,
        args: list[pyqir.Value],
    ) -> lowering.Result:
        """Visit a PyQIR gate and convert it to a Squin gate.

        Args:
            state (lowering.State[pyqir.Module]): The state of the visitor.
            gate_name (str): The name of the gate to visit.
            args (list[pyqir.Value]): The arguments to the gate.

        Returns:
            lowering.Result: The result of the visitor.
        """
        squin_gate = PYQIR_TO_SQUIN_GATES_MAP[gate_name]
        inputs: list[ir.SSAValue] = []
        for arg in args:
            inputs.append(self.visit_node(state, arg))
        inputs = tuple(inputs)  # type: ignore
        return state.current_frame.push(
            func.Invoke(  # pylint: disable=unexpected-keyword-arg, too-many-function-args
                inputs, callee=squin_gate
            )
        )

    def visit_constant(
        self, state: lowering.State[pyqir.Module], value: pyqir.Value
    ) -> ir.SSAValue:
        """Visit a PyQIR Constant instruction.

        Args:
            state (lowering.State[pyqir.Module]): The state of the visitor.
            value (pyqir.Value): The value to visit.

        Returns:
            ir.SSAValue: The SSA value of the constant.
        """
        qubit_id = pointer_id(value)
        if qubit_id is not None and qubit_id in self.qubit_ssa_map:
            return self.qubit_ssa_map[qubit_id]

        supported_classical_const = (
            isinstance(value, (pyqir.FloatConstant, pyqir.IntConstant))
            or value.type.is_double
            or isinstance(value.type, pyqir.IntType)
        )
        if supported_classical_const:
            return state.current_frame.push(py.Constant(value=value.value)).result  # type: ignore

        raise InvalidSquinInput(f"Unsupported constant value: {value}")
