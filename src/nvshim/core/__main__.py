"""Main shim logic"""
import argparse
import functools
import os
import re
import subprocess
import sys
from typing import (
    Callable,
    Dict,
    Hashable,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
    Union,
)

import semver

from nvshim import __version__
from nvshim.utils import (
    environment,
    message,
    process,
)
from nvshim.utils.constants import ErrorCode

KeyType = TypeVar("KeyType")
ValueType = TypeVar("ValueType")


class HashableList(List[ValueType], Hashable):
    """List that can be stored in a hash object"""

    def __hash__(self):
        return hash(frozenset(self))


class HashableSet(Set[ValueType], Hashable):
    """Set that can be stored in a hash object"""

    def __hash__(self):
        return hash(frozenset(self))


class HashableDict(Dict[KeyType, ValueType], Hashable):
    """Dictionary that can be stored in a hash object"""

    def __hash__(self):
        return hash(frozenset(self.items()))


AliasResolver = Callable[..., Optional[str]]
AliasOrResolver = Union[str, AliasResolver]
VersionMapping = HashableDict[str, str]
AliasMapping = Union[HashableDict[str, AliasOrResolver], VersionMapping]


def get_files(path: str) -> Iterator[str]:
    """
    Generate the file paths to traverse, or a single path if a file name was given
    """
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for name in files:
                yield os.path.join(root, name)
    elif os.path.exists(path):
        yield path


def run_nvm_cmd(
    nvm_sh_path: str, nvm_args: str, **kwargs
) -> process.subprocess.CompletedProcess:
    """
    Run nvm command by creating temp file that sources nvm.sh and runs command

    :param nvm_sh_path: path to .nvm/nvm.sh file
    :param nvm_args: arguments to pass to loaded nvm command
    :return: completed process object
    """
    nvshim_file_path = f"{os.path.dirname(sys.argv[0])}/nvm_shim.sh.tmp"
    try:
        with open(nvshim_file_path, "w", encoding="UTF-8") as nvshim_file:
            nvshim_file.write(f"source {nvm_sh_path}\nnvm {nvm_args}")
        return process.run("bash", nvshim_file_path, **kwargs)
    finally:
        try:
            os.remove(nvshim_file_path)
        except OSError as exc:
            message.print_unable_to_remove_nvm_shim_temp_file(exc)


@functools.lru_cache(maxsize=None)
def get_nvm_stable_version(nvm_dir: str) -> Optional[str]:
    """
    Get the stable version by using nvm

    :param nvm_dir: the path to .nvm installation
    :return: the stable version number
    """
    output = run_nvm_cmd(
        get_nvmsh_path(nvm_dir), "alias stable", stdout=subprocess.PIPE
    ).stdout
    try:
        return re.findall(r"> v([\w\.]+)", process.clean_output(output))[0]
    except (IndexError, KeyError) as exc:
        message.print_unable_to_get_stable_version(exc)
        return None


def get_nvm_aliases_dir(nvm_dir: str) -> str:
    """
    Get the folder location of .nvm aliases

    :param nvm_dir: the path to .nvm installation
    :return: nvm directory + alias
    """
    return os.path.join(nvm_dir, "alias")


def get_nvm_aliases(nvm_dir: str) -> AliasMapping:
    """
    Get all nvm aliases

    :param nvm_dir: the path to .nvm installation
    :return: mapping of alias to version or laxy function that returns version
    """
    aliases_to_version: AliasMapping = HashableDict[str, AliasOrResolver](
        default="stable", node="stable", stable=lambda: get_nvm_stable_version(nvm_dir)
    )
    nvm_aliases_dir = get_nvm_aliases_dir(nvm_dir)
    for file_path in get_files(nvm_aliases_dir):
        rel_path = os.path.relpath(file_path, nvm_aliases_dir)
        with open(file_path, encoding="UTF-8") as open_file:
            aliases_to_version[rel_path] = open_file.readline().strip()

    return aliases_to_version


def parse_version(version: Optional[str]) -> Optional[semver.VersionInfo]:
    """
    Extract semantic version info object from version string

    :param version: version string in various formats e.g. v0.1, 1.0.1 etc.
    :return: parsed semantic version info or None when version cannot be parsed
    """
    if not version:
        return None
    try:
        return semver.VersionInfo.parse(
            version[1:] if version.startswith("v") else version
        )
    except ValueError:
        return None


