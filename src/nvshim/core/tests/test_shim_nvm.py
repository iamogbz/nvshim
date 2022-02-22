"""Test nvm shim"""
import sys

import pytest

from nvshim.core.shim_nvm import main


@pytest.fixture
def test_shim_args():
    """Setup system process args for testing"""
    initial_args = list(sys.argv)
    sys.argv = ["/full/path/to/shim/nvm", "--version", "--help"]
    yield sys.argv
    sys.argv = initial_args


def test_shim_nvm_executes_with_args(mocker, test_shim_args):
    """Test that the shim passes the correct args to run the nvm command"""
    nvm_dir = "/home/.nvm"
    mocker.patch(
        "nvshim.core.shim_nvm.core.get_nvm_dir", autospec=True, return_value=nvm_dir
    )
    mocked_core_run_nvm_cmd = mocker.patch(
        "nvshim.core.shim_nvm.core.run_nvm_cmd", autospec=True
    )
    main()
    mocked_core_run_nvm_cmd.assert_called_once_with(
        f"{nvm_dir}/nvm.sh", "--version --help"
    )
