"""Test process util functions"""
import subprocess

import pytest

from nvshim.utils import (
    constants,
    process,
)


def test_process_run_completes_successfully():
    """Test run pipes results successfully"""
    output = process.run("echo", "success", stdout=subprocess.PIPE).stdout.strip()
    assert output == "success"


def test_process_run_handles_exception_system_exit():
    """Test run handles system exit with correct error code"""
    with pytest.raises(SystemExit) as exc_info:
        process.run("bash", "-c", "exit 1")

    assert exc_info.value.code == 1


def test_process_run_handles_exception_interrupt(mocker, capsys, snapshot):
    """Test run handles keyboard interrupt with correct error code"""
    mocked_process_run = mocker.patch(
        "subprocess.run",
        autospec=True,
        side_effect=KeyboardInterrupt("Ctrl+C"),
    )
    mocked_sys_exit = mocker.patch("sys.exit")
    args = ("bash", "-c", "echo 1")
    process.run(*args)
    mocked_process_run.assert_called_once_with(args, check=True, encoding="UTF-8")
    mocked_sys_exit.assert_called_once_with(constants.ErrorCode.KEYBOARD_INTERRUPT)
    captured = capsys.readouterr()
    snapshot.assert_match(process.clean_output(captured.out))
