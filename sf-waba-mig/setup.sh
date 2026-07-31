#!/usr/bin/env bash
#
# setup.sh
# Cria o ambiente para rodar mig_waba.py:
#   - venv Python
#   - dependências (requirements.txt)
#
# Uso:
#   chmod +x setup.sh
#   ./setup.sh
#
# Depois, pra rodar:
#   source venv/bin/activate
#   python mig_waba.py --input ./messaging_components_v1 --json ./templates.json --output ./messaging_components_v2

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "==> Diretório do projeto: $PROJECT_DIR"

# ---------- .env ----------
if [ ! -f .env ]; then
  echo "==> Criando .env a partir de .env.example (opcional, preencha se quiser rodar sem passar --input/--json/--output)"
  cp .env.example .env
else
  echo "==> .env já existe, mantendo (não sobrescrito)"
fi

# ---------- venv ----------
if [ ! -d venv ]; then
  echo "==> Criando venv"
  python3 -m venv venv
else
  echo "==> venv já existe, mantendo"
fi

echo "==> Instalando dependências dentro do venv"
./venv/bin/pip install --upgrade pip --quiet
./venv/bin/pip install -r requirements.txt --quiet

echo ""
echo "==> Setup concluído."
echo "    1. (opcional) edite o .env com INPUT_DIR/JSON_PATH/OUTPUT_DIR"
echo "    2. source venv/bin/activate"
echo "    3. python mig_waba.py --input ./messaging_components_v1 --json ./templates.json --output ./messaging_components_v2"
