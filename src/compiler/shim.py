import os
import sys

from nvshim.__main__ import main


def entry():
    sys.argv.insert(1, os.path.basename(sys.argv[0]))
    main()


if __name__ == "__main__":
    entry()
