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
Module containing OpenQASM to QIR conversion functions

"""
from enum import Enum
from typing import Any, Optional, Union

import openqasm3
import pyqasm
from pyqir import Context, Module, qir_module

# from .adaptive_support import QasmQIRAdaptiveVisitor
from .elements import QasmQIRModule, generate_module_id
from .exceptions import Qasm3ConversionError
from .visitor import QasmQIRVisitor


class Profile(Enum):
    """QIR Profile enumeration."""

    BASE = "Base"
    ADAPTIVE = "AdaptiveExecution"

    @classmethod
    def from_input(cls, profile: Union["Profile", str]) -> "Profile":
        """Convert string or Profile enum to Profile enum.

        Args:
            profile: Either a Profile enum instance or a string representation

        Returns:
            Profile enum instance

        Raises:
            NotImplementedError: If string doesn't match any valid profile
            TypeError: If input is neither Profile nor string
        """

        if isinstance(profile, cls):
            return profile
        elif isinstance(profile, str):
            try:
                normalized = profile.strip().lower()
                profile_map = {
                    "base": cls.BASE,
                    "adaptive": cls.ADAPTIVE,
                }
                return profile_map[normalized]
            except KeyError:
                valid = [p.value for p in cls]
                raise NotImplementedError(
                    f"Invalid profile: {profile}. Valid profiles are: {valid}"
                )
        else:
            raise TypeError(f"Profile must be of type Profile or str, not {type(profile).__name__}")


def qasm3_to_qir(
    program: Union[openqasm3.ast.Program, str],
    name: Optional[str] = None,
    external_gates: Optional[list[str]] = None,
    profile: Union[Profile, str] = Profile.BASE,
    **kwargs,
) -> Module:
    """Converts an OpenQASM 3 program to a PyQIR module.

    Args:
        program (openqasm3.ast.Program or str): The OpenQASM 3 program to convert.
        name (str, optional): Identifier for created QIR module. Auto-generated if not provided.
        external_gates (list[str], optional): A list of custom gate names that are not natively
            recognized by pyqasm but should be treated as valid during program unrolling.
        profile (Profile or str): The specific QIR profile to use for the conversion.
            Can be Profile.BASE, Profile.ADAPTIVE, or equivalent strings. Defaults to Profile.BASE.

    Keyword Args:
        initialize_runtime (bool): Whether to perform quantum runtime environment initialization,
            defaults to `True`.
        record_output (bool): Whether to record output calls for registers, defaults to `True`.
        emit_barrier_calls (bool): Whether to emit barrier calls, defaults to `True`.

    Returns:
        The QIR ``pyqir.Module`` representation of the input OpenQASM 3 program.

    Raises:
        TypeError: If the input is not a valid OpenQASM 3 program.
        Qasm3ConversionError: If the conversion fails.
        NotImplementedError: If string doesn't match any valid profile
    """
    if isinstance(program, openqasm3.ast.Program):
        program = openqasm3.dumps(program)

    elif not isinstance(program, str):
        raise TypeError("Input quantum program must be of type openqasm3.ast.Program or str.")

    qasm3_module = pyqasm.loads(program)
    qasm3_module.unroll(external_gates=external_gates)
    if name is None:
        name = generate_module_id()
    llvm_module = qir_module(Context(), name)

    final_module = QasmQIRModule(name, qasm3_module, llvm_module)

    # Validate and normalize profile
    profile_enum = Profile.from_input(profile)

    # Create visitor with the specified profile
    visitor = QasmQIRVisitor(
        profile_name=profile_enum.value, external_gates=external_gates, **kwargs
    )

    final_module.accept(visitor)

    err = llvm_module.verify()
    if err is not None:
        raise Qasm3ConversionError(err)
    return llvm_module
