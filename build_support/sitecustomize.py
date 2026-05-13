from __future__ import annotations

import ctypes
from pathlib import Path
import sys


def _prepare_tcl_runtime() -> None:
    if sys.platform != "win32":
        return

    for root in {sys.base_prefix, sys.prefix}:
        if not root:
            continue
        dll_path = Path(root) / "DLLs" / "tcl86t.dll"
        if not dll_path.exists():
            continue
        try:
            tcl = ctypes.CDLL(str(dll_path))
            tcl.Tcl_FindExecutable(ctypes.c_wchar_p(sys.executable))
            return
        except Exception:
            continue


_prepare_tcl_runtime()
