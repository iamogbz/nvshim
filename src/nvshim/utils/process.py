import os
import re
import subprocess
import sys
from typing import Dict

from .environment import EnvironmentVariable, EnvDict, process_env
from .message import print_unable_to_run_node


def _include_venv(env: EnvDict):
    path_key = "PATH"
    env_path = env.get(path_key, "")
    return {**env, path_key: f"venv/bin/:{env_path}"}


def run(*args, **kwargs) -> subprocess.CompletedProcess:
    env_vars = _include_venv(os.environ)
    env_vars[EnvironmentVariable.AUTO_INSTALL.value] = "false"

    try:
        with process_env(env_vars):
            return subprocess.run(args, **kwargs, check=True)
    except subprocess.CalledProcessError as error:
        print_unable_to_run_node(error)
        sys.exit(error.returncode)


def clean_output(output: str) -> str:
    """Removes ansi color codes from string"""
    return re.sub(r"\x1B[@-_][0-?]*[ -/]*[@-~]", "", str(output).strip())
