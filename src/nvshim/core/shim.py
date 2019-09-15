import os
import sys

import nvshim.core.__main__ as core


def main():
    sys.argv.insert(1, os.path.basename(sys.argv[0]))
    core.main()


if __name__ == "__main__":
    main()
