"""Windows .cmd wrapper template generator.

On Windows, some hosts (Cursor, possibly others) execute hook commands
through cmd.exe, which brings issues with nested quotes, stdin relay,
and Python path resolution. This module generates parameterized .cmd
wrappers to handle these concerns uniformly.
"""

from __future__ import annotations

import sys
from pathlib import Path


# Template for a Windows .cmd wrapper that:
# 1. Captures stdin to a temp file (some hosts pipe stdin, cmd.exe doesn't handle it well)
# 2. Calls python with the context_lantern module
# 3. Cleans up the temp file
WINDOWS_CMD_TEMPLATE = """\
@echo off
setlocal
set "TMPFILE=%TEMP%\\cl_payload_%RANDOM%.json"
more > "%TMPFILE%"
"{python_path}" -m context_lantern run --adapter {adapter} --stdin-file "%TMPFILE%" {extra_args}
del "%TMPFILE%" 2>nul
endlocal
"""


def generate_cmd_wrapper(
    adapter: str,
    python_path: str | None = None,
    extra_args: str = "",
) -> str:
    """Generate a .cmd wrapper script for a given adapter.

    Args:
        adapter: Adapter name (codex, cursor, ...).
        python_path: Absolute path to Python executable.
            If None, uses sys.executable.
        extra_args: Additional CLI arguments to pass through.

    Returns:
        The .cmd script content as a string.
    """
    if python_path is None:
        python_path = sys.executable

    return WINDOWS_CMD_TEMPLATE.format(
        python_path=python_path.replace("\\", "\\\\"),
        adapter=adapter,
        extra_args=extra_args,
    )


def is_windows() -> bool:
    """Check if the current platform is Windows."""
    return sys.platform == "win32"


def resolve_python_path() -> str:
    """Resolve the best Python path for the current environment."""
    return sys.executable
