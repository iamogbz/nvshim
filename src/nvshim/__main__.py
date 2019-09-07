import functools
import json
import os
from typing import Dict

from colored import fg, bg, attr
import semver

COLOR_ERROR = fg("red")
COLOR_RESET = attr("reset")

AliasMapping = VersionMapping = Dict[str, str]


class HashableDict(dict):
    def __hash__(self):
        return hash(frozenset(self.items()))


def print_error(text: str):
    print(f"{COLOR_ERROR}{text}{COLOR_RESET}")


def get_env_var(name: str, raise_missing: bool = False) -> object:
    try:
        return json.loads(os.environ[name])
    except KeyError:
        print_error(f"Environment variable '{name}' missing")
        if raise_missing:
            raise
    except json.decoder.JSONDecodeError:
        return os.environ.get(name)


def get_nvm_dir() -> str:
    return get_env_var("NVM_DIR", True)


def get_files(path: str) -> [str]:
    """
    Generate the file paths to traverse, or a single path if a file name was given
    """
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
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


def get_nvmrc_path(exec_dir: str = "") -> str:
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


# get nvmrc or use default
# return path to node or npm
if __name__ == "__main__":
    nvm_dir = get_nvm_dir()
    nvm_aliases_dir = get_nvm_aliases_dir(nvm_dir)
    nvm_aliases = get_nvm_aliases(nvm_aliases_dir)
    resolved_aliases = resolve_nvm_aliases(nvm_aliases)
    node_versions_dir = get_node_versions_dir(nvm_dir)
    node_versions = get_node_versions(node_versions_dir)
    all_versions = merge_nvm_aliases_with_node_versions(resolved_aliases, node_versions)
    print(all_versions)
    nvmrc_path = get_nvmrc_path()
    print(nvmrc_path)
