import subprocess
import pytest

from nvshim.utils import process


def test_process_run_completes_successfully():
    output = process.run("echo", "success", stdout=subprocess.PIPE).stdout.strip()
    assert output == b"success"


def test_process_run_raises_correct_exception():
    with pytest.raises(SystemExit) as exc_info:
        process.run("bash", "-c", "exit 1")

    assert exc_info.value.code == 1
