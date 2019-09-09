import argparse
import functools
import os
import re
import sys
from typing import Dict, List, Sequence

import semver

from compiler import __version__
from utils import environment, message, process
from utils.constants import ErrorCode


AliasMapping = VersionMapping = Dict[str, str]


class HashableDict(dict):
    def __hash__(self):
        return hash(frozenset(self.items()))


def get_files(path: str) -> [str]:
    """
    Generate the file paths to traverse, or a single path if a file name was given
    """
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for name in files:
                yield os.path.join(root, name)
    elif os.path.exists(path):
        yield path


def _run_nvm_cmd(nvm_sh_path: str, args: str) -> process.subprocess.CompletedProcess:
    return process.run(
        f". {nvm_sh_path} && nvm {args}",
        shell="bash",
        encoding="UTF-8",
        capture_output=True,
    )


@functools.lru_cache(maxsize=None)
def get_nvm_stable_version(nvm_dir) -> str:
    output = _run_nvm_cmd(get_nvmsh_path(nvm_dir), "alias stable").stdout
    result = re.sub(r"\x1B[@-_][0-?]*[ -/]*[@-~]", "", str(output).strip())
    return re.findall(r"> v([\w\.]+)\)", result)[0]


def get_nvm_aliases_dir(nvm_dir: str) -> str:
    return os.path.join(nvm_dir, "alias")


def get_nvm_aliases(nvm_dir: str) -> AliasMapping:
    aliases_to_version = HashableDict(
        default="stable", node="stable", stable=get_nvm_stable_version(nvm_dir)
    )
    nvm_aliases_dir = get_nvm_aliases_dir(nvm_dir)
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


@functools.lru_cache(maxsize=None)
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
    files = os.listdir(node_versions_dir) if os.path.exists(node_versions_dir) else []
    return {
        str(v): get_node_version_bin_dir(node_versions_dir, str(v))
        for v in map(parse_version, files)
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


def get_nvmrc(nvmrc_path: str = None) -> (str, bool):
    version = "default"
    if nvmrc_path:
        with open(nvmrc_path) as f:
            rc_version = f.readline().strip()
            parsed_version = parse_version(rc_version)
            if parsed_version:
                return str(parsed_version), True
            version = rc_version

    return version, False


def get_nvmsh_path(nvm_dir: str) -> str:
    return os.path.join(nvm_dir, "nvm.sh")


def _pretty_version(version: str, parsed: bool) -> str:
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
    version_mapping = merge_nvm_aliases_with_node_versions(nvm_aliases, node_versions)
    try:
        node_path = version_mapping[version]
    except KeyError:
        if not environment.is_version_auto_install_enabled():
            message.print_version_not_installed(
                _pretty_version(version, is_version_parsed)
            )
            sys.exit(ErrorCode.VERSION_NOT_INSTALLED)

        _run_nvm_cmd(nvm_sh_path, f"install {version}")
        node_path = get_node_version_bin_dir(
            node_versions_dir, version=nvm_aliases.get(version, version)
        )

    bin_path = os.path.join(node_path, bin_file)
    if not os.path.exists(bin_path):
        message.print_node_bin_file_does_not_exist(bin_path)
        sys.exit(ErrorCode.EXECUTABLE_NOT_FOUND)

    return bin_path


def parse_args(args: Sequence[str]) -> (argparse.Namespace, List[str]):
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


def main(version_number: str = __version__):
    message.print_running_version(version_number)
    parsed_args, unknown_args = parse_args(sys.argv[1:])
    nvmrc_path = get_nvmrc_path()
    version, parsed = get_nvmrc(nvmrc_path)
    try:
        nvm_dir = environment.get_nvm_dir()
    except environment.MissingEnvironmentVariableError as error:
        message.print_env_var_missing(error.env_var)
        sys.exit(ErrorCode.ENV_NVM_DIR_MISSING)

    bin_path = get_bin_path(
        version=version,
        is_version_parsed=parsed,
        nvm_aliases=resolve_nvm_aliases(get_nvm_aliases(nvm_dir)),
        node_versions=get_node_versions(get_node_versions_dir(nvm_dir)),
        node_versions_dir=get_node_versions_dir(nvm_dir),
        bin_file=parsed_args.bin_file,
        nvm_sh_path=get_nvmsh_path(nvm_dir),
    )
    message.print_using_version(_pretty_version(version, parsed), bin_path, nvmrc_path)
    process.run(bin_path, *parsed_args.bin_args, *unknown_args)


if __name__ == "__main__":
    main()
