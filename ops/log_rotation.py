"""
Log rotation (S6) — bound log-file growth; keep the last N rotations.

Pure file operations. The scheduler calls `rotate_if_needed` after each run; an oversized
log is rolled to .1, .2, ... up to `keep`, oldest dropped.
"""
from __future__ import annotations
import os

DEFAULT_MAX_BYTES = 5 * 1024 * 1024   # 5 MB
DEFAULT_KEEP = 5


def rotate_if_needed(log_path: str, max_bytes: int = DEFAULT_MAX_BYTES,
                     keep: int = DEFAULT_KEEP) -> bool:
    """Rotate `log_path` if it exceeds max_bytes. Returns True if a rotation happened."""
    if not os.path.exists(log_path) or os.path.getsize(log_path) <= max_bytes:
        return False
    # drop the oldest, shift the rest up
    oldest = f"{log_path}.{keep}"
    if os.path.exists(oldest):
        os.remove(oldest)
    for i in range(keep - 1, 0, -1):
        src, dst = f"{log_path}.{i}", f"{log_path}.{i + 1}"
        if os.path.exists(src):
            os.replace(src, dst)
    os.replace(log_path, f"{log_path}.1")
    open(log_path, "w").close()   # fresh empty log
    return True
