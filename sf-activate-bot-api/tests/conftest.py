import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


import pytest


@pytest.fixture(autouse=True)
def clean_sf_env(monkeypatch):
    """Remove qualquer SF_* residual do ambiente antes de cada teste,
    pra um teste nunca herdar env var de outro."""
    for key in list(os.environ):
        if key.startswith("SF_"):
            monkeypatch.delenv(key, raising=False)


@pytest.fixture
def fake_auth():
    return {"access_token": "fake-token-123", "instance_url": "https://fake.my.salesforce.com"}


@pytest.fixture(autouse=True)
def set_base_credentials(monkeypatch):
    """Credenciais minimas validas, pra testes que nao sao sobre auth
    nao precisarem repetir isso toda hora."""
    monkeypatch.setenv("SF_LOGIN_URL", "https://fake.my.salesforce.com")
    monkeypatch.setenv("SF_CLIENT_ID", "client-id")
    monkeypatch.setenv("SF_CLIENT_SECRET", "client-secret")
