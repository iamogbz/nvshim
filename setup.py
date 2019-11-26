import sys
from datetime import datetime

sys.path.append("src")

import os
from setuptools import setup
from typing import Sequence

from nvshim.utils.constants import shims


def readme() -> str:
    with open("README.md") as f:
        return f.read()


def lines(filepath) -> Sequence[str]:
    """Lines of a file generator"""
    with open(filepath) as f:
        while True:
            line = f.readline().strip()
            if line:
                yield line
            else:
                return


def get_requirements(filepath: str, visited: [str]) -> [str]:
    """
    Get all pip requirements specified by a requirements file
    with support for nested requirements files

    :param filepath: path to requirements.txt file
    :param visited: mutable list of visited requirements.txt files
    :return: unordered list of requirements without versions
    """
    requirements = set()
    filepath = os.path.realpath(filepath)
    rel_filepath = os.path.relpath(filepath)

    if filepath in visited:
        print("Skipping requirements:", rel_filepath)
        print(visited)

    else:
        print("Parsing requirements:", rel_filepath)
        visited.append(filepath)
        req_file_delim = "-r"
        req_package_delim = "=="
        requirements_dir = os.path.dirname(filepath)
        for line in lines(filepath):
            if line.startswith("#"):
                continue
            if line.startswith(req_file_delim):
                nested_req_file = line.split(req_file_delim)[1].strip()
                nested_req_filepath = os.path.join(requirements_dir, nested_req_file)
                requirements.union(get_requirements(nested_req_filepath, visited))
            elif req_package_delim in line:
                requirements.add(line.split(req_package_delim)[0])

    return list(requirements)


def version_scheme(version):
    if version.exact:
        return version.format_with("{tag}")
    else:
        now = datetime.now()
        seconds = (now.hour * 60) + (now.minute * 60) + now.second
        return f"{now.year}.{now.month}.{now.day}.{seconds}"


setup(
    author="Emmanuel Ogbizi-Ugbe",
    author_email="iamogbz+pypi@gmail.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Software Development",
    ],
    description="Automagically use the correct version of node",
    entry_points={"console_scripts": [f"{s}=nvshim.core.shim:main" for s in shims]},
    include_package_data=True,
    install_requires=get_requirements("requirements/prod.txt", []),
    keywords="node nvm node-shim shim shell nvm-shim",
    long_description=readme(),
    long_description_content_type="text/markdown",
    license="GNU",
    name="nvshim",
    packages=["nvshim", "nvshim.core", "nvshim.utils"],
    package_dir={"": "src"},
    setup_requires=["setuptools_scm"],
    tests_require=get_requirements("requirements/test.txt", []),
    url="http://github.com/iamogbz/nvshim",
    use_scm_version={
        "local_scheme": lambda _: "",
        "version_scheme": version_scheme,
        "write_to": "./src/nvshim/__init__.py",
        "write_to_template": '__version__ = "{version}"\n',
    },
)
