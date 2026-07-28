"""
activate_bot.py

Ativa um Einstein Bot (chatbot) via REST API, equivalente a:

    curl -X PATCH \\
      "$INSTANCE_URL/services/data/$SF_API_VERSION/sobjects/BotVersion/$BOT_VERSION_ID" \\
      -H "Authorization: Bearer $ACCESS_TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{"Status": "Active"}'

A versao da API (SF_API_VERSION) vem do .env, com fallback para v61.0.

Fluxo:
    1. Autentica (auth.py -> Client Credentials Flow)
    2. Busca o Bot pelo DeveloperName (SF_BOT_API_NAME no .env)
    3. Busca a BotVersion mais recente desse Bot
    4. Faz PATCH em BotVersion.Status = "Active"

── USO ─────────────────────────────────────────────────────────
python config.py          # opcional: grava SF_BOT_API_NAME no .env
python activate_bot.py
"""

import os
import sys
import requests
from dotenv import load_dotenv

from auth import get_access_token, AuthError

load_dotenv()


class BotActivationError(Exception):
    """Erro ao localizar ou ativar o bot."""


def _query(instance_url: str, access_token: str, api_version: str, soql: str) -> list:
    resp = requests.get(
        f"{instance_url}/services/data/{api_version}/query",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"q": soql},
        timeout=30,
    )
    if resp.status_code != 200:
        raise BotActivationError(f"Falha na query ({resp.status_code}): {resp.text}")
    return resp.json().get("records", [])


def _find_bot_id(instance_url: str, access_token: str, api_version: str, bot_api_name: str) -> str:
    records = _query(
        instance_url,
        access_token,
        api_version,
        f"SELECT Id, DeveloperName FROM BotDefinition WHERE DeveloperName = '{bot_api_name}'",
    )
    if not records:
        raise BotActivationError(
            f"Nenhum Bot encontrado com DeveloperName = '{bot_api_name}'"
        )
    return records[0]["Id"]


def _find_latest_bot_version(instance_url: str, access_token: str, api_version: str, bot_id: str) -> dict:
    records = _query(
        instance_url,
        access_token,
        api_version,
        f"SELECT Id, VersionNumber, Status FROM BotVersion "
        f"WHERE BotDefinitionId = '{bot_id}' ORDER BY VersionNumber DESC LIMIT 1",
    )
    if not records:
        raise BotActivationError(f"Nenhuma BotVersion encontrada para o Bot {bot_id}")
    return records[0]


def _activate_bot_version(instance_url: str, access_token: str, api_version: str, bot_version_id: str) -> None:
    resp = requests.patch(
        f"{instance_url}/services/data/{api_version}/sobjects/BotVersion/{bot_version_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={"Status": "Active"},
        timeout=30,
    )
    # PATCH bem sucedido no REST API padrao retorna 204 sem corpo
    if resp.status_code != 204:
        raise BotActivationError(f"Falha ao ativar ({resp.status_code}): {resp.text}")


def main() -> None:
    bot_api_name = os.getenv("SF_BOT_API_NAME")
    if not bot_api_name:
        print("Defina SF_BOT_API_NAME no .env (rode config.py) ou passe como argumento:")
        print("  python activate_bot.py <DeveloperName_do_Bot>")
        if len(sys.argv) < 2:
            sys.exit(1)
        bot_api_name = sys.argv[1]

    api_version = os.getenv("SF_API_VERSION", "v61.0")

    try:
        auth = get_access_token()
        instance_url = auth["instance_url"]
        access_token = auth["access_token"]

        print(f"Buscando Bot '{bot_api_name}' (API {api_version})...")
        bot_id = _find_bot_id(instance_url, access_token, api_version, bot_api_name)

        print(f"Buscando BotVersion mais recente (BotDefinitionId={bot_id})...")
        bot_version = _find_latest_bot_version(instance_url, access_token, api_version, bot_id)
        print(
            f"  -> Id={bot_version['Id']} "
            f"VersionNumber={bot_version['VersionNumber']} "
            f"Status atual={bot_version['Status']}"
        )

        if bot_version["Status"] == "Active":
            print("Bot ja esta ativo. Nada a fazer.")
            return

        print("Ativando BotVersion...")
        _activate_bot_version(instance_url, access_token, api_version, bot_version["Id"])
        print("Bot ativado com sucesso.")

    except (AuthError, BotActivationError) as e:
        print(f"Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
