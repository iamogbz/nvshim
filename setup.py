import os
from setuptools import setup
from typing import Sequence

from compiler import __version__


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
            if line.startswith(req_file_delim):
                nested_req_file = line.split(req_file_delim)[1].strip()
                nested_req_filepath = os.path.join(requirements_dir, nested_req_file)
                requirements.union(get_requirements(nested_req_filepath, visited))

            elif req_package_delim in line:
                requirements.add(line.split(req_package_delim)[0])

    return list(requirements)


setup(
    author="Emmanuel Ogbizi-Ugbe",
    author_email="iamogbz+pypi@gmail.com",
    description="Automagically use the correct version of node",
    install_requires=get_requirements("requirements/prod.txt", []),
    keywords="node nvm node-shim shim shell nvm-shim",
    long_description=readme(),
    license="GNU",
    name="nvshim",
    scripts=[f"dist/{filename}" for filename in ["node", "npm", "npx"]],
    tests_require=get_requirements("requirements/test.txt", []),
    url="http://github.com/iamogbz/nvshim",
    version=__version__,
)
