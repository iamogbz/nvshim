import os

import semver

from nvshim.utils import process


dist_path = "dist"


def _is_valid_release_version(version: str) -> bool:
    try:
        return semver.parse_version_info(version)
    except:
        pass


def _clean():
    print("Cleaning...")
    process.run("rm", "-rf", dist_path)


def _build():
    print("Building...")
    process.run("python", "setup.py", "sdist", "bdist_wheel")


def _get_publish_command(*, dry_run: bool = True):
    cmd = ["twine", "upload"]
    if dry_run:
        cmd.extend(["--repository-url", "https://test.pypi.org/legacy/"])
    cmd.append(os.path.join(dist_path, "*"))
    return cmd


def _publish(*, dry_run: bool = True):
    print("Publishing...")
    print("Target:", "test.pypi.org" if dry_run else "pypi.org")
    process.run(*_get_publish_command(dry_run=dry_run))

    print("Publishing completed.")


def main():
    _clean()
    _build()
    from nvshim import __version__

    if __version__:
        _publish(dry_run=True)
    else:
        return print("No build version")

    if _is_valid_release_version(__version__):
        _publish(dry_run=False)
    else:
        return print("No release version")


if __name__ == "__main__":
    main()
