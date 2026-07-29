#!/usr/bin/env python3
"""
Gera Messaging Components v2 a partir dos XMLs v1.

Para cada bloco <externalTemplates>...</externalTemplates> encontrado no XML,
o script:
  1. Lê o valor de <templateName>
  2. Busca no JSON (lista de objetos de template) um item cujo "name" seja igual
     - se houver mais de um item com o mesmo "name", desempata usando <language>
       do XML vs "language" do JSON
  3. Substitui o conteúdo de <templateVersionIdentifier> pelo "id" encontrado
  4. Mantém TODO o resto do arquivo (formatação, outras tags, etc.) exatamente igual

Uso:
    python gerar_messaging_component_v2.py \
        --input ./messaging_components_v1 \
        --json ./templates.json \
        --output ./messaging_components_v2

Formato esperado do JSON (lista de objetos, um por template):
[
    {
        "name": "validacao_de_instalacao_instalador__v2",
        "language": "pt_BR",
        "status": "APPROVED",
        "id": "860968043551396"
    },
    ...
]
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Captura cada bloco <externalTemplates>...</externalTemplates> inteiro
BLOCK_PATTERN = re.compile(
    r"<externalTemplates>.*?</externalTemplates>",
    re.DOTALL,
)

TEMPLATE_NAME_PATTERN = re.compile(r"<templateName>(.*?)</templateName>", re.DOTALL)
LANGUAGE_PATTERN = re.compile(r"<language>(.*?)</language>", re.DOTALL)
VERSION_ID_PATTERN = re.compile(
    r"(<templateVersionIdentifier>)(.*?)(</templateVersionIdentifier>)", re.DOTALL
)


def carregar_json(caminho_json: Path) -> list:
    if not caminho_json.exists():
        sys.exit(f"[ERRO] JSON não encontrado: {caminho_json}")
    with open(caminho_json, "r", encoding="utf-8") as f:
        try:
            dados = json.load(f)
        except json.JSONDecodeError as e:
            sys.exit(f"[ERRO] JSON inválido: {e}")

    if not isinstance(dados, list):
        sys.exit("[ERRO] Esperado um array (lista) de templates no JSON.")
    return dados


def buscar_id(nome: str, idioma: str, templates: list):
    """Retorna o 'id' do template cujo name (e language, se necessário) bate com o XML."""
    candidatos = [t for t in templates if t.get("name") == nome]

    if not candidatos:
        return None, "nao_encontrado"

    if len(candidatos) == 1:
        return candidatos[0].get("id"), None

    # Mais de um candidato com o mesmo name -> desempata por language
    por_idioma = [t for t in candidatos if t.get("language") == idioma]
    if len(por_idioma) == 1:
        return por_idioma[0].get("id"), None

    return None, "ambiguo"


def processar_bloco(bloco: str, templates: list):
    nome_match = TEMPLATE_NAME_PATTERN.search(bloco)
    if not nome_match:
        return bloco, "sem_templateName"

    nome = nome_match.group(1).strip()

    idioma_match = LANGUAGE_PATTERN.search(bloco)
    idioma = idioma_match.group(1).strip() if idioma_match else None

    novo_id, erro = buscar_id(nome, idioma, templates)
    if erro:
        return bloco, f"{erro} (templateName='{nome}')"

    novo_bloco = VERSION_ID_PATTERN.sub(rf"\g<1>{novo_id}\g<3>", bloco, count=1)
    return novo_bloco, None


def processar_arquivo(xml_path: Path, templates: list, output_dir: Path):
    conteudo = xml_path.read_text(encoding="utf-8")

    blocos = BLOCK_PATTERN.findall(conteudo)
    if not blocos:
        print(f"  [AVISO] Nenhum bloco <externalTemplates> encontrado em {xml_path.name} — copiando sem alterações.")
        (output_dir / xml_path.name).write_text(conteudo, encoding="utf-8")
        return

    novo_conteudo = conteudo
    problemas = []

    for bloco in blocos:
        novo_bloco, erro = processar_bloco(bloco, templates)
        if erro:
            problemas.append(erro)
            continue
        novo_conteudo = novo_conteudo.replace(bloco, novo_bloco, 1)

    destino = output_dir / xml_path.name
    destino.write_text(novo_conteudo, encoding="utf-8")

    if problemas:
        print(f"  [PARCIAL] {xml_path.name}: {len(blocos) - len(problemas)}/{len(blocos)} bloco(s) atualizados.")
        for p in problemas:
            print(f"      - {p}")
    else:
        print(f"  [OK] {xml_path.name}: {len(blocos)} bloco(s) atualizados.")


def main():
    parser = argparse.ArgumentParser(description="Gera Messaging Components v2 a partir dos XMLs v1.")
    parser.add_argument("--input", required=True, help="Pasta com os XMLs v1")
    parser.add_argument("--json", required=True, help="Arquivo JSON com a lista de templates (name, language, id)")
    parser.add_argument("--output", required=True, help="Pasta de saída para os XMLs v2")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    json_path = Path(args.json)

    if not input_dir.is_dir():
        sys.exit(f"[ERRO] Pasta de entrada não encontrada: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    templates = carregar_json(json_path)

    xml_files = sorted(input_dir.glob("*.xml"))
    if not xml_files:
        sys.exit(f"[ERRO] Nenhum .xml encontrado em {input_dir}")

    print(f"Encontrados {len(xml_files)} arquivo(s) XML em {input_dir}\n")

    for xml_file in xml_files:
        processar_arquivo(xml_file, templates, output_dir)

    print(f"\nConcluído. Arquivos v2 gerados em: {output_dir}")


if __name__ == "__main__":
    main()