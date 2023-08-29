# Blender launcher

Blender launcher for windows with jupyter notebook support.

Inspired by [blender-notebook](https://github.com/cheng-chi/blender_notebook).

![screenshot](https://github.com/fb8works/bl-notebook/blob/main/screenshot.png?raw=true)

# Install

```
pip install git+https://github.com/fb8works/bl-notebook.git
```

# Options

```powershell
PS> bl --help
Usage: bl [OPTIONS] [ARGS]...

Options:
  -b, --blender-version TEXT      Specify blender version.
  -B, --set-blender-version TEXT  Set the default blender version.
  -d, --show-directory            Show the installed blender directory.
  -p, --show-python-executable    Show the installed blender's python
                                  executable path.
  --strict                        Strictly check the architecture.
  -r, --remote                    Remote mode (with -l).
  -I, --install                   Only install blender.
  -l, --list, --list-blender      List installed blender.
  -k, --list-kernel               List kernels.
  -a, --all                       List all blenders installed. (with --list-
                                  blender)
  --remove-kernel                 Remove current kernel.
  --clean                         Remove all kernels created by this command.
  -s, --search-path TEXT          Blender search path.  [default:
                                  C:\app\blender;C:\Program Files\Blender
                                  Foundation]
  --arch, --architectures TEXT    Target architectures.  [default: x86_64,
                                  x86, any]
  --ostypes TEXT                  Target operating system names.  [default:
                                  Windows]
  --ext, --extension TEXT         Archive extension for download and install.
  --bl, --run-blender             Run blender.
  -j, --nb, --notebook, --run-notebook
                                  Run jupyter lab or notebook.
  --no-update-kernel              No update kernel.
  --only-update-kernel            Only update kernel.
  --lab, --use-lab                Run jupyter lab.
  --notebook, --use-notebook      Run jupyter notebook.
  -m, --mirror TEXT               Blender mirror site.  [default: https://mirr
                                  ors.ocf.berkeley.edu/blender/release/]
  --ip, --listen TEXT             Listen address.
  -P, --password TEXT             Password.
  -N, --no-password               No password.
  --no-browser                    No browser.
  -w, --wsl, --ein                Remote mode. (--ip <WSL_IP> --no-password
                                  --no-browser)
  -n, --dry-run                   Dry run.
  -v, --verbose                   Show verbose message.
  -h, --help                      Show this message and exit.
```

# List installed blenders

```powershell
PS C:\> bl --list
3.2.2-windows-x64        C:\app\blender\blender-3.2.2-windows-x64
3.2                      C:\Program Files\Blender Foundation\Blender 3.2
3.3                      C:\Program Files\Blender Foundation\Blender 3.3
```

# Run blender

Run latest version installed.

```powershell
bl
```

Or specify the version.

```powershell
bl -b 3.2
```

Use '-r' option to install blender if not installed.

```powershell
$ bl -b 3.5 -r
Downloading https://mirrors.ocf.berkeley.edu/blender/release/Blender3.5/blender-3.5.1-windows-x64.zip...
100%|███████████████████████████████████████████████████████████████████████████████| 326M/326M [01:36<00:00, 3.56MB/s]
Extracting c:\app\blender\blender-3.5.1-windows-x64.zip into c:\app\blender\blender-3.5.1-windows-x64
```

If you want to pass the arguments literally for the blender, use double dash.

```
$ bl -- --help
```

# Run jupyter notebook with blender kernel

Use '--nb', '--notebook' or '--lab' to run jupyter notebook/lab.

```powershell
bl --nb
```

Or simply pass the .ipynb filename.

```powershell
bl my-notebook.ipynb
```

You can connect to blender kernel from console.

```powershell
jupyter console --existing
```

# Use Ein (Emacs IPython Notebook)

If you want to use [EIN](https://github.com/millejoh/emacs-ipython-notebook) with WSL, You need to remote connect over the "vEthernet (WSL)" interface. In this case, You can use --ein option (alias for --ip <WSL_IP> --no-password --no-browser). And type M-x ein:notebooklist-login RET in emacs. After you got prompt "URL or port", then enter the URL (e.g., "http://172.23.240.1:8888").

```
bl --ein
```

# Set default blender version

Set the default blender version persistently. save settings into ~/.config/bl-notebook/config.ini.

```
bl -B 3.5
```

Or create .blender_version file. If .blender_version exists in the current or parent directory, it takes precedence over the default version specified by the -B option.

```
echo '3.5' > .blender_version
```

# Environment variable

| variable       | description                                        |
|:---------------|:---------------------------------------------------|
| BL_KERNEL_ARGS | Specifies arguments to be passed to blender kernel |

```
$env:BL_KERNEL_ARGS="--window-geometry 50 50 1280 960"; bl --lab
```

# Configuration

~/.config/bl-notebook/config.ini

```
[main]
cache_dir = ~/.cache/bl-notebook

[blender]
version = 3.5
apps_root = C:\app\blender
search_path = C:\app\blender;C:\Program Files\Blender Foundation
mirror = https://mirrors.ocf.berkeley.edu/blender/release/
```

# Wrapper commad for WSL

If you are using WSL, you will probably want to run native blender. If so, copy examples/bl to an executable location on WSL (e.g. ~/.local/bin).
