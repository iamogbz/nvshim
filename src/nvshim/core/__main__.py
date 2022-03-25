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
from nvshim.utils.constants import (
    Alias,
    ErrorCode,
)

K = TypeVar("K")
V = TypeVar("V")


class HashableList(List[V], Hashable):
    """List that can be stored in a hash object"""

    def __hash__(self):
        return hash(frozenset(self))


class HashableSet(Set[V], Hashable):
    """Set that can be stored in a hash object"""

    def __hash__(self):
        return hash(frozenset(self))


class HashableDict(Dict[K, V], Hashable):
    """Dictionary that can be stored in a hash object"""

    def __hash__(self):
        return hash(frozenset(self.items()))


AliasResolver = Callable[..., Optional[str]]
AliasOrResolver = Union[str, AliasResolver]
VersionMapping = HashableDict[str, str]
AliasMapping = HashableDict[str, AliasOrResolver]


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
            nvshim_file.write(f"source {nvm_sh_path} &> /dev/null\nnvm {nvm_args}")
        return process.run("bash", nvshim_file_path, **kwargs)
    finally:
        try:
            os.remove(nvshim_file_path)
        except OSError as exc:
            message.print_unable_to_remove_nvm_shim_temp_file(exc)


def parse_alias_version(line: str) -> Tuple[str, str, Optional[semver.VersionInfo]]:
    """
    Convert nvm alias line to alias and eventual version
    Pattern: alias -> value (-> resolved version)
    Example:
    default -> 14 (-> N/A)
    stable -> 17.8 (-> v17.8.0) (default)
    unstable -> N/A (default)
    """
    alias_ptn = r"^([\w\-.\/ *]+) -> ([\w\-.\/ *]+)( \(-> ([\w\-.\/ ]+)( \*)?\))?( \(default\))?$"
    result = re.findall(alias_ptn, line.strip())
    return result[0][0], result[0][1], parse_version(result[0][3])


@functools.lru_cache(maxsize=None)
def get_nvm_aliases(nvm_dir: str, *, alias: Optional[str] = "") -> VersionMapping:
    """
    Get all nvm aliases

    :param nvm_dir: the path to .nvm installation
    :return: mapping of alias to version
    """
    output: Optional[str] = run_nvm_cmd(
        get_nvmsh_path(nvm_dir),
        f"alias {alias} --no-colors",
        stdout=subprocess.PIPE,
    ).stdout
    aliases = HashableDict(
        {
            k: str(t or v)
            for line in (output or "").splitlines()
            for (k, v, t) in [parse_alias_version(line)]
        }
    )

    if Alias.DEFAULT.value not in aliases:
        aliases[Alias.DEFAULT.value] = Alias.STABLE.value

    return aliases


@functools.lru_cache(maxsize=None)
def get_nvm_stable_version(nvm_dir: str) -> Optional[str]:
    """
    Get the stable version by using nvm

    :param nvm_dir: the path to .nvm installation
    :return: the stable version number
    """
    return get_nvm_aliases(nvm_dir, alias=Alias.STABLE.value).get(
        Alias.STABLE.value
    ) or message.print_unable_to_get_alias_version(Alias.STABLE.value)


def get_nvm_aliases_dir(nvm_dir: str) -> str:
    """
    Get the folder location of .nvm aliases

    :param nvm_dir: the path to .nvm installation
    :return: nvm directory + alias
    """
    return os.path.join(nvm_dir, "alias")


