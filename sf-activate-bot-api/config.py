"""
config.py

Roda ANTES do activate_bot.py. Pergunta no terminal o DeveloperName
(API Name) do Bot e grava no .env, preservando as demais variaveis
ja existentes (SF_LOGIN_URL, SF_CLIENT_ID, SF_CLIENT_SECRET).

── USO ─────────────────────────────────────────────────────────
python config.py
python activate_bot.py
"""

ENV_PATH = ".env"


def read_env(path: str) -> dict:
    """Le o .env existente (se houver) para um dict, preservando ordem."""
    valores = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, _, valor = linha.partition("=")
                valores[chave.strip()] = valor.strip()
    except FileNotFoundError:
        pass
    return valores


def write_env(path: str, valores: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for chave, valor in valores.items():
            f.write(f'{chave}="{valor}"\n')


def main() -> None:
    valores = read_env(ENV_PATH)

    print("Configuracao do Einstein Bot")
    bot_api_name = input(
        f"DeveloperName (API Name) do Bot [{valores.get('SF_BOT_API_NAME', '')}]: "
    ).strip()
    if bot_api_name:
        valores["SF_BOT_API_NAME"] = bot_api_name

    write_env(ENV_PATH, valores)
    print(f"Gravado em {ENV_PATH}.")


if __name__ == "__main__":
    main()
