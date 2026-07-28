import pytest

from auth import get_access_token, AuthError


def test_get_access_token_missing_credentials_raises(monkeypatch):
    monkeypatch.delenv("SF_LOGIN_URL", raising=False)
    monkeypatch.delenv("SF_CLIENT_ID", raising=False)
    monkeypatch.delenv("SF_CLIENT_SECRET", raising=False)

    with pytest.raises(AuthError, match="Faltam variaveis"):
        get_access_token()


def test_get_access_token_success(monkeypatch, requests_mock):
    monkeypatch.setenv("SF_LOGIN_URL", "https://suaorg.my.salesforce.com")
    monkeypatch.setenv("SF_CLIENT_ID", "client-id")
    monkeypatch.setenv("SF_CLIENT_SECRET", "client-secret")

    requests_mock.post(
        "https://suaorg.my.salesforce.com/services/oauth2/token",
        json={"access_token": "abc123", "instance_url": "https://suaorg.my.salesforce.com"},
        status_code=200,
    )

    result = get_access_token()

    assert result == {"access_token": "abc123", "instance_url": "https://suaorg.my.salesforce.com"}


def test_get_access_token_sends_client_credentials_grant(monkeypatch, requests_mock):
    monkeypatch.setenv("SF_LOGIN_URL", "https://suaorg.my.salesforce.com")
    monkeypatch.setenv("SF_CLIENT_ID", "client-id")
    monkeypatch.setenv("SF_CLIENT_SECRET", "client-secret")

    requests_mock.post(
        "https://suaorg.my.salesforce.com/services/oauth2/token",
        json={"access_token": "abc123", "instance_url": "https://suaorg.my.salesforce.com"},
        status_code=200,
    )

    get_access_token()

    sent_body = requests_mock.last_request.text
    assert "grant_type=client_credentials" in sent_body
    assert "client_id=client-id" in sent_body
    assert "client_secret=client-secret" in sent_body


def test_get_access_token_http_error_raises_autherror(monkeypatch, requests_mock):
    monkeypatch.setenv("SF_LOGIN_URL", "https://suaorg.my.salesforce.com")
    monkeypatch.setenv("SF_CLIENT_ID", "client-id")
    monkeypatch.setenv("SF_CLIENT_SECRET", "wrong-secret")

    requests_mock.post(
        "https://suaorg.my.salesforce.com/services/oauth2/token",
        json={"error": "invalid_client"},
        status_code=400,
    )

    with pytest.raises(AuthError, match="400"):
        get_access_token()
