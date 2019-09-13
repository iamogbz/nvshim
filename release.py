import os
import subprocess

import semver

from nvshim.utils import process


def _get_publish_command(*, dry_run: bool = True):
    cmd = ["twine", "upload"]
    if dry_run:
        cmd.extend(["--repository-url", "https://test.pypi.org/legacy/"])
    cmd.append("dist/*")
    return cmd


def main():
    print(os.environ)
    completed_process = process.run(*_get_publish_command(dry_run=True))


if __name__ == "__main__":
    main()
