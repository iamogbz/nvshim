import os
import json
from colored import fg, bg, attr
import semver

COLOR_ERROR = fg("red")
COLOR_RESET = attr("reset")


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


def get_nvm_aliases():
    nvm_aliases_dir = os.path.join(get_nvm_dir(), "alias")
    aliases_to_version = {}
    for file_path in get_files(nvm_aliases_dir):
        rel_path = os.path.relpath(file_path, nvm_aliases_dir)
        with open(file_path) as f:
            aliases_to_version[rel_path] = f.readline().strip()

    return aliases_to_version


# get mapping of aliases to node versions
# get available node versions
# get nvmrc or use default
# return path to node or npm
if __name__ == "__main__":
    print(get_nvm_aliases())
