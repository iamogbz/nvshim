"""Messages printed by nvshim"""
from enum import (
    Enum,
    IntEnum,
)
from subprocess import CalledProcessError

from colored import (
    fg,
    stylize,
)

from .environment import (
    EnvironmentVariable,
    is_verbose_logging,
)


class Color(Enum):
    """Message colors"""

    ERROR = fg("red")
    NOTICE = fg("yellow")


class MessageLevel(IntEnum):
    """Message levels"""

    LOUD = 2
    NORMAL = 1
    QUIET = 0


def _level() -> MessageLevel:
    """Minium threshold level for logging to occur"""

    return MessageLevel.QUIET if is_verbose_logging() else MessageLevel.NORMAL


def _print(*args, level=MessageLevel.NORMAL):
    if level < _level():
        return

    print(*args)


def _stylize(text: str, color: Color) -> str:
    return stylize(text, color.value)


def _print_stylized(text: str, color: Color, level=MessageLevel.NORMAL):
    _print(_stylize(text, color), level=level)


def _print_error(text: str):
    _print_stylized(text, Color.ERROR, MessageLevel.LOUD)


def print_env_var_missing(env_var: EnvironmentVariable):
    """Print message for missing environment variable"""
    _print_error(f"Environment variable '{env_var.value}' missing")


def print_using_version(
    rc_version: str, version: str, bin_path: str, nvmrc_path: str = None
):
    """Print message showing path of which .nvmrc is found and node version is used"""
    messages = (
        f"Found '{nvmrc_path}' with version <{rc_version}>"
        if nvmrc_path
        else f"Using <{version}> version",
        f"\n{bin_path}\n",
    )
    _print("".join(messages), level=MessageLevel.QUIET)


def print_node_bin_file_does_not_exist(bin_path: str):
    """Pring message showing that bin executable not found at given path"""
    _print(f"No executable file found at '{bin_path}'", level=MessageLevel.LOUD)


def print_version_not_installed(version_alias: str, install_version: str):
    """Print error showing that node version is not .nvm installed and instructions to resolve"""
    _print_error(
        f"N/A: version '{version_alias} -> {install_version or 'N/A'}' is not yet installed.\n"
    )
    _print(
        "You need to run",
        _stylize(f"'nvm install {install_version}'", Color.NOTICE),
        "to install it before using it.\n",
    )
    _print(
        "Or set the environment variable",
        _stylize(f"'{EnvironmentVariable.AUTO_INSTALL.value}'", Color.NOTICE),
        "to auto install at run time.\n",
    )


def print_running_version(version_number: str):
    """Print which version of current nvshim"""
    _print(f"Executing shim version {version_number}", level=MessageLevel.QUIET)


def print_unable_to_get_alias_version(alias: str):
    """Print error for unable to get alias version from nvm"""
    _print_error(f"Unable to retrieve {alias} version from nvm")


def print_process_interrupted(exc: KeyboardInterrupt):
    """Print error for interrupt handler"""
    _print(f"\nInterrupted. {exc}")


def print_unable_to_run(exc: CalledProcessError):
    """Print error for failed sub process run"""
    _print(str(exc), level=MessageLevel.QUIET)


def print_unable_to_remove_nvm_shim_temp_file(exc: Exception):
    """Print error for failure to delete temp nvm exec shim file"""
    _print_error("Unable to remove temporary nvm shim file")
    _print(str(exc), level=MessageLevel.QUIET)
