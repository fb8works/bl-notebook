import configparser
import os
from pathlib import Path

from bl_notebook.util import is_win32

PREFIX = "BL_NOTEBOOK_"


def get_default_config_path():
    return os.getenv(
        PREFIX + "CONFIG", "~/.config/bl-notebook/config.ini"
    ).strip()


class PathConfig:
    def __init__(self):
        self.cache_dir = os.getenv(
            PREFIX + "CACHE_DIR", "~/.cache/bl-notebook"
        ).strip()
        self.apps_root = os.getenv(PREFIX + "APP_DIR", "").strip()
        self.search_path = os.getenv(PREFIX + "SEARCH_PATH", "").strip()
        self.mirror = os.getenv(
            PREFIX + "MIRROR",
            "https://mirrors.ocf.berkeley.edu/blender/release/",
        ).strip()


class PathConfigWin(PathConfig):
    def __init__(self):
        super().__init__()
        if self.apps_root.strip() == "":
            self.apps_root = "C:\\app\\blender"
        if self.search_path.strip() == "":
            self.search_path = (
                self.apps_root + ";C:\\Program Files\\Blender Foundation"
            )


class PathConfigUnix(PathConfig):
    def __init__(self):
        super().__init__()
        if self.apps_root.strip() == "":
            self.apps_root = "~/.local/blender"
        if self.search_path.strip() == "":
            self.search_path = (
                self.apps_root + ";~/.local/bin;/usr/local/bin;/usr/bin"
            )


def _get_default_config() -> dict:
    if is_win32():
        path_config = PathConfigWin()
    else:
        path_config = PathConfigUnix()
    return {
        "main": {
            "cache_dir": path_config.cache_dir,
        },
        "blender": {
            "version": "",
            "apps_root": path_config.apps_root,
            "search_path": path_config.search_path,
            "mirror": path_config.mirror,
        },
    }


class Config:
    def __init__(self, config_path=None, no_defaults=False):
        if config_path is None:
            config_path = get_default_config_path()
        self.config_path = Path(config_path).expanduser()
        self.config = configparser.RawConfigParser()
        if not no_defaults:
            defaults = _get_default_config()
            for section, value in defaults.items():
                self.config[section] = value
        self.config.read(self.config_path)

    def save(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as configfile:
            self.config.write(configfile)

    def get(self, section, option, **kwargs):
        return self.config.get(section, option, **kwargs)

    def getint(self, section, option, **kwargs):
        return self.config.getint(section, option, **kwargs)

    def getfloat(self, section, option, **kwargs):
        return self.config.getfloat(section, option, **kwargs)

    def set(self, section, option, value):  # noqa: A003
        self.config.set(section, option, value)
