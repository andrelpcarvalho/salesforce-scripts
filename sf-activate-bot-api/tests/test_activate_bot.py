import pytest

import activate_bot
from activate_bot import (
    BotActivationError,
    _find_bot_id,
    _find_latest_bot_version,
    _activate_bot_version,
    main,
)

INSTANCE_URL = "https://fake.my.salesforce.com"
TOKEN_URL = f"{INSTANCE_URL}/services/oauth2/token"


def _mock_auth(requests_mock):
    requests_mock.post(
        TOKEN_URL,
        json={"access_token": "fake-token-123", "instance_url": INSTANCE_URL},
        status_code=200,
    )


# ── _find_bot_id ─────────────────────────────────────────────────


def test_find_bot_id_success(requests_mock):
    requests_mock.get(
        f"{INSTANCE_URL}/services/data/v61.0/query",
        json={"records": [{"Id": "0Xx000000000001"}]},
    )

    bot_id = _find_bot_id(INSTANCE_URL, "token", "v61.0", "Meu_Bot")

    assert bot_id == "0Xx000000000001"
    query_enviada = requests_mock.last_request.qs["q"][0]
    assert "botdefinition" in query_enviada
    assert "meu_bot" in query_enviada


def test_find_bot_id_not_found_raises(requests_mock):
    requests_mock.get(
        f"{INSTANCE_URL}/services/data/v61.0/query",
        json={"records": []},
    )

    with pytest.raises(BotActivationError, match="Nenhum Bot encontrado"):
        _find_bot_id(INSTANCE_URL, "token", "v61.0", "Bot_Inexistente")


# ── _find_latest_bot_version ─────────────────────────────────────


def test_find_latest_bot_version_success(requests_mock):
    requests_mock.get(
        f"{INSTANCE_URL}/services/data/v61.0/query",
        json={
            "records": [
                {"Id": "0Bv000000000001", "VersionNumber": 3, "Status": "Draft"}
            ]
        },
    )

    version = _find_latest_bot_version(INSTANCE_URL, "token", "v61.0", "0Xx000000000001")

    assert version["Id"] == "0Bv000000000001"
    assert version["Status"] == "Draft"


def test_find_latest_bot_version_not_found_raises(requests_mock):
    requests_mock.get(
        f"{INSTANCE_URL}/services/data/v61.0/query",
        json={"records": []},
    )

    with pytest.raises(BotActivationError, match="Nenhuma BotVersion encontrada"):
        _find_latest_bot_version(INSTANCE_URL, "token", "v61.0", "0Xx000000000001")


# ── _activate_bot_version ────────────────────────────────────────


def test_activate_bot_version_success(requests_mock):
    requests_mock.patch(
        f"{INSTANCE_URL}/services/data/v61.0/sobjects/BotVersion/0Bv000000000001",
        status_code=204,
    )

    _activate_bot_version(INSTANCE_URL, "token", "v61.0", "0Bv000000000001")

    assert requests_mock.last_request.json() == {"Status": "Active"}


def test_activate_bot_version_failure_raises(requests_mock):
    requests_mock.patch(
        f"{INSTANCE_URL}/services/data/v61.0/sobjects/BotVersion/0Bv000000000001",
        status_code=400,
        json={"message": "INVALID_FIELD"},
    )

    with pytest.raises(BotActivationError, match="Falha ao ativar"):
        _activate_bot_version(INSTANCE_URL, "token", "v61.0", "0Bv000000000001")


# ── main() fim a fim ─────────────────────────────────────────────


def test_main_activates_draft_bot(monkeypatch, requests_mock, capsys):
    monkeypatch.setenv("SF_BOT_API_NAME", "Meu_Bot")
    _mock_auth(requests_mock)
    requests_mock.get(
        f"{INSTANCE_URL}/services/data/v61.0/query",
        [
            {"json": {"records": [{"Id": "0Xx000000000001"}]}},
            {
                "json": {
                    "records": [
                        {"Id": "0Bv000000000001", "VersionNumber": 3, "Status": "Draft"}
                    ]
                }
            },
        ],
    )
    requests_mock.patch(
        f"{INSTANCE_URL}/services/data/v61.0/sobjects/BotVersion/0Bv000000000001",
        status_code=204,
    )

    main()

    saida = capsys.readouterr().out
    assert "Bot ativado com sucesso." in saida


def test_main_skips_when_already_active(monkeypatch, requests_mock, capsys):
    monkeypatch.setenv("SF_BOT_API_NAME", "Meu_Bot")
    _mock_auth(requests_mock)
    requests_mock.get(
        f"{INSTANCE_URL}/services/data/v61.0/query",
        [
            {"json": {"records": [{"Id": "0Xx000000000001"}]}},
            {
                "json": {
                    "records": [
                        {"Id": "0Bv000000000001", "VersionNumber": 3, "Status": "Active"}
                    ]
                }
            },
        ],
    )
    patch_mock = requests_mock.patch(
        f"{INSTANCE_URL}/services/data/v61.0/sobjects/BotVersion/0Bv000000000001",
        status_code=204,
    )

    main()

    saida = capsys.readouterr().out
    assert "Bot ja esta ativo" in saida
    assert not patch_mock.called


def test_main_uses_custom_api_version(monkeypatch, requests_mock):
    monkeypatch.setenv("SF_BOT_API_NAME", "Meu_Bot")
    monkeypatch.setenv("SF_API_VERSION", "v60.0")
    _mock_auth(requests_mock)
    requests_mock.get(
        f"{INSTANCE_URL}/services/data/v60.0/query",
        [
            {"json": {"records": [{"Id": "0Xx000000000001"}]}},
            {
                "json": {
                    "records": [
                        {"Id": "0Bv000000000001", "VersionNumber": 1, "Status": "Draft"}
                    ]
                }
            },
        ],
    )
    requests_mock.patch(
        f"{INSTANCE_URL}/services/data/v60.0/sobjects/BotVersion/0Bv000000000001",
        status_code=204,
    )

    main()  # nao deve lancar; se cair na v61.0 (default), requests_mock acusaria NoMockAddress


def test_main_without_bot_api_name_and_no_arg_exits(monkeypatch, capsys):
    monkeypatch.delenv("SF_BOT_API_NAME", raising=False)
    monkeypatch.setattr(activate_bot.sys, "argv", ["activate_bot.py"])

    with pytest.raises(SystemExit):
        main()
