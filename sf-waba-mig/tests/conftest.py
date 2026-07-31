import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


@pytest.fixture(autouse=True)
def clean_config_env(monkeypatch):
    """Remove INPUT_DIR/JSON_PATH/OUTPUT_DIR do ambiente antes de cada teste,
    pra um teste nunca herdar valor de outro (ou de um .env real na máquina)."""
    for key in ("INPUT_DIR", "JSON_PATH", "OUTPUT_DIR"):
        monkeypatch.delenv(key, raising=False)
