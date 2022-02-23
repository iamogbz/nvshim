"""Configure pytest"""
import os
import shutil
import sys
from typing import (
    Dict,
    Union,
)

import pytest

__TEST_DIR__ = os.path.join(os.environ["PWD"], "tmp")
__TEST_VERSION__ = "v14.5.0"
__TEST_DIR_STRUCTURE__: Dict[str, Union[str, dict]] = {".nvmrc": __TEST_VERSION__}
__NVM_DIR__ = os.path.join(os.path.expanduser("~"), ".nvm")


@pytest.fixture
def test_args():
    """Setup system process args for testing"""
    initial_args = list(sys.argv)
    sys.argv = sys.argv[:1] + ["npm", "--version", "--help"]
    yield sys.argv
    sys.argv = initial_args


def _flatten_fs(base: str, structure: Dict[str, Union[str, dict]]):
    flattened: Dict[str, Union[str, dict]] = {}
    items = list(structure.items())
    while items:
        path, content = items.pop()
        file_path = os.path.realpath(os.path.join(base, path))
        if isinstance(content, str):
            flattened[file_path] = content
        elif isinstance(content, dict):
            flattened[file_path] = {}
            items.extend(
                (os.path.join(path, _path), _content)
                for _path, _content in content.items()
            )

    return flattened


def _make_fs(base: str, structure: Dict[str, Union[str, dict]] = None):
    os.makedirs(base, exist_ok=True)
    for file_path, content in _flatten_fs(base, structure or {}).items():
        content_type = type(content)
        if content_type is str:
            with open(file_path, "w", encoding="UTF-8") as open_file:
                open_file.write(content)
        elif content_type is dict:
            os.makedirs(file_path, exist_ok=True)


@pytest.fixture
def test_workspace():
    """Prepare test workspace for interacting with file system during tests"""
    _make_fs(__TEST_DIR__)
    yield __TEST_DIR__
    shutil.rmtree(__TEST_DIR__)


@pytest.fixture
def test_node_version_dir():
    """Ensure node version used for testing does not exist before running tests"""
    nvm_dir = os.environ.get("NVM_DIR") or __NVM_DIR__
    version_path = os.path.join(nvm_dir, "versions", "node", __TEST_VERSION__)
    shutil.rmtree(version_path, ignore_errors=True)
    return __NVM_DIR__, version_path


@pytest.fixture
def test_workspace_with_nvmrc(test_workspace: str):
    """Ensure test workspace has .nvmrc file"""
    _make_fs(test_workspace, __TEST_DIR_STRUCTURE__)
    yield test_workspace


@pytest.fixture
def test_nested_workspace_with_nvmrc(test_workspace: str):
    """Ensure workspace has .nvmrc file in a nested folder"""
    nested_workspace = os.path.join(test_workspace, "nest", "project")
    _make_fs(test_workspace, {nested_workspace: {}, **__TEST_DIR_STRUCTURE__})
    yield nested_workspace
