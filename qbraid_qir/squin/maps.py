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
Module mapping PyQIR gate strings to squin gates.
"""
from bloqade import squin

# Mapping from full PyQIR gate strings to squin gates
PYQIR_TO_SQUIN_GATES_MAP = {
    "__quantum__qis__h__body": squin.h,
    "__quantum__qis__x__body": squin.x,
    "__quantum__qis__y__body": squin.y,
    "__quantum__qis__z__body": squin.z,
    "__quantum__qis__s__body": squin.s,
    "__quantum__qis__t__body": squin.t,
    "__quantum__qis__s__adj": squin.s_adj,
    "__quantum__qis__t__adj": squin.t_adj,
    "__quantum__qis__rx__body": squin.rx,
    "__quantum__qis__ry__body": squin.ry,
    "__quantum__qis__rz__body": squin.rz,
    "__quantum__qis__cnot__body": squin.cx,
    "__quantum__qis__cz__body": squin.cz,
}

QIR_TO_SQUIN_UNSUPPORTED_STATEMENTS_MAP = [
    "__quantum__rt__initialize",
    "__quantum__rt__result_record_output",
    "__quantum__rt__array_record_output",
]
