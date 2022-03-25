"""Test main shim logic"""
import os
import subprocess
import sys
from pathlib import Path

import pytest
import semver

from nvshim.core.__main__ import (
    HashableDict,
    HashableList,
    get_files,
    get_nvm_aliases,
    get_nvm_stable_version,
    get_nvmrc,
    main,
    match_version,
    parse_args,
    parse_version,
    resolve_alias,
    run_nvm_cmd,
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


def test_fails_when_nvm_dir_not_available(capsys, snapshot, test_args):
    """Test main logic that when nvm dir is not available appropriate error is raised"""
    with process_env({EnvironmentVariable.VERBOSE.value: "true"}), pytest.raises(
        SystemExit
    ) as exc_info:
        main()

    captured = capsys.readouterr()
    snapshot.assert_match(clean_output(captured.out))
    assert not captured.err
    assert exc_info.value.code == 1003


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

    captured = capsys.readouterr()
    snapshot.assert_match(clean_output(captured.out))
    assert not captured.err
    assert exc_info.value.code == 1001


def test_fails_when_node_binary_not_found_in_install_path(
    mocker,
    capsys,
    test_args,
    test_workspace_with_nvmrc,
    test_node_version_dir,
):
    """Test main logic checks nvm install node binary exists before execution"""
    nvm_dir, node_version_dir = test_node_version_dir
    mocker.patch(
        "nvshim.core.__main__.os.getcwd",
        autospec=True,
        return_value=test_workspace_with_nvmrc,
    )
    expected_node_bin_path = f"{node_version_dir}/bin/{test_args[1]}"

    mocker.patch(
        "nvshim.core.__main__.os.path.exists",
        side_effect=lambda path: Path(path).exists()
        if path != expected_node_bin_path
        else False,
    )
    mock_env = {
        EnvironmentVariable.NVM_DIR.value: nvm_dir,
        **os.environ,
        EnvironmentVariable.VERBOSE.value: "true",
        EnvironmentVariable.AUTO_INSTALL.value: "true",
    }
    with process_env(mock_env), pytest.raises(SystemExit) as exc_info:
        main()

    captured = capsys.readouterr()
    assert "No executable file found at" in clean_output(captured.out)
    assert exc_info.value.code == 1002


def test_runs_correct_version_of_node(
    mocker,
    capsys,
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


def test_get_files_returns_path_when_single_file(test_workspace_with_nvmrc):
    """Test get files when called for non directory"""
    file_path = f"{test_workspace_with_nvmrc}/.nvmrc"
    result = [*get_files(file_path)]
    assert result == [file_path]


def test_run_nvm_command_handles_failure_to_remove_tmp_file(capsys, mocker, snapshot):
    """Test handling of os remove file error"""
    mocked_process_run = mocker.patch(
        "nvshim.core.__main__.process.run",
        autospec=True,
    )
    mocker.patch(
        "nvshim.core.__main__.os.remove",
        autospec=True,
        side_effect=OSError,
    )
    run_nvm_cmd("/home/.nvm/.nvm.sh", "list")
    mocked_process_run.assert_called_with(
        "bash", f"{os.path.dirname(sys.argv[0])}/nvm_shim.sh.tmp"
    )
    captured = capsys.readouterr()
    assert snapshot == clean_output(captured.out)


def test_get_nvm_stable_version_returns_nothing_when_no_version_found(
    capsys, mocker, snapshot
):
    """Test failure handling of fetching stable version from nvm"""
    mocked_process_run = mocker.patch(
        "nvshim.core.__main__.process.run",
        autospec=True,
        return_value=subprocess.CompletedProcess(None, 1),
    )
    assert get_nvm_stable_version("/home/.nvm") is None
    mocked_process_run.assert_called_with(
        "bash",
        f"{os.path.dirname(sys.argv[0])}/nvm_shim.sh.tmp",
        stdout=subprocess.PIPE,
    )
    captured = capsys.readouterr()
    assert snapshot == clean_output(captured.out)


def test_get_nvm_stable_version_returns_correctly_when_no_version_found(mocker):
    """Test correct handling of fetching alias version from nvm"""
    test_nvm_dir = "/home/.nvm"
    expected_version = "17.8.0"
    mocked_run_nvm_cmd = mocker.patch(
        "nvshim.core.__main__.run_nvm_cmd",
        autospec=True,
        return_value=subprocess.CompletedProcess(
            None, 0, f"stable -> 17.8 (-> v{expected_version}) (default)\n"
        ),
    )
    assert get_nvm_aliases(test_nvm_dir) == {
        "default": "stable",
        "stable": expected_version,
    }
    mocked_run_nvm_cmd.assert_called_with(
        f"{test_nvm_dir}/nvm.sh", "alias  --no-colors", stdout=subprocess.PIPE
    )


def test_parse_version_handles_none_case():
    """Test parse version handles when version given is None"""
    assert parse_version(None) is None


def test_get_nvmrc_uses_raw_value_when_not_parseable(test_workspace):
    """Test get nvmrc uses value in rc version when not parseable"""
    nvmrc_path = f"{test_workspace}/.nvmrc"
    non_parseable_version = "D902"
    with open(nvmrc_path, "w", encoding="UTF-8") as open_file:
        open_file.write(non_parseable_version)
    assert get_nvmrc(nvmrc_path) == non_parseable_version


def test_resolve_alias_handles_cycles():
    """Test that resolving aliases can handle recursive references"""
    mock_alias_mappings = HashableDict({"a": "b", "b": "c", "c": "a"})
    result = resolve_alias("a", mock_alias_mappings)
    assert result == (None, "a", HashableList(["a", "b", "c"]))


def test_parse_version_returns_correct_values():
    """Test limits of version parsing"""
    assert parse_version("") is None
    assert parse_version("1") is None
    assert parse_version("v1") is None
    assert parse_version("v1.0") is None
    assert parse_version("v1.0") is None
    assert parse_version("1.0.0") == semver.VersionInfo(1, 0, 0)
    assert parse_version("v1.0.0") == semver.VersionInfo(1, 0, 0)


def test_match_version_returns_correct_value():
    """Test limits of matching version"""
    version_set = ("0.0.0", "0.0.1", "1.0.0", "1.0.1", "1.1.0", "2.0.0")
    assert match_version("alias", version_set) is None
    assert match_version("", version_set) is None
    assert match_version("3", version_set) is None
    assert match_version("2", version_set) == semver.VersionInfo.parse("2.0.0")
    assert match_version("1", version_set) == semver.VersionInfo.parse("1.1.0")
    assert match_version("1.0", version_set) == semver.VersionInfo.parse("1.0.1")
    assert match_version("0", version_set) == semver.VersionInfo.parse("0.0.1")
