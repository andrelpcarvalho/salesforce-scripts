#!/usr/bin/env bash
#
# setup.sh
# Cria o ambiente para rodar os fluxos de query e update via Bulk API 2.0:
#   - venv Python (compartilhado pelos dois fluxos)
#   - requirements.txt
#   - .env (template, com valores em branco para você preencher)
#
# Uso:
#   chmod +x setup.sh
#   ./setup.sh
#
# Depois:
#   source venv/bin/activate
#   python run_query.py    # fluxo de leitura (SOQL -> CSV)
#   python run_update.py   # fluxo de escrita em massa (insert/update/upsert/delete)

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "==> Diretório do projeto: $PROJECT_DIR"

if [ ! -f requirements.txt ]; then
  echo "==> Criando requirements.txt"
  cat > requirements.txt <<'EOF'
requests>=2.31.0
python-dotenv>=1.0.0
EOF
else
  echo "==> requirements.txt já existe, mantendo"
fi

if [ ! -f .env ]; then
  echo "==> Criando .env a partir de .env.example (preencha os valores antes de rodar)"
  cp .env.example .env
  echo "    -> Edite o .env e preencha SF_CLIENT_ID, SF_CLIENT_SECRET e SF_LOGIN_URL"
  echo "    -> O resto (SF_OBJECT, SF_FIELDS, SF_OPERATION etc.) também pode ser"
  echo "       preenchido interativamente via 'python configure_query.py' ou"
  echo "       'python configure_update.py' (ou simplesmente rodando run_query.py"
  echo "       / run_update.py, que já chamam isso pra você)."
else
  echo "==> .env já existe, mantendo (não sobrescrito)"
fi

if [ ! -f .gitignore ]; then
  echo "==> Criando .gitignore"
  cat > .gitignore <<'EOF'
.env
venv/
logs/
csv/
output/
header_mapping.json
__pycache__/
*.pyc
EOF
fi

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
echo "    1. source venv/bin/activate"
echo "    2. python run_query.py    (ou python run_update.py)"
