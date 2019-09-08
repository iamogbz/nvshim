import argparse
from enum import Enum, IntEnum
import functools
import json
import os
import subprocess
import sys
from typing import Dict

from colored import stylize, fg, bg, attr
import semver


AliasMapping = VersionMapping = Dict[str, str]


class HashableDict(dict):
    def __hash__(self):
        return hash(frozenset(self.items()))


class Color(Enum):
    ERROR = fg("red")
    NOTICE = fg("yellow")


class ErrorCode(IntEnum):
    EXECUTABLE_NOT_FOUND = 1002
    VERSION_NOT_INSTALLED = 1001


class EnvironmentVariable(Enum):
    AUTO_INSTALL = "NVSHIM_AUTO_INSTALL"
    NVM_DIR = "NVM_DIR"


class Message:
    @staticmethod
    def _stylize(text: str, color: Color) -> str:
        return stylize(text, color.value)

    @classmethod
    def _print_stylized(cls, text: str, color: Color):
        print(cls._stylize(text, color))

    @classmethod
    def _print_error(cls, text: str):
        cls._print_stylized(text, Color.ERROR)

    @classmethod
    def _print_notice(cls, text: str):
        cls._print_stylized(text, Color.NOTICE)

    @classmethod
    def print_env_var_missing(cls, env_var: EnvironmentVariable):
        cls._print_error(f"Environment variable '{env_var.value}' missing")

    @staticmethod
    def print_found_version(nvmrc_path: str, version: str):
        print(f"Found '{nvmrc_path}' with version <v{version}>\n")

    @staticmethod
    def print_node_bin_file_not_provided():
        print(f"Node executable file was not supplied")

    @staticmethod
    def print_node_bin_file_does_not_exist(bin_path: str):
        print(f"No executable file found at '{bin_path}'")

    @classmethod
    def print_version_not_installed(cls, version: str):
        cls._print_error(f"N/A version 'v{version}' is not yet installed.\n")
        print(
            "You need to run",
            cls._stylize(f"'nvm install v{version}'", Color.NOTICE),
            "to install it before using it.\n",
        )
        print(
            "Or set the environment variable",
            cls._stylize(f"'{EnvironmentVariable.AUTO_INSTALL.value}'", Color.NOTICE),
            "to auto install at run time.\n",
        )


def run(*args, **kwargs):
    try:
        subprocess.run(args, **kwargs, check=True)
    except subprocess.CalledProcessError as error:
        exit(error.returncode)


def get_env_var(env_var: EnvironmentVariable, raise_missing: bool = False) -> object:
    try:
        return json.loads(os.environ[env_var.value])
    except KeyError:
        if raise_missing:
            Message.print_env_var_missing(env_var)
            raise
    except json.decoder.JSONDecodeError:
        return os.environ.get(env_var.value)


def get_nvm_dir() -> str:
    return get_env_var(EnvironmentVariable.NVM_DIR, True)


def get_files(path: str) -> [str]:
    """
    Generate the file paths to traverse, or a single path if a file name was given
    """
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for name in files:
                yield os.path.join(root, name)
    else:
        yield path


def get_nvm_aliases_dir(nvm_dir: str) -> str:
    return os.path.join(nvm_dir, "alias")


def get_nvm_aliases(nvm_aliases_dir: str) -> AliasMapping:
    aliases_to_version = HashableDict()
    for file_path in get_files(nvm_aliases_dir):
        rel_path = os.path.relpath(file_path, nvm_aliases_dir)
        with open(file_path) as f:
            aliases_to_version[rel_path] = f.readline().strip()

    return aliases_to_version


def parse_version(version: str) -> semver.VersionInfo:
    try:
        return semver.parse_version_info(
            version[1:] if version.startswith("v") else version
        )
    except ValueError:
        pass


@functools.lru_cache(maxsize=None)
def resolve_alias(
    name: str, alias_mapping: AliasMapping
) -> (semver.VersionInfo, str, [str]):
    """
    Resolve an alias to a semantic version going through multiple mappings
    
    :param name: name of the version alias to resolve
    :type alias_mapping: mapping of alias to version
    :return: (semantic version info, alias name, list of aliases traversed)
    """
    seen_in_order = []
    seen = set()
    while name in alias_mapping and name not in seen:
        name = alias_mapping.get(name)
        seen_in_order.append(name)
        seen.add(name)

    return parse_version(name), name, seen_in_order


