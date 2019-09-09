import os

from utils.process import run


def _get_template_file_path(filename: str) -> str:
    return os.path.realpath(os.path.join(__file__, f"../templates/{filename}.py"))


def _build_dist(name: str):
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
        _get_template_file_path(name),
    )
    return os.path.join(dist_path, name)


def build_installer(shim_bin: bytes):
    """Build installer exec for a particular nvshim version binary"""
    name = "installer"

    py_file_path = _get_template_file_path(name)
    with open(py_file_path, "r") as f:
        content = f.read().replace("{SHIM_BIN_PLACEHOLDER}", str(shim_bin))
    with open(py_file_path, "w") as f:
        f.write(content)

    return _build_dist(name)


def build_shim() -> str:
    """Build shim executable and return path to distributable"""
    return _build_dist("shim")


def main():
    shim_path = build_shim()
    with open(shim_path, "rb") as shim_file:
        build_installer(shim_file.read())


if __name__ == "__main__":
    main()
