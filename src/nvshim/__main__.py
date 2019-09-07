import functools
import json
import os
from typing import Dict

from colored import fg, bg, attr
import semver

COLOR_ERROR = fg("red")
COLOR_RESET = attr("reset")

AliasMapping = Dict[str, str]


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


def get_nvm_alias_dir(nvm_dir):
    return os.path.join(nvm_dir, "alias")


def get_nvm_aliases(nvm_alias_dir: str) -> AliasMapping:
    aliases_to_version = HashableDict()
    for file_path in get_files(nvm_alias_dir):
        rel_path = os.path.relpath(file_path, nvm_alias_dir)
        with open(file_path) as f:
            aliases_to_version[rel_path] = f.readline().strip()

    return aliases_to_version


def parse_version(version: str) -> semver.VersionInfo:
    try:
        if version.startswith("v"):
            version = version[1:]
        return semver.parse_version_info(version)
    except ValueError:
        pass


@functools.lru_cache(maxsize=None)
def resolve_alias(
    name: str, alias_mapping: AliasMapping
) -> (semver.VersionInfo, str, [str]):
    seen_in_order = []
    seen = set()
    while name in alias_mapping and name not in seen:
        name = alias_mapping.get(name)
        seen_in_order.append(name)
        seen.add(name)

    return parse_version(name), name, seen_in_order


def resolve_nvm_aliases(nvm_aliases: AliasMapping):
    resolved_aliases = {}
    for alias, version in nvm_aliases.items():
        version_info = parse_version(version)
        if not version_info:
            version_info = resolve_alias(version, nvm_aliases)[0]

        if version_info:
            resolved_aliases[alias] = str(version_info)

    return resolved_aliases


# get mapping of aliases to node versions
# get available node versions
# get nvmrc or use default
# return path to node or npm
if __name__ == "__main__":
    nvm_dir = get_nvm_dir()
    nvm_alias_dir = get_nvm_alias_dir(nvm_dir)
    nvm_aliases = get_nvm_aliases(nvm_alias_dir)
    print(resolve_nvm_aliases(nvm_aliases))
