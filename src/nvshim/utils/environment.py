"""Utility constants and functions for environment management"""
import json
import os
from contextlib import contextmanager
from enum import Enum
from typing import Dict

EnvDict = Dict[str, str]


class EnvironmentVariable(Enum):
    """Environment variables nvshim cares about"""

    AUTO_INSTALL = "NVSHIM_AUTO_INSTALL"
    NVM_DIR = "NVM_DIR"
    VERBOSE = "NVSHIM_VERBOSE"


class MissingEnvironmentVariableError(Exception):
    """Error for missing environment variable"""

    def __init__(self, env_var: EnvironmentVariable):
        super().__init__()
        self.env_var = env_var


def _get_env_var(env_var: EnvironmentVariable, raise_missing: bool = False) -> object:
    try:
        return json.loads(os.environ[env_var.value])
    except KeyError as exc:
        if raise_missing:
            raise MissingEnvironmentVariableError(env_var) from exc
        return None
    except json.decoder.JSONDecodeError:
        return os.environ.get(env_var.value)


def _set_envs(values: EnvDict):
    os.environ.clear()
    os.environ.update(**values)


@contextmanager
def process_env(env_vars: EnvDict):
    """Run code with specific enviroment variables that are reset afterwards"""
    prev_env_vars = {**os.environ}
    _set_envs(env_vars)
    yield
    _set_envs(prev_env_vars)


def is_version_auto_install_enabled() -> bool:
    """Return if the auto install environment variable is true or false"""
    return bool(_get_env_var(EnvironmentVariable.AUTO_INSTALL))


def is_verbose_logging() -> bool:
    """Return if verbosity is set using the nvshim environment variable"""
    return bool(_get_env_var(EnvironmentVariable.VERBOSE))


def get_nvm_dir() -> str:
    """Return the path set from the $NVM_DIR environment variable"""
    return str(_get_env_var(EnvironmentVariable.NVM_DIR, True))