@functools.lru_cache(maxsize=None)
def resolve_alias(
    var: AliasOrResolver,
    alias_mapping: AliasMapping,
    seen: HashableSet[str] = HashableSet(),
    seen_order: HashableList[str] = HashableList(),
) -> Tuple[Optional[semver.VersionInfo], Optional[str], HashableList[str]]:
    """
    Resolve an alias to a semantic version going through multiple mappings

    :param var: version alias or resolver
    :type alias_mapping: mapping of alias to version, alias or resolver
    :return: (semantic version info, alias name, list of aliases traversed)
    """
    alias = var() if callable(var) else var
    if alias and alias in alias_mapping and alias not in seen:
        seen_order.append(alias)
        seen.add(alias)
        return resolve_alias(alias_mapping.get(alias), alias_mapping, seen, seen_order)

    return parse_version(alias), alias, seen_order


@functools.lru_cache(maxsize=None)
def resolve_nvm_aliases(nvm_aliases: AliasMapping) -> HashableDict[str, str]:
    """
    Resolve all aliases in a mapping to their version info
    """
    resolved_aliases = HashableDict[str, str]()
    for alias, version in nvm_aliases.items():
        version_info = parse_version(version) if isinstance(version, str) else None
        version_info = (
            version_info if version_info else resolve_alias(version, nvm_aliases)[0]
        )

        if version_info:
            resolved_aliases[alias] = str(version_info)

    return resolved_aliases


def get_node_versions_dir(nvm_dir: str) -> str:
    """
    Get the folder location of nvm install node binaries

    :param nvm_dir: the path to .nvm installation
    :return: folder path string
    """
    return os.path.join(nvm_dir, "versions", "node")


def get_node_version_bin_dir(node_versions_dir: str, version: str) -> str:
    """
    Get the folder location of the binaries for the specfic version of node managed by .nvm

    :param node_versions_dir: the path of .nvm node installations
    :param version: resolved version string without the leading 'v' e.g. 1.1.1, 0.1.1
    :return: the folder path string of nvm managed node version installed binaries
    """
    return os.path.join(node_versions_dir, f"v{version}", "bin")


def get_node_versions(node_versions_dir: str) -> VersionMapping:
    """
    Get a mapping of nvm manager node versions to their bin install folder path

    :param node_versions_dir: the path of .nvm node installations
    :return: mapping of parsed versions in the node versions folder to node version bin folder path
    """
    files = os.listdir(node_versions_dir) if os.path.exists(node_versions_dir) else []
    return HashableDict(
        {
            str(v): get_node_version_bin_dir(node_versions_dir, str(v))
            for v in map(parse_version, files)
        }
    )


def merge_nvm_aliases_with_node_versions(
    nvm_aliases: AliasMapping, node_versions: VersionMapping
) -> VersionMapping:
    """
    Merge nvm aliases with node versions for aliases that resolved to detected node versions

    :param nvm_aliases: resolved nvm aliases
    :param node_versions: parsed node versions to bin folder path
    :return: all aliases and versions to bin folder path
    """
    alias_versions = {
        alias: node_versions[str(version)]
        for alias, version in nvm_aliases.items()
        if version in node_versions
    }
    return HashableDict({**alias_versions, **node_versions})


def get_nvmrc_path(exec_dir: str) -> Optional[str]:
    """
    Get the path to the nearest .nvmrc file from the current folder by traversing up the tree

    :param exec_dir: the folder to start search from
    :return: path to first found .nvmrc file
    """
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


def get_nvmrc(nvmrc_path: str = None) -> Tuple[str, bool]:
    """
    Get the version from the nvmrc file, falling back to default when none found

    :param nvmrc_path: the location of the .nvmrc file, defaults to None
    :return: .nvmrc version and bool indicating if it was found or using fallback
    """
    version = "default"
    if nvmrc_path:
        with open(nvmrc_path, encoding="UTF-8") as open_file:
            rc_version = open_file.readline().strip()
            parsed_version = parse_version(rc_version)
            if parsed_version:
                return str(parsed_version), True
            version = rc_version

    return version, False


