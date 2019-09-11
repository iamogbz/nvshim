import argparse
from functools import reduce
import os
import re
import stat
import sys
from typing import Sequence

from compiler import __version__
from utils import message


def parse_args(args: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install node version manager shim")
    parser.add_argument(
        "install_path",
        type=str,
        metavar="NVSHIM_DIR",
        help="Path to location for node shims installation",
    )
    parser.add_argument(
        "profile_paths",
        type=str,
        nargs="*",
        metavar="PROFILE",
        help="Paths to profiles to configure with exports",
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


def configure_profile(config: str, *paths: [str]):
    config_border = "## NVSHIM: DO NOT MODIFY"

    def _with_border(content: str) -> str:
        return f"{config_border}{content}{config_border}"

    for profile_path in paths:
        profile_content = ""
        if os.path.exists(profile_path):
            with open(profile_path, "r") as profile:
                profile_content = profile.read()

        profile_config = _with_border(f"\n{config}\n")
        if config_border in profile_content:
            modified_profile = re.sub(
                pattern=_with_border("(.|\\s)*"),
                repl=profile_config,
                string=profile_content,
            )
        else:
            modified_profile = (
                f"{profile_content}{profile_config}"
                if profile_content
                else profile_config
            )

        with open(profile_path, "w+") as profile:
            profile.write(modified_profile)
            message.print_updated_profile(profile_path, config)


def configure_sh(install_path: str, *profile_paths: [str]):
    configure_profile(f'export PATH="{install_path}:$PATH"', *profile_paths)


def parse_path(path: str) -> str:
    return reduce(
        lambda p, r: r(p),
        [os.path.expanduser, os.path.expandvars, os.path.realpath],
        path,
    )


def main(shim_bin: bytes, version_number: str = __version__):
    message.print_installing_version(version_number)

    defaults = {0: os.path.join(os.path.expanduser("~"), ".nvshim")}
    argv = {i: value for i, value in enumerate(sys.argv[1:])}
    envs = {
        i: os.environ.get(env_var)
        for i, env_var in enumerate(["NVSHIM_DIR", "PROFILE"])
        if env_var in os.environ
    }
    args = parse_args({**defaults, **argv, **envs}.values())

    install_path = parse_path(args.install_path)
    install_shims(shim_bin, install_path)
    if args.profile_paths:
        configure_sh(install_path, *map(parse_path, args.profile_paths))

    message.print_install_complete()


if __name__ == "__main__":
    main()
