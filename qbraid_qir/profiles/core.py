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
Module containing core profile classes for QIR generation.

"""


from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

import pyqir
from pyqir import qis

from .abstract import QIRModule, QIRVisitor


@dataclass
class ProfileCapabilities:
    """Data class representing profile capabilities."""

    forward_branching: bool = False
    conditional_execution: bool = False
    qubit_reuse: bool = False
    measurement_tracking: bool = False
    grouped_output_recording: bool = False
    preserves_register_structure: bool = False
    inverted_bit_order: bool = False


@dataclass
class ProfileRestrictions:
    """Data class representing profile restrictions."""

    subset_barriers_allowed: bool = True
    must_cover_all_qubits: bool = False
    emit_calls_configurable: bool = True
    modifiers_supported: bool = True
    prefer_qis_over_native: bool = False


class Profile(ABC):
    """Abstract base class for QIR profiles."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.capabilities = ProfileCapabilities()
        self.restrictions = ProfileRestrictions()

    @abstractmethod
    def get_measurement_function(self) -> Callable:
        """Get the measurement function for this profile."""
        # pass

    @abstractmethod
    def get_reset_function(self) -> Callable:
        """Get the reset function for this profile."""
        # pass

    @abstractmethod
    def get_barrier_function(self) -> Callable:
        """Get the barrier function for this profile."""
        # pass

    @abstractmethod
    def get_conditional_function(self) -> Callable:
        """Get the conditional branching function for this profile."""
        # pass

    @abstractmethod
    def should_track_qubit_measurement(self) -> bool:
        """Whether this profile tracks qubit measurement state."""
        # pass

    @abstractmethod
    def allow_qubit_use_after_measurement(self) -> bool:
        """Whether this profile allows qubit operations after measurement."""
        # pass

    @abstractmethod
    def record_output_method(self, visitor: QIRVisitor, module: QIRModule) -> None:
        """Profile-specific output recording method."""
        # pass


class BaseProfile(Profile):
    """Basic QIR profile implementation."""

    def __init__(self):
        super().__init__("Base", "1.0.0")
        self.capabilities.forward_branching = False
        self.capabilities.conditional_execution = True
        self.capabilities.qubit_reuse = False
        self.capabilities.measurement_tracking = False
        self.capabilities.grouped_output_recording = False

        self.restrictions.subset_barriers_allowed = False
        self.restrictions.must_cover_all_qubits = True
        self.restrictions.prefer_qis_over_native = False
        self.restrictions.emit_calls_configurable = True

    def get_measurement_function(self) -> Callable:
        return pyqir._native.mz

    def get_reset_function(self) -> Callable:
        return pyqir._native.reset

    def get_barrier_function(self) -> Callable:
        return pyqir._native.barrier

    def get_conditional_function(self) -> Callable:
        return pyqir._native.if_result

    def should_track_qubit_measurement(self) -> bool:
        return True

    def allow_qubit_use_after_measurement(self) -> bool:
        return False

    def record_output_method(self, visitor: QIRVisitor, module: QIRModule) -> None:
        """Basic output recording - simple sequential recording."""
        if visitor._record_output is False:
            return
        assert visitor._llvm_module is not None
        assert visitor._builder is not None
        i8p = pyqir.PointerType(pyqir.IntType(visitor._llvm_module.context, 8))
        for i in range(module.num_qubits):
            result_ref = pyqir.result(visitor._llvm_module.context, i)
            pyqir.rt.result_record_output(visitor._builder, result_ref, pyqir.Constant.null(i8p))


class AdaptiveProfile(Profile):
    """Adaptive QIR profile implementation with advanced capabilities."""

    def __init__(self):
        super().__init__("AdaptiveExecution", "1.0.0")
        self.capabilities.forward_branching = True
        self.capabilities.conditional_execution = True
        self.capabilities.qubit_reuse = True
        self.capabilities.measurement_tracking = True
        self.capabilities.grouped_output_recording = True
        self.capabilities.preserves_register_structure = True
        self.capabilities.inverted_bit_order = True

        self.restrictions.subset_barriers_allowed = False
        self.restrictions.must_cover_all_qubits = True
        self.restrictions.emit_calls_configurable = True
        self.restrictions.prefer_qis_over_native = True

    def get_measurement_function(self) -> Callable:
        return qis.mz

    def get_reset_function(self) -> Callable:
        return qis.reset

    def get_barrier_function(self) -> Callable:
        return qis.barrier

    def get_conditional_function(self) -> Callable:
        return qis.if_result

    def should_track_qubit_measurement(self) -> bool:
        return True

    def allow_qubit_use_after_measurement(self) -> bool:
        return True

    def record_output_method(self, visitor: QIRVisitor, module: QIRModule) -> None:
        """Adaptive profile output recording - preserves register structure."""
        if not visitor._record_output:
            return
        assert visitor._llvm_module is not None
        assert visitor._builder is not None
        i8p = pyqir.PointerType(pyqir.IntType(visitor._llvm_module.context, 8))
        null_ptr = pyqir.Constant.null(i8p)
        recorded_ids = set()

        # If we have register structure information, use it
        if hasattr(visitor, "_global_creg_size_map") and visitor._global_creg_size_map:
            # Record output grouped by register to preserve structure
            for reg_name, reg_size in visitor._global_creg_size_map.items():
                # Record array for each register
                pyqir.rt.array_record_output(
                    visitor._builder,
                    pyqir.const(pyqir.IntType(visitor._llvm_module.context, 64), reg_size),
                    null_ptr,
                )
                # Record individual results within the register (inverted order)
                for i in range(reg_size - 1, -1, -1):
                    bit_label = f"{reg_name}_{i}"
                    if bit_label in visitor._clbit_labels:
                        bit_id = visitor._clbit_labels[bit_label]
                        if bit_id not in recorded_ids:
                            result_ref = pyqir.result(visitor._llvm_module.context, bit_id)
                            pyqir.rt.result_record_output(visitor._builder, result_ref, null_ptr)
                            recorded_ids.add(bit_id)
        else:
            # Fallback to simple sequential recording
            for i in range(module.num_qubits):
                result_ref = pyqir.result(visitor._llvm_module.context, i)
                pyqir.rt.result_record_output(visitor._builder, result_ref, null_ptr)


class ProfileRegistry:
    """Registry for managing QIR profiles."""

    _profiles: dict[str, Profile] = {}

    @classmethod
    def register_profile(cls, profile: Profile) -> None:
        """Register a profile."""
        cls._profiles[profile.name] = profile

    @classmethod
    def get_profile(cls, name: str) -> Profile:
        """Get a profile by name."""
        if name not in cls._profiles:
            raise ValueError(f"Unknown profile: {name}")
        return cls._profiles[name]

    @classmethod
    def list_profiles(cls) -> list[str]:
        """List available profile names."""
        return list(cls._profiles.keys())


# Register built-in profiles
ProfileRegistry.register_profile(BaseProfile())
ProfileRegistry.register_profile(AdaptiveProfile())
