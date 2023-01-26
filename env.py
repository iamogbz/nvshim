"""Module to help configure python app build system path to include the package source"""
import sys

# Relative to this file
PACKAGE_SOURCE = "./src"

sys.path.insert(0, PACKAGE_SOURCE)
