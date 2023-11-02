from pathlib import Path

import win32com.client
from win32com.shell import shell, shellcon

from .util import print_error

_WSHELL = win32com.client.Dispatch("Wscript.Shell")


def register_startmenu(
    executable,
    name,
    description=None,
    arguments="",
    window_style=0,
    verbose=False,
):
    folder = Path(shell.SHGetFolderPath(0, shellcon.CSIDL_PROGRAMS, None, 0))
    folder = folder.resolve(strict=False)
    name = name + ".lnk"
    dest = str(folder / name)
    folder.mkdir(parents=True, exist_ok=True)
    Path(dest).unlink(missing_ok=True)
    if description is None:
        description = name
    if verbose:
        print_error(f"A shortcut named {str(dest)} was created.")
    create_shortcut(
        dest,
        target_path=executable,
        description=name,
        arguments=arguments,
        window_style=window_style,
    )


def create_shortcut(
    dest, target_path, description, arguments="", window_style=0
):
    wscript = _WSHELL.CreateShortCut(str(dest))
    wscript.Targetpath = f'"{str(target_path)}"'
    wscript.Arguments = arguments
    wscript.WorkingDirectory = str(Path(target_path).parent)
    wscript.WindowStyle = window_style
    wscript.Description = description
    wscript.IconLocation = str(target_path)
    wscript.save()
