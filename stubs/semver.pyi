# pylint: skip-file
from distutils.version import Version

class VersionInfo:
    @classmethod
    def parse(cls, version: str) -> VersionInfo: ...
