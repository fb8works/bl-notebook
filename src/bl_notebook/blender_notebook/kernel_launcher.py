#!/usr/bin/env python3
"""
Blender kernel launcher.

Copy and modified from https://github.com/cheng-chi/blender_notebook.
"""

import json
import os
import pathlib
import shlex
import shutil
import subprocess
import sys
import tempfile

DEFAULT_BL_KERNEL_ARGS = ""


def get_blender_config():
    this_file_path = pathlib.Path(__file__)
    json_path = this_file_path.parent.joinpath("blender_config.json")
    config_dict = None
    with json_path.open("r") as f:
        config_dict = json.load(f)

    assert pathlib.Path(config_dict["blender_executable"]).exists()
    for path in config_dict["python_path"]:
        assert pathlib.Path(path).exists()
    return config_dict


def get_kernel_args():
    return shlex.split(
        os.environ.get("BL_KERNEL_ARGS", DEFAULT_BL_KERNEL_ARGS)
    )


def main():
    blender_config = get_blender_config()
    blender_config["args"] = sys.argv[1:]

    kernel_path = pathlib.Path(__file__).parent.joinpath("kernel.py")
    assert kernel_path.exists()

    with tempfile.TemporaryDirectory() as tempdirname:
        tempdir = pathlib.Path(tempdirname)
        runtime_config_path = tempdir.joinpath("runtime_config.json")
        with runtime_config_path.open("w") as f:
            json.dump(blender_config, f)

        runtime_kernel_path = tempdir.joinpath("kernel.py")
        shutil.copyfile(kernel_path, runtime_kernel_path)

        blender_executable = blender_config["blender_executable"]

        args = [blender_executable]
        args += get_kernel_args()
        args += ["-P", str(runtime_kernel_path)]

        subprocess.run(args)


main()
