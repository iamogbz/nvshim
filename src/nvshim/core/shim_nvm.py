"""Shim nvm for running nvm commands"""
import shlex
import sys

import nvshim.core.__main__ as core


def main():
    """Pipe arguments to run nvm command"""
    nvm_args = " ".join(shlex.quote(arg) for arg in sys.argv[1:])
    core.run_nvm_cmd(core.get_nvmsh_path(core.get_nvm_dir()), nvm_args)


if __name__ == "__main__":
    main()
