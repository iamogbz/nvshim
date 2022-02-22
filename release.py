"""Release to pypi deploy logic"""
import importlib
import os

import semver

import nvshim
from nvshim.utils import process

DIST_PATH = "dist"


def _is_valid_release_version(version: str) -> bool:
    try:
        return bool(semver.VersionInfo.parse(version))
    except ValueError:
        return False


def _clean():
    print("Cleaning...")
    process.run("rm", "-rf", DIST_PATH)


def _build():
    print("Building...")
    process.run("python", "setup.py", "sdist", "bdist_wheel")


def _get_publish_command(*, dry_run: bool = True):
    cmd = ["twine", "upload", "--skip-existing"]
    if dry_run:
        cmd.extend(["--repository-url", "https://test.pypi.org/legacy/"])
    cmd.append(os.path.join(DIST_PATH, "*"))
    return cmd


def _publish(*, dry_run: bool = True):
    print("Target:", "test.pypi.org" if dry_run else "pypi.org")
    process.run(*_get_publish_command(dry_run=dry_run))

    print("Publishing completed.")


def main():
    """Run main release logic"""
    _clean()
    _build()

    __version__ = importlib.reload(nvshim).__version__
    print(f"Publishing: {__version__}")

    if __version__:
        _publish(dry_run=True)
    else:
        return print("No build version")

    if _is_valid_release_version(__version__):
        _publish(dry_run=False)
    else:
        return print("No release version")

    return None


if __name__ == "__main__":
    main()
