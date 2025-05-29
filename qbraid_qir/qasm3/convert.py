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
from typing import Optional, Union, Any

from enum import Enum

import openqasm3
import pyqasm
from pyqir import Context, Module, qir_module

from .adaptive_support import QasmQIRAdaptiveVisitor
from .elements import QasmQIRModule, generate_module_id
from .exceptions import Qasm3ConversionError
from .visitor import QasmQIRVisitor

class Profile(Enum):
    """QIR Profile enumeration."""
    BASE = "base"
    ADAPTIVE = "adaptive"

# Export the enum values directly for convenience
BASE = Profile.BASE
ADAPTIVE = Profile.ADAPTIVE

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

    Returns:
        The QIR ``pyqir.Module`` representation of the input OpenQASM 3 program.

    Raises:
        TypeError: If the input is not a valid OpenQASM 3 program.
        Qasm3ConversionError: If the conversion fails.
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

    # Convert enum to string if needed, then normalize and validate
    if isinstance(profile, Profile):
        profile_str = profile.value.lower()
    else:
        profile_str = profile.lower()
        # Validate that the string corresponds to a valid profile
        valid_profiles = [p.value for p in Profile]
        if profile_str not in valid_profiles:
            raise ValueError(f"Invalid profile: {profile}. Valid profiles are: {valid_profiles}")

    visitor: Any
    if profile_str == "adaptive":
        visitor = QasmQIRAdaptiveVisitor(external_gates=external_gates, **kwargs)
    elif profile_str == "base":
        visitor = QasmQIRVisitor(external_gates=external_gates, **kwargs)
    else:
        raise ValueError(f"Invalid profile: {profile_str}")

    final_module.accept(visitor)

    err = llvm_module.verify()
    if err is not None:
        raise Qasm3ConversionError(err)
    return llvm_module
