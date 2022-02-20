import os
import shlex
import sys

from nvshim.utils.environment import get_nvm_dir, process_env
from nvshim.utils.process import run_with_error_handler
from nvshim.utils import message


def main():
    nvm_sh_file_path = f"{get_nvm_dir()}/nvm.sh"
    nvshim_file_path = f"{os.path.dirname(sys.argv[0])}/nvm_shim.sh.tmp"
    try:
        with open(nvshim_file_path, "w") as nvshim_file:
            nvm_command = shlex.join(["nvm"] + sys.argv[1:])
            nvshim_file.write(f"source {nvm_sh_file_path}\n{nvm_command}")
        run_with_error_handler("bash", nvshim_file_path)
    finally:
        try:
            os.remove(nvshim_file_path)
        except Exception as e:
            message.print_unable_to_remove_nvm_shim_temp_file(e)


if __name__ == "__main__":
    main()
