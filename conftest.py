import sys
import pathlib

ROOT = pathlib.Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from db.paths import CamelDbs, init_all
from ops.kill_switch import resume


@pytest.fixture(autouse=True)
def _kill_switch_off():
    """Constitution.evaluate() checks is_halted() (S4), so ensure the kill switch is OFF
    for every test unless a test explicitly halt()s it. Prevents cross-test pollution."""
    resume()
    yield
    resume()


@pytest.fixture
def dbs(tmp_path):
    """Initialise all seven Camel databases under a fresh temp directory."""
    _dbs = CamelDbs.from_dir(str(tmp_path))
    init_all(_dbs)
    return _dbs
