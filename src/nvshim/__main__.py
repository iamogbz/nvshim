import functools
import json
import os
import subprocess
import sys
from typing import Dict

from colored import stylize, fg, bg, attr
import semver

COLOR_ERROR = fg("red")
COLOR_NOTICE = fg("yellow")
COLOR_RESET = attr("reset")

ERROR_CODE_EXECUTABLE_NOT_GIVEN = 1000
ERROR_CODE_EXECUTABLE_NOT_FOUND = 1002
ERROR_CODE_VERSION_NOT_INSTALLED = 1001

ENV_VAR_NVM_DIR = "NVM_DIR"
ENV_VAR_AUTO_INSTALL = "NVSHIM_AUTO_INSTALL"

AliasMapping = VersionMapping = Dict[str, str]


class HashableDict(dict):
    def __hash__(self):
        return hash(frozenset(self.items()))


def print_stylized(text, color):
    print(stylize(text, color))


def print_error(text: str):
    print_stylized(text, COLOR_ERROR)


def print_notice(text: str):
    print_stylized(text, COLOR_NOTICE)


def print_found_version(nvmrc_path: str, version: str):
    print(f"Found '{nvmrc_path}' with version <v{version}>\n")


def print_node_bin_file_not_provided():
    print(f"Node executable file was not supplied")


def print_node_bin_file_does_not_exist(bin_path: str):
    print(f"No executable file found at '{bin_path}'")


def print_version_not_installed(version: str):
    print_error(f"N/A version 'v{version}' is not yet installed.\n")
    print(
        "You need to run",
        stylize(f"'nvm install v{version}'", COLOR_NOTICE),
        "to install it before using it.\n",
    )
    print(
        "Or set the environment variable",
        stylize(f"'{ENV_VAR_AUTO_INSTALL}'", COLOR_NOTICE),
        "to auto install at run time.\n",
    )


def run(*args):
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError as error:
        exit(error.returncode)


def get_env_var(name: str, raise_missing: bool = False) -> object:
    try:
        return json.loads(os.environ[name])
    except KeyError:
        if raise_missing:
            print_error(f"Environment variable '{name}' missing")
            raise
    except json.decoder.JSONDecodeError:
        return os.environ.get(name)


def get_nvm_dir() -> str:
    return get_env_var(ENV_VAR_NVM_DIR, True)


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


def get_node_versions(node_versions_dir: str) -> VersionMapping:
    return {
        str(parse_version(v)): os.path.join(node_versions_dir, v, "bin")
        for v in os.listdir(node_versions_dir)
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
            print_found_version(nvmrc_path, version)
            return version

    return "default"


def get_bin_path(version: str, node_versions: VersionMapping, bin_file: str):
    try:
        node_path = node_versions[version]
    except KeyError:
        if not is_auto_install_version_enabled():
            print_version_not_installed(version)
            exit(ERROR_CODE_VERSION_NOT_INSTALLED)

        run(["nvm install", version])

    bin_path = os.path.join(node_path, bin_file)
    if not os.path.exists(bin_path):
        print_node_bin_file_does_not_exist(bin_path)
        exit(ERROR_CODE_EXECUTABLE_NOT_FOUND)

    return bin_path


def is_auto_install_version_enabled() -> bool:
    return bool(get_env_var(ENV_VAR_AUTO_INSTALL))


def get_args() -> [str]:
    try:
        [_, bin_file, *bin_args] = sys.argv
    except ValueError:
        print_node_bin_file_not_provided()
        exit(ERROR_CODE_EXECUTABLE_NOT_GIVEN)

    return bin_file, bin_args


def main():
    nvm_dir = get_nvm_dir()

    nvm_aliases_dir = get_nvm_aliases_dir(nvm_dir)
    nvm_aliases = get_nvm_aliases(nvm_aliases_dir)
    resolved_aliases = resolve_nvm_aliases(nvm_aliases)

    node_versions_dir = get_node_versions_dir(nvm_dir)
    node_versions = get_node_versions(node_versions_dir)

    all_versions = merge_nvm_aliases_with_node_versions(resolved_aliases, node_versions)

    nvmrc_path = get_nvmrc_path()
    nvmrc = get_nvmrc(nvmrc_path)

    bin_file, bin_args = get_args()
    bin_path = get_bin_path(nvmrc, all_versions, bin_file)
    run(bin_path, *bin_args)


if __name__ == "__main__":
    main()
