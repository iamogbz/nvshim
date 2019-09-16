from enum import Enum, IntEnum

from colored import fg, stylize

from .environment import EnvironmentVariable


class Color(Enum):
    ERROR = fg("red")
    NOTICE = fg("yellow")


class MessageLevel(IntEnum):
    LOUD = 2
    NORMAL = 1
    QUIET = 0


def _level() -> MessageLevel:
    """Minium threshold level for logging to occur"""
    from .environment import is_verbose_logging

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
    _print_error(f"Environment variable '{env_var.value}' missing")


def print_using_version(version: str, bin_path: str, nvmrc_path: str = None):
    messages = (
        f"Found '{nvmrc_path}' with version <{version}>"
        if nvmrc_path
        else f"Using <{version}> version",
        f"\n.{bin_path}\n",
    )
    _print("".join(messages), level=MessageLevel.QUIET)


def print_node_bin_file_does_not_exist(bin_path: str):
    _print(f"No executable file found at '{bin_path}'", level=MessageLevel.LOUD)


def print_version_not_installed(version: str):
    _print_error(f"N/A version '{version}' is not yet installed.\n")
    _print(
        "You need to run",
        _stylize(f"'nvm install {version}'", Color.NOTICE),
        "to install it before using it.\n",
    )
    _print(
        "Or set the environment variable",
        _stylize(f"'{EnvironmentVariable.AUTO_INSTALL.value}'", Color.NOTICE),
        "to auto install at run time.\n",
    )


def print_running_version(version_number: str):
    _print(f"Executing shim version {version_number}", level=MessageLevel.QUIET)


def print_unable_to_get_stable_version():
    _print_error("Unable to retrieve stable version from nvm")
