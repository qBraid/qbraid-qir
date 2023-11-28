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
Module containing utility functions for unit tests.

"""


def check_qir_result(given_qir: str, filename: str) -> None:
    """Function that compares generated qir to the qir in a file

    Args:
        given_qir (str): Given qir string that should be compared with the file
        filename (str): Name of the file that should be compared with the given qir
    """

    with open(f"resources/{filename}.ll", encoding="utf-8") as f:
        data = f.read()

    assert data == given_qir
