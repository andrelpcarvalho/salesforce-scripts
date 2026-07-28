"""
auth.py

Autentica na org via OAuth 2.0 Client Credentials Flow e retorna
access_token + instance_url, no mesmo padrao usado nos outros
projetos (sf-jwt / bulk-api).

Variaveis esperadas no .env:
    SF_LOGIN_URL     -> ex: https://minhaorg.my.salesforce.com
    SF_CLIENT_ID     -> Consumer Key da Connected App
    SF_CLIENT_SECRET -> Consumer Secret da Connected App
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


class AuthError(Exception):
    """Erro ao autenticar na org."""


def get_access_token() -> dict:
    """
    Faz o Client Credentials Flow e retorna:
        {"access_token": ..., "instance_url": ...}
    """
    login_url = os.getenv("SF_LOGIN_URL")
    client_id = os.getenv("SF_CLIENT_ID")
    client_secret = os.getenv("SF_CLIENT_SECRET")

    faltando = [
        nome
        for nome, valor in [
            ("SF_LOGIN_URL", login_url),
            ("SF_CLIENT_ID", client_id),
            ("SF_CLIENT_SECRET", client_secret),
        ]
        if not valor
    ]
    if faltando:
        raise AuthError(f"Faltam variaveis no .env: {', '.join(faltando)}")

    resp = requests.post(
        f"{login_url}/services/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )

    if resp.status_code != 200:
        raise AuthError(f"Falha na autenticacao ({resp.status_code}): {resp.text}")

    data = resp.json()
    return {
        "access_token": data["access_token"],
        "instance_url": data["instance_url"],
    }
