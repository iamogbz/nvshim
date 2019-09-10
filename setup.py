from setuptools import setup
from compiler import __version__


def readme() -> str:
    with open("README.md") as f:
        return f.read()


def get_requirements(filepath: str, parents: [str]) -> [str]:
    requirements = set()
    with open(filepath) as f:
        parents.append(filepath)
        while True:
            line = f.readline().strip()
            req_file_delim = "-r"
            req_package_delim = "=="
            if not line:
                break
            elif line.startswith(req_file_delim):
                nested_requirements_file = line.split(req_file_delim)[1].trim()
                if nested_requirements_file in parents:
                    print("Recursive requirement dependency chain", filepath, parents)
                    break

                requirements.union(get_requirments(nested_requirements_file, parents))
            elif req_package_delim in line:
                requirements.add(line.split(req_package_delim)[0])

    return list(requirements)


def install_requirements() -> [str]:
    return get_requirements("requirements/prod.txt", [])


def test_requirements() -> [str]:
    return get_requirements("requirements/test.txt", [])


setup(
    author="Emmanuel Ogbizi-Ugbe",
    author_email="iamogbz+pypi@gmail.com",
    description="Automagically use the correct version of node",
    install_requires=install_requirements(),
    keywords="node nvm node-shim shim shell nvm-shim",
    long_description=readme(),
    license="GNU",
    name="nvshim",
    scripts=[f"dist/{filename}" for filename in ["node", "npm", "npx"]],
    tests_require=test_requirements(),
    url="http://github.com/iamogbz/nvshim",
    version=__version__,
)
