"""Shim node binaries for running node commands"""
import os
import sys

import nvshim.core.__main__ as core


def main():
    """Pipe arguments to run specific node binary"""
    sys.argv.insert(1, os.path.basename(sys.argv[0]))
    core.main()


if __name__ == "__main__":
    main()
