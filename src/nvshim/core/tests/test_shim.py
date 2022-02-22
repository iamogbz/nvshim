"""Test node shim"""
import sys

import pytest

from nvshim.core.shim import main


@pytest.fixture
def test_shim_args():
    """Setup system process args for testing"""
    initial_args = list(sys.argv)
    sys.argv = ["/full/path/to/shim/node", "--version", "--help"]
    yield sys.argv
    sys.argv = initial_args


def test_shim_executes_with_args(mocker, test_shim_args):
    """Test that the shim passes the correct args to run the main node shim logic"""
    mocked_core_main = mocker.patch("nvshim.core.shim.core.main", autospec=True)
    main()
    mocked_core_main.assert_called_once_with()
