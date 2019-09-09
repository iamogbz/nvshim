import argparse
import os
import stat
import sys
from typing import Sequence

from utils.process import run


def parse_args(args: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install node version manager shim")
    parser.add_argument(
        "install_path", type=str, help="Path to location for node shims installation"
    )
    parser.add_argument(
        "profile_path",
        type=str,
        nargs="?",
        help="Path to profile to configure with exports",
    )

    return parser.parse_args(args)


def install_shims(path: str):
    shim_bin = {SHIM_BIN_PLACEHOLDER}
    shim_names = ["node", "npm", "npx"]
    for name in shim_names:
        file_path = os.path.join(path, name)
        with open(file_path, "wb") as shim_file:
            shim_file.write(shim_bin)
            os.chmod(file_path, os.stat(file_path).st_mode | stat.S_IEXEC)


def configure_profile(profile_path: str):
    profile_section = "## NVSHIM'D"
    with open(profile_path) as profile:
        initial_profile = profile.read()

    modified_profile = initial_profile

    with open(profile_path) as profile:
        profile.write(modified_profile)


def main():
    args = parse_args(sys.argv[1:])
    install_shims(args.install_path)
    if args.profile_path:
        configure_profile(args.profile_path)


if __name__ == "__main__":
    main()
