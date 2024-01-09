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
Unit tests for the export module

"""
import os
import pathlib
import shutil

import pytest

from qbraid_qir.serialization import dumps

# pylint: disable=redefined-outer-name,too-few-public-methods


class MockModule:
    """Mock class for a Module object"""

    def __init__(self, source_filename, bitcode, ir_representation):
        self.source_filename = source_filename
        self.bitcode = bitcode
        self.ir_representation = ir_representation

    def __str__(self):
        return self.ir_representation


@pytest.fixture
def mock_module():
    """Fixture for creating a mock module"""
    return MockModule("mock_module", b"bitcode data", "IR representation")


@pytest.fixture
def tmp_path():
    """Provides a temporary directory for the test and cleans it up after tests are complete."""
    tmp_directory = pathlib.Path(__file__).parent / "tmp"
    tmp_directory.mkdir(exist_ok=True)
    yield tmp_directory
    shutil.rmtree(tmp_directory)


def test_save_qir_default_directory(tmp_path, mock_module):
    """Test saving QIR in the default directory"""
    os.chdir(tmp_path)
    dumps(mock_module)
    assert os.path.exists("mock_module.bc")
    assert os.path.exists("mock_module.ll")


def test_save_qir_custom_directory(tmp_path, mock_module):
    """Test saving QIR in a custom directory"""
    custom_dir = tmp_path / "custom"
    dumps(mock_module, output_dir=str(custom_dir))
    assert os.path.exists(custom_dir / "mock_module.bc")
    assert os.path.exists(custom_dir / "mock_module.ll")


def test_save_qir_with_exception(mock_module):
    """Test exception handling"""
    with pytest.raises(Exception):
        dumps(mock_module, output_dir="/non/existent/path")
