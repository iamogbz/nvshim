import os
import sys

import nvshim.core.__main__ as core
from nvshim.utils.constants import ErrorCode
from nvshim.utils.message import print_process_interrupted


def main():
    try:
        sys.argv.insert(1, os.path.basename(sys.argv[0]))
        core.main()
    except KeyboardInterrupt as e:
        print_process_interrupted(e)
        sys.exit(ErrorCode.KEYBOARD_INTERRUPT)


if __name__ == "__main__":
    main()
