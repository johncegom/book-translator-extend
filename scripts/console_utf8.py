"""Make a command line print UTF-8 even when the console uses a legacy code page (BUG-021).

On Windows, Python's stdout and stderr use the system code page (cp1252 on many machines), also when
piped or redirected. Book text has letters it cannot encode ("ế", "｜"), so `print` raises
UnicodeEncodeError. `errors="replace"` is not an option: it would corrupt the JSON that
`grade_checks --sample` prints for the judged checks.

Call `use_utf8_output()` first in a `main()`, never at import: importing a module must not change the process.
"""
from __future__ import annotations

import sys


def use_utf8_output() -> None:
    """Switch stdout and stderr to UTF-8 when they are not. A stream that cannot be reconfigured is left alone."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        if (getattr(stream, "encoding", "") or "").lower().replace("-", "") == "utf8":
            continue
        reconfigure(encoding="utf-8")
