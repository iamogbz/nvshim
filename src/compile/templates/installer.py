import argparse
import os
import re
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
    shim_bin = {"__SHIM_BIN_PLACEHOLDER__"}
    shim_names = ["node", "npm", "npx"]
    for name in shim_names:
        file_path = os.path.join(path, name)
        with open(file_path, "wb") as shim_file:
            shim_file.write(shim_bin)
            os.chmod(file_path, os.stat(file_path).st_mode | stat.S_IEXEC)


def configure_profile(configuration: str, profile_path: str):
    profile_section = "## NVSHIM: DO NOT MODIFY"
    initial_profile = ""

    if os.path.exists(profile_path):
        with open(profile_path, "r") as profile:
            initial_profile = profile.read()

    wrapped_config = "\n".join([profile_section, configuration, profile_section])
    if profile_section in initial_profile:
        modified_profile = re.sub(
            pattern=f"{profile_section}(.|\\s)*{profile_section}",
            repl=wrapped_config,
            string=initial_profile,
        )
    else:
        modified_profile = "\n".join(filter(bool, [initial_profile, wrapped_config]))

    with open(profile_path, "w+") as profile:
        profile.write(modified_profile)


def configure_sh(install_path: str, profile_path: str):
    configure_profile(f"export PATH='{install_path}:$PATH'", profile_path)


def main():
    args = parse_args(sys.argv[1:])
    install_shims(args.install_path)
    if args.profile_path:
        configure_sh(args.install_path, args.profile_path)


if __name__ == "__main__":
    main()
