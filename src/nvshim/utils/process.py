"""Run process utility functions"""
import os
import re
import subprocess
import sys

from .constants import ErrorCode
from .environment import (
    EnvDict,
    EnvironmentVariable,
    process_env,
)
from .message import (
    print_process_interrupted,
    print_unable_to_run,
)


def _include_venv(env: EnvDict):
    path_key = "PATH"
    env_path = env.get(path_key, "")
    return {**env, path_key: f"venv/bin/:{env_path}"}


def run(*args, **kwargs) -> subprocess.CompletedProcess:
    """
    Disables nvshim auto install for the duration of the process run.
    Wraps subprocess.run passing varargs as the first parameter and kwargs as is.
    Handles keyboard interrupt and called process error to end with correct sys exit error code.
    """
    env_vars = _include_venv({**os.environ})
    env_vars[EnvironmentVariable.AUTO_INSTALL.value] = "false"

    with process_env(env_vars):
        return _run_with_error_handler(*args, **kwargs)


def _run_with_error_handler(*args, **kwargs) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, encoding="UTF-8", **kwargs, check=True)
    except KeyboardInterrupt as interrupt_e:
        print_process_interrupted(interrupt_e)
        sys.exit(ErrorCode.KEYBOARD_INTERRUPT)
    except subprocess.CalledProcessError as process_e:
        print_unable_to_run(process_e)
        sys.exit(process_e.returncode)


def clean_output(output: str) -> str:
    """Removes ansi color codes from string"""
    return re.sub(r"\x1B[@-_][0-?]*[ -/]*[@-~]", "", str(output).strip())
