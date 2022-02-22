"""Test main shim logic"""
import os
import subprocess

import pytest

from nvshim.core.__main__ import (
    main,
    parse_args,
)
from nvshim.utils.environment import (
    EnvironmentVariable,
    process_env,
)
from nvshim.utils.process import clean_output


def test_raises_missing_bin_file():
    """Test parsing of no arguments provided"""
    with pytest.raises(SystemExit):
        parse_args([])


def test_accepts_bin_file_arg(snapshot):
    """Test parsing accept the bin file to be called"""
    snapshot.assert_match(parse_args(["node"]))


def test_accepts_any_arg_for_bin_file(snapshot):
    """Test parsing accepts the bin file and arguments to be called with"""
    snapshot.assert_match(parse_args(["npm", "--version", "--help"]))


def test_fails_when_nvm_dir_not_available(mocker, capsys, snapshot, test_args):
    """Test main logic that when nvm dir is not available appropriate error is raised"""
    with process_env({EnvironmentVariable.VERBOSE.value: "true"}), pytest.raises(
        SystemExit
    ) as exc_info:
        main()

    assert exc_info.value.code == 1003
    captured = capsys.readouterr()
    snapshot.assert_match(clean_output(captured.out))
    assert not captured.err


def test_fails_when_version_not_installed(
    mocker,
    capsys,
    snapshot,
    test_args,
    test_nested_workspace_with_nvmrc,
    test_node_version_dir,
):
    """Test main logic that when nvm dir is not available appropriate error is raised"""
    nvm_dir, _ = test_node_version_dir
    mocker.patch(
        "nvshim.core.__main__.os.getcwd",
        autospec=True,
        return_value=test_nested_workspace_with_nvmrc,
    )
    mock_env = {
        EnvironmentVariable.NVM_DIR.value: nvm_dir,
        **os.environ,
        EnvironmentVariable.VERBOSE.value: "true",
        EnvironmentVariable.AUTO_INSTALL.value: "false",
    }
    with process_env(mock_env), pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1001
    captured = capsys.readouterr()
    snapshot.assert_match(clean_output(captured.out))
    assert not captured.err


def test_runs_correct_version_of_node(
    mocker,
    capsys,
    snapshot,
    test_args,
    test_nested_workspace_with_nvmrc,
    test_node_version_dir,
):
    """Test main logic that correct version of node is used from .nvmrc file"""
    nvm_dir, node_version_dir = test_node_version_dir
    mocker.patch(
        "nvshim.core.__main__.os.getcwd",
        autospec=True,
        return_value=test_nested_workspace_with_nvmrc,
    )
    mocked_process_run = mocker.patch(
        "nvshim.utils.process.subprocess.run", wraps=subprocess.run
    )
    mock_env = {
        EnvironmentVariable.NVM_DIR.value: nvm_dir,
        **os.environ,
        EnvironmentVariable.VERBOSE.value: "true",
        EnvironmentVariable.AUTO_INSTALL.value: "true",
    }
    with process_env(mock_env):
        main()

    mocked_process_run.assert_called_with(
        (f"{node_version_dir}/bin/{test_args[1]}", *test_args[2:]),
        check=True,
        encoding="UTF-8",
    )
    captured = capsys.readouterr()
    assert "with version <v14.5.0>" in clean_output(captured.out)
    assert not captured.err
