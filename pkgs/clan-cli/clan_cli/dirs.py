import os
import sys
from pathlib import Path

from .errors import ClanError


def get_clan_flake_toplevel() -> Path:
    """Returns the path to the toplevel of the clan flake"""
    for project_file in [".clan-flake", ".git", ".hg", ".svn", "flake.nix"]:
        initial_path = Path(os.getcwd())
        path = Path(initial_path)
        while path.parent != path:
            if (path / project_file).exists():
                return path
            path = path.parent
    raise ClanError("Could not find clan flake toplevel directory")


def user_config_dir() -> Path:
    if sys.platform == "win32":
        return Path(os.getenv("APPDATA", os.path.expanduser("~\\AppData\\Roaming\\")))
    elif sys.platform == "darwin":
        return Path(os.path.expanduser("~/Library/Application Support/"))
    else:
        return Path(os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config")))