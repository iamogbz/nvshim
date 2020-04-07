import os
import sys

import nvshim.core.__main__ as core


def main():
    try:
        sys.argv.insert(1, os.path.basename(sys.argv[0]))
        core.main()
    except KeyboardInterrupt as e:
        print(f'Interrupted: {e}')
        return 130


if __name__ == "__main__":
    main()