def get_nvmsh_path(nvm_dir: str) -> str:
    """
    Get path to .nvm/nvm.sh file using

    :param nvm_dir: the path to .nvm installation
    :return: {nvm_dir}/.nvmsh
    """
    return os.path.join(nvm_dir, "nvm.sh")


def _pretty_version(version: str, parsed: bool) -> str:
    """
    Get the version string for printing logs of what version was found

    :param version: version string
    :param parsed: if the version was semantic compatible or not
    :return: version string with 'v' prefixed if parsed otherwise pass through
    """
    return f"v{version}" if parsed else version


def get_bin_path(
    *,
    version: str,
    is_version_parsed: bool,
    nvm_aliases: AliasMapping,
    node_versions: VersionMapping,
    bin_file: str,
    node_versions_dir: str,
    nvm_sh_path: str,
):
    """
    Get path of the node executable for the version/alias given

    :param version: version or alias
    :param is_version_parsed: if the version was semantically parseable
    :param nvm_aliases: nvm aliases to version mapping
    :param node_versions: node versions to bin folder mapping
    :param bin_file: the node binary to find
    :param node_versions_dir: the path of .nvm node installations
    :param nvm_sh_path: path to .nvm/nvm.sh file
    :return: path to the bin_file in the node version installation
    """
    resolved_nvm_aliases = (
        resolve_nvm_aliases(nvm_aliases)
        if version not in node_versions
        and nvm_aliases.get(version) not in node_versions
        else HashableDict(
            {
                k: k if k in node_versions else v
                for k, v in nvm_aliases.items()
                if isinstance(v, str)
            }
        )
    )
    version_mapping = merge_nvm_aliases_with_node_versions(
        resolved_nvm_aliases, node_versions
    )
    try:
        node_path = version_mapping[version]
    except KeyError:
        if not environment.is_version_auto_install_enabled():
            message.print_version_not_installed(
                _pretty_version(version, is_version_parsed)
            )
            sys.exit(ErrorCode.VERSION_NOT_INSTALLED)

        run_nvm_cmd(nvm_sh_path, f"install {version}")
        node_path = get_node_version_bin_dir(
            node_versions_dir, version=resolved_nvm_aliases.get(version, version)
        )

    bin_path = os.path.join(node_path, bin_file)
    if not os.path.exists(bin_path):
        message.print_node_bin_file_does_not_exist(bin_path)
        sys.exit(ErrorCode.EXECUTABLE_NOT_FOUND)

    return bin_path


def parse_args(args: Sequence[str]) -> Tuple[argparse.Namespace, List[str]]:
    """
    Get the arguments to be used to execute the node binary
    :return: parsed and unknown arguments
    """
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

    return parser.parse_known_args(args)


def get_nvm_dir() -> str:
    """
    Get nvm dir from environment or fail if the variable is not set

    :return: $NVM_DIR
    """
    try:
        return environment.get_nvm_dir()
    except environment.MissingEnvironmentVariableError as error:
        message.print_env_var_missing(error.env_var)
        sys.exit(ErrorCode.ENV_NVM_DIR_MISSING)


def main(version_number: str = __version__):
    """
    Run the main shim logic

    :param version_number: the current nvshim version, defaults to __version__
    """
    message.print_running_version(version_number)
    parsed_args, unknown_args = parse_args(sys.argv[1:])
    nvmrc_path = get_nvmrc_path(os.getcwd())
    version, parsed = get_nvmrc(nvmrc_path)
    nvm_dir = get_nvm_dir()

    bin_path = get_bin_path(
        version=version,
        is_version_parsed=parsed,
        nvm_aliases=get_nvm_aliases(nvm_dir),
        node_versions=get_node_versions(get_node_versions_dir(nvm_dir)),
        node_versions_dir=get_node_versions_dir(nvm_dir),
        bin_file=parsed_args.bin_file,
        nvm_sh_path=get_nvmsh_path(nvm_dir),
    )
    message.print_using_version(_pretty_version(version, parsed), bin_path, nvmrc_path)
    process.run(bin_path, *parsed_args.bin_args, *unknown_args)


if __name__ == "__main__":
    main()
