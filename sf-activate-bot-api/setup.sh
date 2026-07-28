#!/usr/bin/env bash
set -e

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo ".env criado a partir de .env.example -- preencha as credenciais."
fi

echo ""
echo "Proximos passos:"
echo "  source .venv/bin/activate"
echo "  # edite .env com SF_LOGIN_URL, SF_CLIENT_ID, SF_CLIENT_SECRET"
echo "  python config.py"
echo "  python activate_bot.py"
