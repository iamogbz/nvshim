import argparse
import functools
import os
import sys
from typing import Dict, List, Sequence

import semver

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
            return str(parse_version(f.readline().strip()))

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
        if not environment.is_version_auto_install_enabled():
            message.print_version_not_installed(version)
            sys.exit(ErrorCode.VERSION_NOT_INSTALLED)

        process.run(f"source {nvm_sh_path} && nvm install {version}", shell="bash")
        node_path = get_node_version_bin_dir(node_versions_dir, version)

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


def main():
    parsed_args, unknown_args = parse_args(sys.argv[1:])
    nvmrc_path = get_nvmrc_path()
    version = get_nvmrc(nvmrc_path)
    try:
        nvm_dir = environment.get_nvm_dir()
    except environment.MissingEnvironmentVariableError as error:
        message.print_env_var_missing(error.env_var)
        sys.exit(ErrorCode.ENV_NVM_DIR_MISSING)

    bin_path = get_bin_path(
        version=version,
        node_versions=merge_nvm_aliases_with_node_versions(
            resolve_nvm_aliases(get_nvm_aliases(get_nvm_aliases_dir(nvm_dir))),
            get_node_versions(get_node_versions_dir(nvm_dir)),
        ),
        node_versions_dir=get_node_versions_dir(nvm_dir),
        bin_file=parsed_args.bin_file,
        nvm_sh_path=get_nvmsh_path(nvm_dir),
    )
    message.print_using_version(version, bin_path, nvmrc_path)
    process.run(bin_path, *parsed_args.bin_args, *unknown_args)


if __name__ == "__main__":
    main()
