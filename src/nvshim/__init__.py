import os

try:
    version_file_path = os.path.realpath(__file__, "../../version.txt")
    with open(version_file_path, "r") as f:
        __version__ = f.read()
except:
    __version__ = "0.0.0"
