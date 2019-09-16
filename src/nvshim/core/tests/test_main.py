import pytest
import os
import runpy
import shutil
import subprocess

from nvshim.utils.constants import ErrorCode
from nvshim.utils.environment import process_env, EnvironmentVariable
from nvshim.utils.process import clean_output
from nvshim.core.__main__ import (
    get_node_version_bin_dir,
    get_node_versions_dir,
    main,
    parse_args,
)


class TestParseArgs:
    def test_raises_missing_bin_file(self):
        with pytest.raises(SystemExit):
            parse_args([])

    def test_accepts_bin_file_arg(self, snapshot):
        snapshot.assert_match(parse_args(["node"]))

    def test_accepts_any_arg_for_bin_file(self, snapshot):
        snapshot.assert_match(parse_args(["npm", "--version", "--help"]))


class TestMain:
    def test_fails_when_nvm_dir_not_available(
        self, mocker, capsys, snapshot, test_args
    ):
        with process_env({EnvironmentVariable.VERBOSE.value: "true"}), pytest.raises(
            SystemExit
        ) as exc_info:
            main()

        assert exc_info.value.code == 1003
        captured = capsys.readouterr()
        snapshot.assert_match(clean_output(captured.out))
        assert not captured.err

    def test_fails_when_version_not_installed(
        self,
        mocker,
        capsys,
        snapshot,
        test_args,
        test_nested_workspace_with_nvmrc,
        test_node_version_dir,
    ):
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
        self,
        mocker,
        capsys,
        snapshot,
        test_args,
        test_nested_workspace_with_nvmrc,
        test_node_version_dir,
    ):
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
            (f"{node_version_dir}/bin/{test_args[1]}", *test_args[2:]), check=True
        )
        captured = capsys.readouterr()
        assert "with version <lts/carbon>" in clean_output(captured.out)
        assert not captured.err
