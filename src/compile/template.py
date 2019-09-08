import os
import sys

from nvshim.__main__ import main

sys.argv.insert(1, os.path.basename(sys.argv[0]))
main()
