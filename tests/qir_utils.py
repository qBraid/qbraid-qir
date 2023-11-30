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
Module for containing QIR code utils functions used for unit tests.

"""
import os


def assert_equal_qir(given_qir: str, filename: str) -> None:
    """Function that compares generated qir to the qir in a file.

    Args:
        given_qir (str): Given qir string that should be compared with the file.
        filename (str): Name of the file that should be compared with the given qir.
    """
    current_dir = os.path.dirname(__file__)

    resources_file = os.path.join(current_dir, "resources", f"{filename}.ll")

    with open(resources_file, encoding="utf-8") as f:
        file_data = f.read().strip()

    processed_given_qir = given_qir.strip()

    assert file_data == processed_given_qir
