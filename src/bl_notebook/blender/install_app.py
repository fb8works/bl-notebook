from bl_notebook.util import print_error

from .app import BlenderApp
from .ostype import OSType


class BlenderNotFound(Exception):
    pass


def get_blender_install(
    version,
    architectures,
    ostypes,
    repository,
    remote=False,
    dry_run=False,
    verbose=False,
) -> BlenderApp:
    blender = None

    ostypes = tuple(map(OSType, ostypes))

    if repository.local.versions:
        blender = repository.local.find(version, architectures, ostypes)
        if blender is not None and not blender.is_ok():
            print_error(
                "warning: Blender directory found,"
                " but executable not found: " + str(blender.executable)
            )

    if blender is not None and blender.is_ok():
        if verbose:
            print_error(f"Installed blender found: {blender.directory}")
        return blender

    if not remote:
        arg = version + " " if version else ""
        raise BlenderNotFound(
            "Can not find blender installed: "
            + arg
            + "(use --remote to download and install)"
        )

    folder = repository.remote.find_version(version)
    if folder is None:
        raise BlenderNotFound(
            f"No blender matching version {version}"
            f" found at {repository.remote.url_base}"
        )

    try:
        remote_file = folder.find(
            architectures, ostypes, repository.remote.ext_re
        )
    except FileNotFoundError:
        archnames = f"{'|'.join([x.value for x in architectures])}"
        ostype_names = f"{'|'.join([x.value for x in ostypes])}"
        ext_re = repository.remote.ext_re
        raise BlenderNotFound(
            "Can not find blender"
            f" (ostype={ostype_names}, arch={archnames}, ext={ext_re})"
            f" in remote {folder.version_url}"
        )

    if dry_run:
        print_error(f"(DRY-RUN) download and install: {remote_file.href}")
    else:
        remote_file.download()
        remote_file.install(force=False, verbose=verbose, dry_run=dry_run)
        blender = BlenderApp(
            path=remote_file.blender_executable,
            version=remote_file.version,
            arch=remote_file.arch,
            ostype=remote_file.ostype,
        )
        try:
            blender.check()
        except Exception as exc:
            raise BlenderNotFound(f"Installation failed: {exc}")

    return blender