def resolve_nvm_aliases(nvm_aliases: AliasMapping) -> AliasMapping:
    """
    Resolve all aliases in a mapping to their version info
    """
    resolved_aliases = {}
    for alias, version in nvm_aliases.items():
        version_info = parse_version(version) or resolve_alias(version, nvm_aliases)[0]

        if version_info:
            resolved_aliases[alias] = str(version_info)

    return resolved_aliases


def get_node_versions_dir(nvm_dir: str) -> str:
    return os.path.join(nvm_dir, "versions", "node")


def get_node_version_bin_dir(node_versions_dir: str, version: str) -> str:
    return os.path.join(node_versions_dir, f"v{version}", "bin")


def get_node_versions(node_versions_dir: str) -> VersionMapping:
    return {
        str(v): get_node_version_bin_dir(node_versions_dir, str(v))
        for v in map(parse_version, os.listdir(node_versions_dir))
    }


def merge_nvm_aliases_with_node_versions(
    nvm_aliases: AliasMapping, node_versions: VersionMapping
) -> VersionMapping:
    alias_versions = {
        alias: node_versions[version]
        for alias, version in nvm_aliases.items()
        if version in node_versions
    }
    return dict(alias_versions, **node_versions)


def get_nvmrc_path(exec_dir: str = os.getcwd()) -> str:
    root_dir = os.path.abspath(os.sep)
    current_dir = exec_dir
    config_file = ".nvmrc"
    config_found = False
    while True:
        current_config = os.path.join(current_dir, config_file)
        config_found = os.path.exists(current_config)
        if config_found or current_dir == root_dir:
            break
        current_dir = os.path.realpath(os.path.join(current_dir, "../"))

    return current_config if config_found else None


def get_nvmrc(nvmrc_path: str = None) -> str:
    if nvmrc_path:
        with open(nvmrc_path) as f:
            version = str(parse_version(f.readline().strip()))
            Message.print_found_version(nvmrc_path, version)
            return version

    return "default"


def get_nvmsh_path(nvm_dir: str) -> str:
    return os.path.join(nvm_dir, "nvm.sh")


def get_bin_path(
    *,
    version: str,
    node_versions: VersionMapping,
    bin_file: str,
    node_versions_dir: str,
    nvm_sh_path: str,
):
    try:
        node_path = node_versions[version]
    except KeyError:
        if not is_auto_install_version_enabled():
            Message.print_version_not_installed(version)
            exit(ErrorCode.VERSION_NOT_INSTALLED)

        run(f"source {nvm_sh_path} && nvm install {version}", shell="bash")
        node_path = get_node_version_bin_dir(node_versions_dir, version)

    bin_path = os.path.join(node_path, bin_file)
    if not os.path.exists(bin_path):
        Message.print_node_bin_file_does_not_exist(bin_path)
        exit(ErrorCode.EXECUTABLE_NOT_FOUND)

    return bin_path


def is_auto_install_version_enabled() -> bool:
    return bool(get_env_var(EnvironmentVariable.AUTO_INSTALL))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch executable using project or default node version",
        add_help=False,
    )
    parser.add_argument(
        "bin_file",
        metavar="nvx",
        type=str,
        help="filename of the node executable binary",
    )
    parser.add_argument(
        "bin_args",
        metavar="args",
        nargs="*",
        help="arguments passed to the node executable",
    )

    return parser.parse_known_args()


def main():
    nvm_dir = get_nvm_dir()
    parsed_args, unknown_args = parse_args()
    bin_path = get_bin_path(
        version=get_nvmrc(get_nvmrc_path()),
        node_versions=merge_nvm_aliases_with_node_versions(
            resolve_nvm_aliases(get_nvm_aliases(get_nvm_aliases_dir(nvm_dir))),
            get_node_versions(get_node_versions_dir(nvm_dir)),
        ),
        node_versions_dir=get_node_versions_dir(nvm_dir),
        bin_file=parsed_args.bin_file,
        nvm_sh_path=get_nvmsh_path(nvm_dir),
    )
    run(bin_path, *parsed_args.bin_args, *unknown_args)


if __name__ == "__main__":
    main()
