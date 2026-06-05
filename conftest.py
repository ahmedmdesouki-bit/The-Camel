import sys
import pathlib

# Ensure the repo root is on sys.path so packages (guardrail, sharia, data, db)
# are importable regardless of how pytest is invoked.
ROOT = pathlib.Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
