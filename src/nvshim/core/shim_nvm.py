import os
import shlex
import sys

import nvshim.core.__main__ as core


def main():
    core.run_nvm_cmd(core.get_nvmsh_path(core.get_nvm_dir()), shlex.join(sys.argv[1:]))


if __name__ == "__main__":
    main()
