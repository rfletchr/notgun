# Agent Notes

## Rez Build Conventions

This project uses [rez](https://github.com/AcademySoftwareFoundation/rez) for production package management with cmake as the build system.

### package.py

- `build_command` defaults to `"cmake"` — do not set it explicitly
- `build_requires = ["python"]` is required whenever `rez_install_python` is used in CMakeLists.txt
- Use `env.PATH.prepend("{root}/bin")` in `commands()` to expose executables — do not use `alias()`

### CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 2.8)
include(RezBuild)

# Install Python package
file(GLOB_RECURSE py_files "src/<package>/*.py")
rez_install_python(
    py
    FILES ${py_files}
    DESTINATION python
    LOCAL_SYMLINK
)

# Install executables from bin/ (packages with entry points only)
file(GLOB bin_files "bin/*")
rez_install_files(
    ${bin_files}
    DESTINATION .
    EXECUTABLE
    LOCAL_SYMLINK
)
```

### LOCAL_SYMLINK

All install commands use `LOCAL_SYMLINK`, which symlinks installed files back to the source
tree during a local build (`rez-build`). This gives editable-install behaviour without pip.

For `bin/` scripts, `LOCAL_SYMLINK` creates a symlink to the source file — the symlink
inherits no permissions of its own, so the **source file itself must have its execute bit
set** (`chmod +x bin/<script>`). The `EXECUTABLE` flag alone is not sufficient when
`LOCAL_SYMLINK` is active.

### Entry Points

- Shell/Python scripts live in `bin/` and must have `chmod +x` applied to the source file
- Installed via `rez_install_files` with both `EXECUTABLE` and `LOCAL_SYMLINK`
- `commands()` in package.py adds `{root}/bin` to `PATH`
- Do not use `alias()` for entry points

Tool packages that expose a CLI use the standard `__main__.py` pattern. The `bin/`
script is a minimal bash shim that delegates to `python3 -m <package>`:

```bash
#!/usr/bin/env bash
exec python3 -m notgun_launcher "$@"
```

The package's `__main__.py` defines a `main()` function and calls `sys.exit(main())`:

```python
import sys

def main() -> int:
    ...

if __name__ == "__main__":
    sys.exit(main())
```

This keeps the entry point logic in Python (testable, importable) while the `bin/`
script stays a trivial one-liner.

`exec` is used deliberately so that bash replaces itself with the Python process rather
than forking a child. Benefits:
- **Signal handling** — signals (SIGTERM, SIGINT, etc.) arrive directly at Python. Without
  `exec`, bash is the parent and does not forward SIGTERM to its child by default, which
  breaks process managers, `kill`, systemd, and Docker.
- **PID stability** — the PID of the launched process remains the Python process for its
  entire lifetime, so supervisors and tools like `pgrep` see a consistent process.

This is the same reason Docker entrypoints conventionally end with `exec "$@"`.

<!-- TODO: move exec rationale to user-facing documentation once the project is more mature -->

### Package Structure

```
packages/<name>/
├── package.py
├── CMakeLists.txt
├── bin/          # executable scripts
└── src/<name>/   # Python source
```

### PyPI Dependencies

PyPI packages are not installed via pip during the rez build. They are wrapped as
separate rez packages and declared as `requires` entries.

## Development Without a Full Rez Environment

During development it is possible to avoid resolving a full rez environment by adding
rez package `src/` directories directly to a `.pth` file inside your venv. This makes
the packages importable without `rez env`:

```
# e.g. <venv>/lib/pythonX.Y/site-packages/notgun-dev.pth
/home/rob/Development/notgun/packages/notgun/src
/home/rob/Development/notgun/packages/notgun-launcher/src
```

Python automatically processes `.pth` files at startup, so any package under those
`src/` directories becomes importable immediately. This is equivalent to a `pip install
-e` editable install but works entirely within an existing venv without touching rez.

this is handy for development, but when running code its better to use rez env to properly bootstrap the environment.