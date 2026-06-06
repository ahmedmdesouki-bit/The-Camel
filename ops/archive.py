"""
Off-box backup archive (S6) — zip all seven DBs into one file for off-machine transfer.

The local verified copy is ops/backup.py. This produces a single .zip suitable for an
encrypted off-box push. NOTE: encryption happens at the transfer layer (e.g. rclone crypt /
restic / an encrypted volume) per the machine-hardening checklist — never ship the raw zip
off-box unencrypted.
"""
from __future__ import annotations
import os
import zipfile

from db.paths import CamelDbs
from ops.backup import _db_items


def archive_backup(dbs: CamelDbs, dest_zip: str) -> str:
    """Zip every existing DB file into dest_zip. Returns the archive path."""
    parent = os.path.dirname(dest_zip)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for _name, path in _db_items(dbs):
            if os.path.exists(path):
                z.write(path, os.path.basename(path))
    return dest_zip


def verify_archive(dbs: CamelDbs, dest_zip: str) -> bool:
    """True iff every existing source DB is present (and non-empty) inside the archive."""
    if not os.path.exists(dest_zip) or not zipfile.is_zipfile(dest_zip):
        return False
    with zipfile.ZipFile(dest_zip) as z:
        names = {i.filename: i.file_size for i in z.infolist()}
    for _name, path in _db_items(dbs):
        if os.path.exists(path):
            base = os.path.basename(path)
            if base not in names or names[base] == 0 and os.path.getsize(path) > 0:
                return False
    return True
