import os
from typing import Union

from nvshim.utils.process import run


FileContents = Union[bytes, str]


def _get_script_file_path(filename: str) -> str:
    return os.path.realpath(os.path.join(__file__, f"../{filename}.py"))


def _read_file(path: str, mode: str = "r") -> FileContents:
    with open(path, mode) as f:
        contents = f.read()

    return contents


def _write_file(path: str, contents: FileContents, mode: str = "w"):
    with open(path, mode) as f:
        f.write(contents)


def _build_dist(name: str, *, build_args: [str] = [], script_file_name: str = None):
    dist_path = "dist"
    run(
        "pyinstaller",
        "-F",
        "-n",
        name,
        "-p",
        "src",
        "--distpath",
        dist_path,
        "--specpath",
        "artifacts",
        _get_script_file_path(script_file_name or name),
        *build_args,
    )
    return os.path.join(dist_path, name)


def build_installer(shim_bin: bytes):
    """Build installer exec for a particular nvshim version binary"""
    name = "installer"

    py_file_path = _get_script_file_path(name)
    original_content = _read_file(py_file_path)
    try:
        _write_file(
            py_file_path,
            original_content.replace('{"__SHIM_BIN_PLACEHOLDER__"}', str(shim_bin)),
        )
        return _build_dist(name)
    finally:
        _write_file(py_file_path, original_content)


def build_shim() -> str:
    """Build shim executable and return path to distributable"""
    return _build_dist("shim")


def main():
    build_installer(_read_file(build_shim(), "rb"))


if __name__ == "__main__":
    main()
