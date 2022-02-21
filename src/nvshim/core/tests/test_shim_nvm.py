import runpy
import sys

import pytest

from nvshim.core.shim_nvm import main
from nvshim.utils.constants import ErrorCode
from nvshim.utils.process import clean_output


@pytest.fixture
def test_shim_args():
    initial_args = list(sys.argv)
    sys.argv = ["/full/path/to/shim/nvm", "--version", "--help"]
    yield sys.argv
    sys.argv = initial_args


def test_shim_nvm_executes_with_args(mocker, test_shim_args):
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
