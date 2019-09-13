import os
import subprocess

import semver


def _get_publish_command(*, dry_run: bool = True):
    cmd = ["twine", "upload"]
    if dry_run:
        cmd.extend(["--repository-url", "https://test.pypi.org/legacy/"])
    cmd.append("dist/*")


def main():
    print(os.environ)
    completed_process = subprocess.run(_get_publish_command(dry_run=True), check=True)


if __name__ == "__main__":
    main()
