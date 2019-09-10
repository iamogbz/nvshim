from setuptools import setup
from compiler import __version__


def readme():
    with open("README.md") as f:
        return f.read()


setup(
    author="Emmanuel Ogbizi-Ugbe",
    author_email="iamogbz+pypi@gmail.com",
    description="Automagically use the correct version of node",
    keywords="node nvm node-shim shim shell nvm-shim",
    long_description=readme(),
    license="GNU",
    name="nvshim",
    scripts=[f"dist/{filename}" for filename in ["node", "npm", "npx"]],
    url="http://github.com/iamogbz/nvshim",
    version=__version__,
)
