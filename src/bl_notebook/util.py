import hashlib
import platform
import random
import re
import shlex
import subprocess
import sys
from contextlib import suppress
from pathlib import Path
from textwrap import indent
from typing import Optional, Union

from bl_notebook.blender.ostype import OSType

NOTEBOOK_AUTH_SALT_LEN = 12  # notebook.auth.salt_len


def is_win32():
    return re.match(r"^Windows-", platform.platform())


def print_error(*args, dry_run=False, **kwargs):
    prefix = ("", "SKIP(dry-run) ")[int(bool(dry_run))]
    args = (prefix + str(args[0]),) + args[1:]
    print(*args, **kwargs, file=sys.stderr)


def print_command(cmd, dry_run=False, **kwargs):
    print_error("RUN: " + shlex.join(map(str, cmd)), dry_run=dry_run, **kwargs)


def make_executable_filename(path: Path, ostype):
    ostype = OSType(ostype)
    if ostype == OSType.ANY and is_win32():
        ostype = OSType.WINDOWS
    if ostype == OSType.WINDOWS and not re.search(r"\.exe$", str(path), re.I):
        return path.with_suffix(".exe")
    return path


def run_command(
    cmd,
    verbose=False,
    show_nonzero=True,
    dry_run=False,
    fail_on_exit=False,
    yes: Optional[Union[str, bytes, bool]] = None,
    **kwargs,
) -> Optional[int]:
    if verbose or dry_run:
        print_command(cmd, dry_run=dry_run)
        if dry_run:
            return None

    def print_command_and_error(message):
        if not verbose:
            print_command(cmd)
        print_error(f"Command failed ({message})")

    try:
        if yes:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, **kwargs)
        else:
            proc = subprocess.Popen(cmd, **kwargs)
    except OSError as exc:
        print_command_and_error(str(exc))
        raise

    if yes:
        if isinstance(yes, str):
            yes = yes.encode("utf-8")
        elif not isinstance(yes, bytes):
            yes = b"Y"
        with suppress(BrokenPipeError):
            while True:
                proc.stdin.write(yes + b"\n")
    else:
        proc.communicate()

    code = proc.wait()
    if code != 0:
        if show_nonzero:
            print_command_and_error(f"Exited by {code}")
        if fail_on_exit:
            sys.exit(code)

    return code


def make_password(plain_password):
    salt_len = NOTEBOOK_AUTH_SALT_LEN
    h = hashlib.new("sha1")
    salt = f"{random.getrandbits(4 * salt_len):0{salt_len}x}"
    h.update(plain_password.encode("utf-8") + salt.encode("ascii"))
    password = ":".join(("sha1", salt, h.hexdigest()))
    return password


def normalize_path(path):
    is_obj = isinstance(path, Path)
    p = str(path)
    p = Path(p).expanduser()
    if not is_obj:
        p = str(p)
    return p


def get_ip_address_win(interface_name):
    try:
        output = subprocess.check_output(
            ["netsh", "interface", "ipv4", "show", "addresses", interface_name]
        )
    except subprocess.CalledProcessError as e:
        print_error("netsh command exited by non zero")
        print_error(indent(e.output.decode("utf-8"), "  "))
        sys.exit(1)

    for line in output.decode("utf-8").split("\n"):
        m = re.match(r"^\s*IP Address:\s*([.0-9]+)\s*$", line)
        if m:
            return m.group(1)
    return None
