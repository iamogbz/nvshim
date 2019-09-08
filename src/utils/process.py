import subprocess


def run(*args, **kwargs):
    try:
        subprocess.run(args, **kwargs, check=True)
    except subprocess.CalledProcessError as error:
        exit(error.returncode)
