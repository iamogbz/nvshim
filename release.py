import os
import re
import subprocess
from contextlib import contextmanager
from datetime import datetime

import semver

import nvshim as version_pkg
from nvshim.utils import process


dist_path = "dist"


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
    with open(version_pkg.__file__, "r") as f:
        file_content = f.read()
    try:
        with open(version_pkg.__file__, "w") as f:
            print("Setting version to:", version)
            f.write(file_content.replace("0.0.0", version))
        yield
    finally:
        with open(version_pkg.__file__, "w") as f:
            print("Restoring version")
            f.write(file_content)


def _get_build_command():
    return ["python", "setup.py", "sdist", "bdist_wheel"]


def _get_publish_command(*, dry_run: bool = True):
    cmd = ["twine", "upload"]
    if dry_run:
        cmd.extend(["--repository-url", "https://test.pypi.org/legacy/"])
    cmd.append(os.path.join(dist_path, "*"))
    return cmd


def _publish(*, version: str, dry_run: bool = True):
    print("Cleaning up")
    process.run("rm", "-rf", dist_path)

    if dry_run:
        now = datetime.now()
        seconds = now.hour * now.minute * now.second
        version = f"{now.year}.{now.month}.{now.day}.{seconds}"

    with _setup_version(version):
        print("Building version:", version)
        process.run(*_get_build_command())
        print("Publishing to:", "test.pypi.org" if dry_run else "pypi.org")
        process.run(*_get_publish_command(dry_run=dry_run))

    print("Publishing completed.")


def main():
    ref = _get_ref_name()
    if ref:
        _publish(version=ref, dry_run=True)
    else:
        return print("No reference version")
    if _is_valid_release_version(ref):
        _publish(version=ref, dry_run=False)
    else:
        return print("No release version")


if __name__ == "__main__":
    main()
