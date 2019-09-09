from enum import Enum
import json
import os


class EnvironmentVariable(Enum):
    AUTO_INSTALL = "NVSHIM_AUTO_INSTALL"
    NVM_DIR = "NVM_DIR"
    VERBOSE = "NVSHIM_VERBOSE"


class MissingEnvironmentVariableError(Exception):
    def __init__(self, env_var: EnvironmentVariable):
        self.env_var = env_var


def _get_env_var(env_var: EnvironmentVariable, raise_missing: bool = False) -> object:
    try:
        return json.loads(os.environ[env_var.value])
    except KeyError:
        if raise_missing:
            raise MissingEnvironmentVariableError(env_var)
    except json.decoder.JSONDecodeError:
        return os.environ.get(env_var.value)


def is_version_auto_install_enabled() -> bool:
    return bool(_get_env_var(EnvironmentVariable.AUTO_INSTALL))


def is_verbose_logging() -> bool:
    return _get_env_var(EnvironmentVariable.VERBOSE)


def get_nvm_dir() -> str:
    return _get_env_var(EnvironmentVariable.NVM_DIR, True)
