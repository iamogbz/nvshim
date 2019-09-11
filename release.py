import sys

import semantic_release

try:
    ARGS = sorted(sys.argv[1:], key=lambda x: 1 if x.startswith("--") else -1)
    semantic_release.cli.main(args=ARGS)
except Exception as e:
    print(e)
