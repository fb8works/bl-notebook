import platform
import re
import sys
from pathlib import Path

import click

from .blender.arch import Architecture
from .blender.criteria import Criteria
from .blender.install_app import BlenderNotFound, get_blender_install
from .blender.ostype import OSType
from .blender.repository import Repository
from .blender.version import Version
from .config import Config
from .notebook import NotebookManager
from .util import get_ip_address_win, is_win32, print_error, run_command

config = Config()


def get_blender_version(d=None):
    if d is None:
        d = Path(".").resolve()

    for name in (".blender-version", ".blender_version"):
        f = d / name
        if f.exists():
            with open(f) as fh:
                return fh.read().strip(" \r\n\t")

    # NOTE: str(d) == d.root is not work for windows.
    if d == d.parent:
        return None

    d = d.parent

    return get_blender_version(d)


def get_parameter_non_default(name):
    ctx = click.get_current_context()
    source = ctx.get_parameter_source(name)
    if source == click.core.ParameterSource.DEFAULT:
        return None
    return ctx.params[name]


@click.command(
    context_settings={
        "show_default": True,
        "help_option_names": ["-h", "--help"],
    }
)
@click.option(
    "-b",
    "--blender-version",
    default=get_blender_version(),
    help="Specify blender version.",
)
@click.option(
    "-B",
    "--set-blender-version",
    default=None,
    help="Set the default blender version.",
)
@click.option(
    "-d",
    "--show-directory",
    is_flag=True,
    help="Show the installed blender directory.",
)
@click.option(
    "-p",
    "--show-python-executable",
    is_flag=True,
    help="Show the installed blender's python executable path.",
)
@click.option(
    "--strict", is_flag=True, help="Strictly check the architecture."
)
@click.option("-r", "--remote", is_flag=True, help="Remote mode (with -l).")
@click.option("-I", "--install", is_flag=True, help="Only install blender.")
@click.option(
    "-l",
    "--list",
    "--list-blender",
    "list_blender",
    is_flag=True,
    help="List installed blender.",
)
@click.option("-k", "--list-kernel", is_flag=True, help="List kernels.")
@click.option(
    "-a",
    "--all",
    "list_all",
    is_flag=True,
    help="List all blenders installed. (with --list-blender)",
)
@click.option("--remove-kernel", is_flag=True, help="Remove current kernel.")
@click.option(
    "--clean", is_flag=True, help="Remove all kernels created by this command."
)
@click.option(
    "-s",
    "--search-path",
    default=config.get("blender", "search_path"),
    help="Blender search path.",
)
@click.option(
    "--arch",
    "--architectures",
    "architectures",
    multiple=True,
    default=[Architecture(platform.machine()).name.lower()],
    help="Target architectures.",
)
@click.option(
    "--ostypes",
    multiple=True,
    default=[OSType(platform.system()).name.lower()],
    help="Target operating system names.",
)
@click.option(
    "--ext",
    "--extension",
    "ext_re",
    default=None,
    help="Archive extension for download and install.",
)
@click.option(
    "--bl",
    "--run-blender",
    "run_blender",
    is_flag=True,
    help="Run blender.",
)
@click.option(
    "-j",
    "--jupyter",
    "run_jupyter",
    is_flag=True,
    help="Run jupyter lab or notebook.",
)
@click.option("--no-update-kernel", is_flag=True, help="No update kernel.")
@click.option("--only-update-kernel", is_flag=True, help="Only update kernel.")
@click.option(
    "--lab", "--force-lab", "force_lab", is_flag=True, help="Run jupyter lab."
)
@click.option(
    "--notebook",
    "--force-notebook",
    "force_notebook",
    is_flag=True,
    help="Run jupyter notebook.",
)
@click.option(
    "-m",
    "--mirror",
    default=config.get("blender", "mirror"),
    help="Blender mirror site.",
)
@click.option("--ip", "--listen", "listen_address", help="Listen address.")
@click.option("-P", "--password", help="Password.")
@click.option("-N", "--no-password", is_flag=True, help="No password.")
@click.option("--no-browser", is_flag=True, help="No browser.")
@click.option(
    "-w",
    "--wsl",
    "--ein",
    is_flag=True,
    help="Remote mode. (--ip <WSL_IP> --no-password --no-browser)",
)
@click.option("-n", "--dry-run", is_flag=True, help="Dry run.")
@click.option("-v", "--verbose", is_flag=True, help="Show verbose message.")
@click.argument("args", nargs=-1)
def main(
    blender_version,
    show_directory,
    show_python_executable,
    set_blender_version,
    remote,
    strict,
    install,
    list_blender,
    list_kernel,
    list_all,
    remove_kernel,
    clean,
    search_path,
    architectures,
    ostypes,
    ext_re,
    run_blender,
    run_jupyter,
    no_update_kernel,
    only_update_kernel,
    force_lab,
    force_notebook,
    mirror,
    listen_address,
    password,
    no_password,
    no_browser,
    wsl,
    dry_run,
    verbose,
    args,
):
    def normalize_enum_list(values, cls, option):
        values = sum([x.split(",") for x in values], [])
        try:
            values = tuple(map(cls, values))
        except ValueError as exc:
            print_error(f"Bad option value for {option}: {exc}")
            sys.exit(1)
        return values

    args = list(args)

    # Normalize option value
    architectures = normalize_enum_list(
        architectures, Architecture, "--architectures"
    )
    ostypes = normalize_enum_list(ostypes, OSType, "--ostype")
    ext_re = "|".join([x.ext_re for x in ostypes])

    # Special option for Use Ein on WSL
    if wsl:
        if not is_win32():
            print_error(
                "Can not use -w/--wsl/--ein option" " on your platform"
            )
            sys.exit(1)

        if listen_address is None:
            listen_address = get_ip_address_win("vEthernet (WSL)")
            if listen_address is None:
                print_error(
                    "Can not find network interface" ' named "vEthernet (WSL)"'
                )
            # listen_address is private address
            no_password = True

        if not (run_jupyter or force_notebook or force_lab):
            run_jupyter = True

        no_browser = True

    if force_lab or force_notebook:
        run_jupyter = True

    if install:
        remote = True

    if no_update_kernel and only_update_kernel:
        print_error(
            "Can not use --no-update-kernel"
            " and --only-update-kernel same time."
        )
        sys.exit(1)

    if run_blender and run_jupyter:
        print_error("Can not use option --run-bleder with notebook options.")
        sys.exit(1)

    if not run_blender and not run_jupyter:
        for x in args:
            if re.search(r"\.ipynb$", x):
                run_jupyter = True
                break

    run_blender = run_blender or not run_jupyter
    update_kernel = not run_blender and (
        not no_update_kernel or only_update_kernel
    )

    if run_blender and run_jupyter:
        print_error("Can not use option --run-bleder with notebook options.")
        sys.exit(1)

    if blender_version is None:
        blender_version = config.get("blender", "version")
        if blender_version == "":
            blender_version = None

    # Jupyter notebook manager
    notebook = NotebookManager(verbose=verbose, dry_run=dry_run)

    # Blender repository
    repository = Repository(
        search_path=search_path,
        url=mirror,
        apps_root=config.get("blender", "apps_root"),
        cache_dir=config.get("main", "cache_dir"),
        ext_re=ext_re,
        strict=strict,
    )

    # --list-kernel
    if list_kernel:
        for entry in notebook.kernel_directories():
            print(f"{entry}")
        sys.exit(0)

    # --clean:
    if clean:
        notebook.remove_kernel_all()
        sys.exit(0)

    if verbose:
        print_error("Blender search path is {}".format(search_path))

    # --list-blender
    if list_blender:
        v = get_parameter_non_default("blender_version")
        if list_all:
            v = None

        if remote:
            criteria = Criteria(v, architectures, ostypes, ext_re)
            v1 = Version(v) if v is not None else None
            for folder in reversed(repository.remote.versions):
                v2 = Version(folder.folder_version)

                if v1 is not None and (v1 not in v2 and v2 not in v1):
                    continue

                if len(v2.elements) < 3:
                    try:
                        found = False
                        for bl in folder.find_all(
                            v, architectures, ostypes, ext_re
                        ):
                            print(f"{str(bl.version):<24s} {bl.href}")
                        if not found and verbose:
                            print_error(
                                f"ERROR: {folder.version_url}:"
                                f" No blender instlation file found"
                                f" ({criteria})"
                            )
                    except FileNotFoundError as exc:
                        if verbose:
                            print_error(f"ERROR: {folder.version_url}: {exc}")
                else:
                    print(f"{str(folder.version):<24s} {folder.version_url}")
        else:
            if v is None:
                criteria = Criteria()
                versions = repository.local.versions
            else:
                criteria = Criteria(v, architectures, ostypes)
                versions = repository.local.find_all(v, architectures, ostypes)

            if criteria.is_empty():
                print_error("List blenders:")
            else:
                print_error(f"List blenders ({criteria}):")

            if len(versions) == 0:
                if list_all:
                    print_error("Can not detect any installed blenders")
                else:
                    print_error("Not mached")
            else:
                for blender in versions:
                    if verbose:
                        print(
                            f"{str(blender.version):<24s}"
                            f" {blender.ostype.name.lower():<8s}"
                            f" {blender.arch.name.lower():<8s}"
                            f" {blender.directory!s}"
                        )
                    else:
                        print(
                            f"{str(blender.version):<24s}"
                            f" {blender.directory!s}"
                        )

        sys.exit(0)

    try:
        blender = get_blender_install(
            blender_version,
            architectures,
            ostypes=ostypes,
            repository=repository,
            remote=remote,
            dry_run=dry_run,
            verbose=verbose,
        )
    except BlenderNotFound as exc:
        print_error(exc)
        sys.exit(1)
    else:
        if dry_run and blender is None:
            sys.exit(1)

    if blender:
        blender.check()

    if show_directory:
        print(blender.directory)
        sys.exit(0)

    if show_python_executable:
        print(blender.python_executable)
        sys.exit(0)

    if install:
        if blender is not None:
            if blender.is_ok():
                print_error(f"Blender {blender.version} is already installed.")
            else:
                print_error(f"Failed to install blender {blender.version}.")
        sys.exit(0)

    if verbose:
        print_error(f"Blender found: {blender.executable}")

    if verbose and (update_kernel or remove_kernel or run_jupyter):
        print_error(
            "Target kernel path is" f" {notebook.kernel_root / blender.name}"
        )

    if set_blender_version is not None:
        # save default blender version into ~/.config/bl-notebook/config.ini
        c = Config(no_defaults=True)
        c.set("blender", "version", set_blender_version)
        c.save()
        from .shortcut import register_startmenu

        name = "blender/Blender " + str(blender.version)
        register_startmenu(blender.executable, name=name, verbose=verbose)
        register_startmenu(
            blender.executable, name="blender/Blender", verbose=verbose
        )
        sys.exit(0)

    # --remove-kernel
    if remove_kernel or only_update_kernel:
        notebook.remove_kernel(blender.name, ignore_missing=not remove_kernel)
        if not only_update_kernel:
            sys.exit(0)

    # Install blender kernel
    if update_kernel:
        try:
            notebook.install_kernel(
                blender,
                interactive=False,
            )

        except OSError as exc:
            print_error(exc)
            sys.exit(1)

    if only_update_kernel:
        sys.exit(0)

    # Run blender
    if not run_jupyter:
        cmd = [str(blender.executable)] + args
        run_command(cmd, verbose=verbose, dry_run=dry_run, fail_on_exit=True)
        sys.exit(0)

    # Target frontends
    if not force_lab and not force_notebook:
        frontends = ["lab", "notebook"]
    elif force_lab:
        frontends = ["lab"]
    else:
        frontends = ["notebook"]

    # Run notebook
    try:
        notebook.execute_notebook(
            args,
            frontends,
            listen_address,
            password=password,
            no_password=no_password,
            no_browser=no_browser,
            default_kernel=blender.name,
        )
    except ImportError as exc:
        print_error(exc)
        sys.exit(1)
    except OSError as exc:
        print_error(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
