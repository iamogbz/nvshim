import os
import re
import subprocess
from contextlib import contextmanager
from datetime import datetime

import semver

from nvshim.utils import process


version_file = os.path.join("src", "nvshim", "__init__.py")


def _get_ref_name() -> str:
    """
    Gotten from the environment variable $GITHUB_REF
    Examples: refs/heads/branch-name, refs/tags/v0.0.0
    """
    github_ref = os.environ.get("GITHUB_REF", "")
    result = re.match(r"refs\/\w+\/(.*)", github_ref)
    return result and result.group(1)


def _is_valid_release_version(version: str) -> bool:
    try:
        return version.startswith("v") and semver.parse_version_info(version[1:])
    except:
        pass


@contextmanager
def _setup_version(version: str):
    with open(version_file, "r") as f:
        file_content = f.read()
    try:
        with open(version_file, "w") as f:
            print("Setting version to:", version)
            f.write(file_content.replace("0.0.0", version))
        yield
    finally:
        with open(version_file, "w") as f:
            print("Restoring version")
            f.write(file_content)


def _get_publish_command(*, dry_run: bool = True):
    cmd = ["twine", "upload"]
    if dry_run:
        cmd.extend(["--repository-url", "https://test.pypi.org/legacy/"])
    cmd.append("dist/*")
    return cmd


def main():
    version = _get_ref_name()
    if not version:
        print("No ref found")
        return

    timestamp = datetime.now()
    test_version = f"{version}-{timestamp}"
    with _setup_version(test_version):
        print("Publishing to sandbox: ", test_version)
        process.run(*_get_publish_command(dry_run=True))

    if not _is_valid_release_version(version):
        print("Skipping publishing to pypi")
        return

    with _setup_version(version):
        print("Publishing to pypi:", version)
        process.run(*_get_publish_command(dry_run=False))

    print("Finished publishing release version")


if __name__ == "__main__":
    main()
