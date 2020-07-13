import runpy
import sys

import pytest

from nvshim.core.shim import main
from nvshim.utils.constants import ErrorCode
from nvshim.utils.process import clean_output


@pytest.fixture
def test_shim_args():
    initial_args = list(sys.argv)
    sys.argv = ["/full/path/to/shim/node", "--version", "--help"]
    yield sys.argv
    sys.argv = initial_args


def test_shim_executes_with_args(mocker, test_shim_args):
    mocked_core_main = mocker.patch("nvshim.core.shim.core.main", autospec=True)
    main()
    mocked_core_main.assert_called_once_with()


def test_shim_handles_process_interrupt(mocker, capsys, test_shim_args, snapshot):
    mocked_core_main = mocker.patch(
        "nvshim.core.shim.core.main",
        autospec=True,
        side_effect=KeyboardInterrupt("Ctrl+C"),
    )
    mocked_sys_exit = mocker.patch("sys.exit")
    main()
    mocked_core_main.assert_called_once_with()
    mocked_sys_exit.assert_called_once_with(ErrorCode.KEYBOARD_INTERRUPT)
    captured = capsys.readouterr()
    snapshot.assert_match(clean_output(captured.out))
