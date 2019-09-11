import sys

from semantic_release import cli

try:
    ARGS = sorted(sys.argv[1:], key=lambda x: 1 if x.startswith("--") else -1)
    cli.main(args=ARGS)
except Exception as e:
    print(e)
