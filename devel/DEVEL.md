# Setup for development

## Windows

```powershell
poetry install
poetry shell
pre-commit install
```

## Linux

```bash
ln -s env/.??* .
asdf install
direnv allow
poetry install
poetry shell
pre-commit install
```

# Internals

1. Run jupyter notebook.
  1. Run blender kernel in jupyter notebook.
  1. It executes kernel_launcher.py by argv in kernel.json.
    - e.g., "python kernel_launcher.py -f {connection_file}"
1. In kernel_launcher.py.
  1. Copy kernel.py in temporary directory.
  1. And write runtime_config.json in the temporary directory.
    1. The runtime_config.json contains a sys.argv[:1] with the key named args. For example, ["-f", "<CONNECTION_FILE>"].
  1. Run "blender -P kernel.py".
1. In kernel.py
  1. Load runtime_config.json into RUNTIME_CONFIG.
  1. Initialize jupyter kernel with RUNTIME_CONFIG["args"]. e.g., ["python", "-f", "<CONNECTION_FILE>"]
  1. Start kernel.
  1. Register blender operator named JupyterKernelLoop.
  1. JupterKernelLoop.execute makes timer.
  1. JupterKernelLoop.modal handles timer event and run the asyncio event loop short time.
