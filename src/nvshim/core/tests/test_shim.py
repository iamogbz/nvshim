import runpy
import sys

import pytest

from nvshim.core.shim import main


@pytest.fixture
def test_shim_args():
    initial_args = list(sys.argv)
    sys.argv = ["/full/path/to/shim/node", "--version", "--help"]
    yield sys.argv
    sys.argv = initial_args


def test_shim_executes_with_args(mocker, test_shim_args):
    mocked_core_main = mocker.patch("nvshim.core.shim.core.main")
    main()
    mocked_core_main.assert_called_once_with()
