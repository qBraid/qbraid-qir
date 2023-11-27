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
qBraid QIR setup file

"""
import os

from setuptools import setup


def read_requirements(file_path):
    """
    Reads a requirements file and returns the packages listed in it.

    Args:
        file_path (str): Path to the requirements file.

    Returns:
        list: List of package requirements.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def read_version(file_path):
    """
    Extracts the version from a Python file containing a version variable.

    Args:
        file_path (str): Path to the Python file with the version variable.

    Returns:
        str: Version string, if found; otherwise, None.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return next(
            (
                line.split("=")[-1].strip().strip("\"'")
                for line in file
                if line.startswith("__version__")
            ),
            None,
        )


# Determine the directory where setup.py is located
here = os.path.abspath(os.path.dirname(__file__))

# Reading the package's version and requirements
version = read_version(os.path.join(here, "qbraid_qir/_version.py"))
install_requires = read_requirements(os.path.join(here, "requirements.txt"))
dev_requires = read_requirements(os.path.join(here, "requirements-dev.txt"))
docs_requires = read_requirements(os.path.join(here, "docs", "requirements.txt"))

setup(
    version=version,
    install_requires=install_requires,
    extras_require={"dev": dev_requires, "docs": docs_requires},
)
