"""
Backup / restore (S5.5) — local verified backup of all seven Noah DBs.

S5.5 is the local, verified copy + restore. The off-box encrypted backup is S6. Verification
is a SHA-256 compare so a silent partial copy is caught.
"""
from __future__ import annotations
import hashlib
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from db.paths import NoahDbs


def _db_items(dbs: NoahDbs) -> List[Tuple[str, str]]:
    return [("market", dbs.market), ("macro", dbs.macro),
            ("fundamentals", dbs.fundamentals), ("news", dbs.news),
            ("sharia", dbs.sharia), ("portfolio", dbs.portfolio),
            ("learning", dbs.learning)]


def _sha256(path: str):
    if not os.path.exists(path):
        return None
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def backup(dbs: NoahDbs, dest_dir: str) -> Dict[str, str]:
    """Copy every existing DB file to dest_dir; return {db_name: sha256}."""
    os.makedirs(dest_dir, exist_ok=True)
    result: Dict[str, str] = {}
    for name, path in _db_items(dbs):
        if os.path.exists(path):
            shutil.copy2(path, os.path.join(dest_dir, os.path.basename(path)))
            result[name] = _sha256(path)
    return result


def verify_backup(dbs: NoahDbs, dest_dir: str) -> bool:
    """True iff every existing source DB has a byte-identical copy in dest_dir."""
    for _name, path in _db_items(dbs):
        if os.path.exists(path):
            backed = os.path.join(dest_dir, os.path.basename(path))
            if not os.path.exists(backed) or _sha256(path) != _sha256(backed):
                return False
    return True


def restore(dbs: NoahDbs, dest_dir: str) -> List[str]:
    """Copy backups back over the live DBs. Returns the list of restored db names."""
    restored: List[str] = []
    for name, path in _db_items(dbs):
        backed = os.path.join(dest_dir, os.path.basename(path))
        if os.path.exists(backed):
            shutil.copy2(backed, path)
            restored.append(name)
    return restored
