import sys
import pathlib

ROOT = pathlib.Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from db.paths import NoahDbs, init_all


@pytest.fixture
def dbs(tmp_path):
    """Initialise all seven Noah databases under a fresh temp directory."""
    _dbs = NoahDbs.from_dir(str(tmp_path))
    init_all(_dbs)
    return _dbs
