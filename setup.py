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

setup(
    version=version,
    install_requires=["pyqir~=0.10.0"],
    extras_require={
        "cirq": ["cirq-core>=1.3.0,<1.4.0"],
        "qasm3": ["openqasm3[parser]>=0.4.0,<0.6.0"],
        "test": ["qbraid~=0.5.3", "pytest", "pytest-cov"],
        "lint": ["black[jupyter]", "isort", "pylint"],
        "docs": ["sphinx~=7.2.6", "sphinx-autodoc-typehints>=1.24,<2.1", "sphinx-rtd-theme~=2.0.0", "docutils<0.21"],
    },
)
