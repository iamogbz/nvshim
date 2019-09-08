import os

from utils.process import run


def build_shim(name: str):
    src_base = "src"
    src_file = os.path.join(src_base, "compile", "template.py")
    run(
        "pyinstaller",
        "-F",
        "-n",
        name,
        "-p",
        src_base,
        "--specpath",
        "artifacts",
        src_file,
    )


def main():
    for shim in ["node", "npm", "npx"]:
        build_shim(shim)


if __name__ == "__main__":
    main()
