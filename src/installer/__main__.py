import argparse
import os
import re
import stat
import sys
from typing import Sequence

from utils import message


def parse_args(args: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install node version manager shim")
    parser.add_argument(
        "install_path",
        type=str,
        nargs="?",
        help="Path to location for node shims installation",
        default=os.path.join(os.path.expanduser("~"), ".nvshim"),
    )
    parser.add_argument(
        "profile_path",
        type=str,
        nargs="?",
        help="Path to profile to configure with exports",
    )

    return parser.parse_args(args)


def install_shims(shim_bin: bytes, install_path: str):
    os.makedirs(install_path, exist_ok=True)
    shim_names = ["node", "npm", "npx"]
    for name in shim_names:
        file_path = os.path.join(install_path, name)
        with open(file_path, "wb") as shim_file:
            shim_file.write(shim_bin)
            os.chmod(file_path, os.stat(file_path).st_mode | stat.S_IEXEC)
            message.print_installed_shim(file_path)


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
        message.print_updated_profile(profile_path, configuration)


def configure_sh(install_path: str, profile_path: str):
    configure_profile(f'export PATH="{install_path}:$PATH"', profile_path)


def main(shim_bin: bytes):
    args = parse_args(sys.argv[1:])
    install_path = os.path.realpath(args.install_path)
    install_shims(shim_bin, install_path)
    if args.profile_path:
        configure_sh(install_path, args.profile_path)

    message.print_install_complete()


if __name__ == "__main__":
    main()
