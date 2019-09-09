import os
import subprocess
import sys
from typing import Dict


def _with_venv(env: Dict[str, str]):
    path_key = "PATH"
    env_path = env.get(path_key, "")
    return dict(env, **{path_key: f"venv/bin/:{env_path}"})


def run(*args, **kwargs):
    try:
        subprocess.run(
            args, **kwargs, check=True, env=_with_venv(kwargs.get("env", os.environ))
        )
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