def get_nvm_alias_mapping(nvm_dir: str) -> AliasMapping:
    """
    Get all nvm aliases

    :param nvm_dir: the path to .nvm installation
    :return: mapping of alias to version or lazy function that returns version
    """
    aliases_to_version = AliasMapping(
        {
            Alias.DEFAULT.value: Alias.STABLE.value,
            Alias.NODE.value: Alias.STABLE.value,
            Alias.STABLE.value: lambda: get_nvm_stable_version(nvm_dir),
        }
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


def as_number(maybe_numeric: str) -> Tuple[Union[int, float, None], bool, bool]:
    """
    Attempt to parse string as numeric value

    :returns: the number, is integer i.e. only major, is float i.e. no patch
    """
    try:
        return int(maybe_numeric), True, True
    except ValueError:
        try:
            return float(maybe_numeric), False, True
        except ValueError:
            return None, False, False


def match_version(
    version_alias: str, version_set: Set[str]
) -> Optional[semver.VersionInfo]:
    """
    Find the closest matching semantic version in the version set
    """
    plain_version = (
        version_alias[1:] if version_alias.startswith("v") else version_alias
    )
    version = parse_version(plain_version)
    if version:
        is_minor_wildcard = False
        is_patch_wildcard = False
    else:
        version_number, is_minor_wildcard, is_patch_wildcard = as_number(plain_version)
        if version_number is None:
            return None
        version = parse_version(f"{float(version_number)}.0")

    version_sorted = sorted(
        vi
        for vi in (semver.VersionInfo.parse(v) for v in version_set)
        if version.major == vi.major
        and (is_minor_wildcard or version.minor == vi.minor)
        and (is_patch_wildcard or version.patch == vi.patch)
    )
    return version_sorted.pop() if version_sorted else None


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


def get_nvmrc(nvmrc_path: str = None) -> str:
    """
    Get the version from the nvmrc file, falling back to default when none found

    :param nvmrc_path: the location of the .nvmrc file, defaults to None
    :return: .nvmrc version or using fallback
    """
    if nvmrc_path:
        with open(nvmrc_path, encoding="UTF-8") as open_file:
            return open_file.readline().strip()

    return Alias.DEFAULT.value


def get_nvmsh_path(nvm_dir: str) -> str:
    """
    Get path to .nvm/nvm.sh file using

    :param nvm_dir: the path to .nvm installation
    :return: {nvm_dir}/.nvmsh
    """
    return os.path.join(nvm_dir, "nvm.sh")


def resolve_version(
    *, version_alias: str, nvm_aliases: AliasMapping, node_versions: VersionMapping
) -> Tuple[str, bool]:
    """
    Resolve the rc version to an installed or installable version

    :param rc_version: version loaded from nvmrc file
    :param nvm_aliases: nvm aliases to version mapping
    :param node_versions: node versions to bin folder mapping
    :return: version to use, if version is installed
    """
    resolved_version, resolved_alias, _ = resolve_alias(version_alias, nvm_aliases)
    version_to_install = resolved_version or resolved_alias or version_alias
    version_installed = match_version(
        version_alias=str(version_to_install),
        version_set=set(node_versions.keys()),
    )
    return str(version_installed or version_to_install), bool(version_installed)


def get_bin_path(
    *,
    version_alias: str,
    version: str,
    version_installed: bool,
    bin_file: str,
    node_versions_dir: str,
    nvm_sh_path: str,
):
    """
    Get path of the node executable for the version/alias given

    :param version_alias: nvmrc version or alias
    :param version: resolved version number to use
    :param version_installed: if the resolved version was already installed
    :param bin_file: the node binary to find
    :param node_versions_dir: the path of .nvm node installations
    :param nvm_sh_path: path to .nvm/nvm.sh file
    :return: path to the bin_file in the node version installation
    """
    if not version_installed:
        installed_version = None
        if environment.is_version_auto_install_enabled():
            run_nvm_cmd(nvm_sh_path, f"install {version}")
            installed_version = match_version(
                version_alias=version,
                version_set=set(get_node_versions(node_versions_dir).keys()),
            )
        if not installed_version:
            message.print_version_not_installed(version_alias, version)
            sys.exit(ErrorCode.VERSION_NOT_INSTALLED)
        version = installed_version

    node_path = get_node_version_bin_dir(node_versions_dir, version=version)
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
    rc_version = get_nvmrc(nvmrc_path)
    nvm_dir = get_nvm_dir()
    node_versions_dir = get_node_versions_dir(nvm_dir)
    version, version_installed = resolve_version(
        version_alias=rc_version,
        nvm_aliases=get_nvm_alias_mapping(nvm_dir),
        node_versions=get_node_versions(node_versions_dir),
    )
    bin_path = get_bin_path(
        version_alias=rc_version,
        version=version,
        version_installed=version_installed,
        node_versions_dir=node_versions_dir,
        bin_file=parsed_args.bin_file,
        nvm_sh_path=get_nvmsh_path(nvm_dir),
    )
    message.print_using_version(rc_version, version, bin_path, nvmrc_path)
    process.run(bin_path, *parsed_args.bin_args, *unknown_args)


if __name__ == "__main__":
    main()
