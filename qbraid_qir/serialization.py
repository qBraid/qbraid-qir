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
Module for exporting QIR to bitcode and LLVM IR files.

"""
from __future__ import annotations

import logging
import os
import pathlib
from typing import TYPE_CHECKING, Optional

from .exceptions import QbraidQirError

if TYPE_CHECKING:
    import pyqir


def dumps(module: pyqir.Module, output_dir: Optional[str] = None) -> None:
    """
    Saves the Quantum Intermediate Representation (QIR) of a given module
    to bitcode (.bc) and LLVM IR (.ll) files.

    Args:
        module: The module containing the QIR.
        output_dir (Optional[str]): The directory where the files will be saved.
            If not provided, defaults to the current working directory.

    Raises:
        QbraidQirError: If there's an error in writing the files.
    """
    filename_prefix = os.path.splitext(os.path.basename(module.source_filename))[0]

    file_dir = output_dir if output_dir else str(pathlib.Path.cwd())

    try:
        os.makedirs(file_dir, exist_ok=True)
    except OSError as err:
        raise QbraidQirError("Failed to create target directory") from err

    bc_file = os.path.join(file_dir, f"{filename_prefix}.bc")
    ll_file = os.path.join(file_dir, f"{filename_prefix}.ll")

    with open(bc_file, "wb") as file:  # pylint: disable=unspecified-encoding
        file.write(module.bitcode)
    logging.info("Saved to %s", bc_file)

    with open(ll_file, "w", encoding="utf-8") as file:
        file.write(str(module))
    logging.info("Saved to %s", ll_file)
