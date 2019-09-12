import re
from typing import Tuple

from git import InvalidGitRepositoryError, Repo

try:
    repo = Repo(".", search_parent_directories=True)
except InvalidGitRepositoryError:
    print("No repo found")
    repo = None


def get_repository_owner_and_name() -> Tuple[str, str]:
    """
    Checks the origin remote to get the owner and name of the remote repository.
    :return: A tuple of the owner and name.
    """
    if not repo:
        print("No repo")
        return
    url = repo.remote("origin").url
    parts = re.search(r"[:/]([^\.:]+)/([^/]+).git$", url)
    if not parts:
        print("No parts", url, parts)
        return
    print("get_repository_owner_and_name", parts)
    return parts.group(1), parts.group(2)


get_repository_owner_and_name()
