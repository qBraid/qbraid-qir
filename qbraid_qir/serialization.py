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
Module for exporting QIR to bitcode and LLVM IR files.

"""
import logging
import os
import pathlib
from typing import TYPE_CHECKING, Optional

from .exceptions import QbraidQirError

if TYPE_CHECKING:
    import pyqir


def dumps(module: "pyqir.Module", output_dir: Optional[str] = None) -> None:
    """
    Saves the Quantum Intermediate Representation (QIR) of a given module
    to bitcode (.bc) and LLVM IR (.ll) files.

    Args:
        module: The module containing the QIR.
        output_dir (Optional[str]): The directory where the files will be saved.
                                    If not provided, defaults to the current
                                    working directory.

    Raises:
        QbraidQirError: If there's an error in writing the files.
    """
    # Determine the filename prefix from the module's source filename
    filename_prefix = os.path.splitext(os.path.basename(module.source_filename))[0]

    # Set the output directory to the current working directory if not provided
    file_dir = output_dir if output_dir else str(pathlib.Path.cwd())

    # Create the directory if it doesn't exist
    try:
        os.makedirs(file_dir, exist_ok=True)
    except OSError as err:
        raise QbraidQirError("Failed to create target directory") from err

    # Construct file paths
    bc_file = os.path.join(file_dir, f"{filename_prefix}.bc")
    ll_file = os.path.join(file_dir, f"{filename_prefix}.ll")

    # Save bitcode file (does not require an encoding)
    with open(bc_file, "wb") as file:  # pylint: disable=unspecified-encoding
        file.write(module.bitcode)
    logging.info("Saved to %s", bc_file)

    # Save LLVM IR file (default python encoding)
    with open(ll_file, "w", encoding="utf-8") as file:
        file.write(str(module))
    logging.info("Saved to %s", ll_file)
