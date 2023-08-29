import json
import os
import re
import subprocess
import sys
from contextlib import suppress
from pathlib import Path
from shutil import rmtree

from jupyter_core.paths import jupyter_data_dir

from .util import make_password, print_command, print_error, run_command


class NotebookManager:
    def __init__(self, data_dir=None, verbose=False, dry_run=False):
        self.data_dir = Path(data_dir or jupyter_data_dir())
        self.kernel_root = self.data_dir / "kernels"
        self.verbose = verbose
        self.dry_run = dry_run

    def kernel_directories(self):
        return self.kernel_root.iterdir()

    def remove_kernel(self, name, ignore_missing=False):
        kernel_path = self.kernel_root / name

        kernel_path = Path(kernel_path)
        if self.verbose or self.dry_run:
            print_error(f"Remove: {kernel_path}", dry_run=self.dry_run)
        if not kernel_path.exists():
            if ignore_missing:
                return
            mess = f"Kernel does not exist: {kernel_path}"
            if self.dry_run:
                print_error(mess)
                return
            raise FileNotFoundError(mess)
        if not self.dry_run:
            try:
                rmtree(kernel_path)
            except OSError as exc:
                print_error(f"Can not delete {kernel_path}: {exc}")

    def remove_kernel_all(self):
        for entry in self.kernel_directories():
            if re.match(r"blender[\d_-]", entry.name, re.I):
                path = entry / "kernel.json"
                with suppress(FileNotFoundError), open(path) as fh:
                    data = json.load(fh)
                    tag = data.get("tag")
                    if "bl_notebook" in tag.split(","):
                        self.remove_kernel(entry)

    def install_kernel(
        self,
        kernel_name,
        python_executable,
        blender_executable,
        interactive=False,
    ):
        kernel_name = re.sub(r"[^a-zA-Z0-9_.-]", "-", kernel_name)
        installer = Path(__file__).parent / "blender_notebook" / "installer.py"
        cmd = [
            sys.executable,
            installer,
            "install",
            "--kernel-name",
            kernel_name,
            "--kernel-dir",
            str(self.kernel_root),
            "--blender-exec",
            str(blender_executable),
            "--tag",
            "bl_notebook",
        ]
        yes = not interactive
        run_command(cmd, verbose=self.verbose, dry_run=self.dry_run, yes=yes)

        # Install bl_notebook for blender's python.

        # The original blender_notebook added sys.path for loading ipykernel.
        # This would cause blender python to import an incompatible version.
        # To avoid this, do not add sys.path and always install ipykernel into
        # site-packages in blender's python.

        # Test if bl_notebook is installed.
        code = run_command(
            [python_executable, "-c", "import ipykernel"],
            verbose=self.verbose,
            dry_run=self.dry_run,
            show_nonzero=False,
            fail_on_exit=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if code is None or code != 0:
            print_error("Installing ipykernel...")
            run_command(
                [
                    python_executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-warn-script-location",
                    "ipykernel",
                ],
                verbose=self.verbose,
                dry_run=self.dry_run,
                fail_on_exit=True,
            )

    def execute_notebook(
        self,
        args,
        frontends,
        ip,
        password,
        no_password,
        no_browser,
        default_kernel=None,
    ):
        def normalize_frontend_name(name):
            if re.search(r"(jupyter[ _-]?)?lab", name, re.I):
                return "lab"
            elif re.search(r"(jupyter[ _-]?)?notebook", name, re.I):
                return "notebook"
            else:
                raise ValueError(f"Unsupported jupyter frontend name {name!r}")

        frontends = [normalize_frontend_name(x) for x in frontends]
        for name in frontends:
            use_lab = name == "lab"
            try:
                self._execute_notebook(
                    args,
                    use_lab,
                    ip,
                    password,
                    no_password,
                    no_browser,
                    default_kernel=default_kernel,
                )
            except ImportError:
                pass
            else:
                return

        names = "/".join(frontends)
        raise ImportError(
            f"Can not run jupyter {names}. please install jupyter {names}."
        )

    def _execute_notebook(
        self,
        args,
        use_lab,
        ip,
        password,
        no_password,
        no_browser,
        default_kernel,
    ):
        if isinstance(args, tuple):
            args = list(args)

        options = []

        if ip is not None:
            options += ["--NotebookApp.ip", ip]
        else:
            # change default listen address to 127.0.0.1 for avoid HSTS
            options += ["--NotebookApp.ip", "127.0.0.1"]

        if use_lab and no_password:
            # password_required=False does not work for Jupyter lab.
            # We must use an encrypted blank password instead empty string.
            password = ""

        if password is not None:
            options += ["--NotebookApp.password", make_password(password)]
        else:
            options += ["--NotebookApp.password", ""]

        if no_password:
            options += ["--NotebookApp.token", ""]
            options += ["--NotebookApp.password_required", "False"]

        if no_browser:
            options += ["--no-browser"]

        os.environ["JUPYTER_DATA_DIR"] = str(self.data_dir)

        if not use_lab:
            try:
                from jupyter_core.command import main as notebook_main
            except ImportError:
                print_error("Jupyter notebook is not installed.")
                sys.exit(1)
            else:
                sys.argv = ["jupyter", "notebook"] + options + args
                if self.verbose or self.dry_run:
                    cmd = [sys.executable, "-m"] + sys.argv
                    print_command(cmd, dry_run=self.dry_run)
                if not self.dry_run:
                    notebook_main()
        else:
            from jupyterlab.labapp import main as labapp_main

            if default_kernel:
                options += [
                    "--MultiKernelManager.default_kernel_name",
                    default_kernel,
                ]

            args = options + args

            if self.verbose or self.dry_run:
                cmd = [sys.executable, "-m", "jupyter", "lab"] + args
                print_command(cmd, dry_run=self.dry_run)
            if not self.dry_run:
                labapp_main(argv=args)
