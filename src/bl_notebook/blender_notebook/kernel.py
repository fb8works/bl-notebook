"""
Blender kernel.

Copy and modified from https://github.com/cheng-chi/blender_notebook.
"""

import asyncio
import json
import pathlib
import sys

import bpy
from bpy.app.handlers import persistent

_stdout = sys.stdout
_stderr = sys.stderr


def dprint(*args, **kwargs):
    print(*args, file=_stderr, **kwargs)


def get_runtime_config():
    this_file_path = pathlib.Path(__file__)
    json_path = this_file_path.parent.joinpath("runtime_config.json")
    config_dict = None
    with json_path.open("r") as f:
        config_dict = json.load(f)

    # check config
    assert "args" in config_dict
    for path in config_dict["python_path"]:
        assert pathlib.Path(path).exists()
    return config_dict


class JupyterKernelLoop(bpy.types.Operator):
    bl_idname = "asyncio.jupyter_kernel_loop"
    bl_label = "Jupyter Kernel Loop"

    _timer = None

    kernelApp = None

    def modal(self, context, event):
        if event.type == "TIMER":
            # Run event loop shortly
            loop = asyncio.get_event_loop()
            loop.call_soon(loop.stop)
            loop.run_forever()

        return {"PASS_THROUGH"}

    def execute(self, context):
        # Register timer
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.016, window=context.window)
        wm.modal_handler_add(self)

        if not JupyterKernelLoop.kernelApp:
            runtime_config = get_runtime_config()
            JupyterKernelLoop.kernelApp = BlenderIPKernelApp.instance()
            JupyterKernelLoop.kernelApp.initialize(
                ["python"] + runtime_config["args"]
            )
            # doesn't start event loop, kernelApp.start() does
            JupyterKernelLoop.kernelApp.kernel.start()

        return {"RUNNING_MODAL"}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


try:
    from ipykernel.kernelapp import IPKernelApp
except ModuleNotFoundError:
    text = f"""
Please install ipykernel:

  $ {sys.executable} -m pip install ipykernel
    """
    print(text, file=sys.stderr)
else:

    @persistent
    def quit_blender():
        bpy.ops.wm.quit_blender()

    class BlenderIPKernelApp(IPKernelApp):
        def init_kernel(self):
            super().init_kernel()

            def do_shutdown(restart):
                super(self.kernel.__class__, self.kernel).do_shutdown(restart)
                bpy.app.timers.register(quit_blender)

            # dirty hack for quit blender on restart or shutdown kernel
            setattr(self.kernel, "do_shutdown", do_shutdown)  # noqa: B010

    bpy.utils.register_class(JupyterKernelLoop)

    @persistent
    def loadHandler():
        bpy.ops.asyncio.jupyter_kernel_loop()

    bpy.app.timers.register(loadHandler, first_interval=0.0, persistent=True)

    # Need the timer hack because if immediately call registered operation, get
    # self.user_global_ns is None error in IPython/core/interactiveshell.py
    # The bpy.app.timers causes a segfault when used with jupyter_kernel_loop()
