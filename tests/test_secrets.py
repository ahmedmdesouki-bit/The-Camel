"""
S4 — secrets-leak tests. Cheap, high-value: fail loudly if a secret ever escapes.
"""
import pathlib
import re
import subprocess

# NB: do NOT .resolve() — that expands the N: virtual drive back to the real 261-char path
# and read_text() then hits Windows MAX_PATH. Keep paths on the short drive.
ROOT = pathlib.Path(__file__).parent.parent
KEY_PATTERN = re.compile(r"(sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{12,}|secret_[A-Za-z0-9]{16,})")


def test_env_is_gitignored():
    lines = [ln.strip() for ln in (ROOT / ".gitignore").read_text().splitlines()]
    assert ".env" in lines

def test_env_not_tracked_by_git():
    out = subprocess.run(["git", "ls-files"], cwd=str(ROOT),
                         capture_output=True, text=True).stdout.splitlines()
    assert ".env" not in out

def test_no_hardcoded_secrets_in_source():
    offenders = []
    for p in ROOT.rglob("*.py"):
        if ".git" in p.parts or "source-materials" in p.parts:
            continue
        if KEY_PATTERN.search(p.read_text(errors="ignore")):
            offenders.append(str(p.relative_to(ROOT)))
    assert offenders == [], f"possible hardcoded secret(s) in: {offenders}"

def test_env_example_has_only_placeholders():
    ex = (ROOT / ".env.example").read_text()
    assert "your_paper_key" in ex                 # placeholder present
    assert not KEY_PATTERN.search(ex)             # no real-looking key
