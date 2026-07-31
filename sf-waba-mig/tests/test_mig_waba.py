#!/usr/bin/env python3
"""
Testes para mig_waba.py

Rodar com (da raiz do projeto sf-waba-mig):
    pip install -r requirements-dev.txt
    pytest tests/ -v
"""

import json
import sys
from pathlib import Path

import pytest

import mig_waba as gmv2


# ---------------------------------------------------------------------------
# Fixtures de dados reutilizáveis
# ---------------------------------------------------------------------------

@pytest.fixture
def templates_basico():
    """Lista de templates sem ambiguidade de nome."""
    return [
        {"name": "validacao_de_instalacao_instalador__v2", "language": "pt_BR",
         "status": "APPROVED", "id": "860968043551396"},
        {"name": "confirmacao_pedido", "language": "pt_BR",
         "status": "APPROVED", "id": "111222333444555"},
    ]


@pytest.fixture
def templates_ambiguos():
    """Mesmo name em dois idiomas diferentes -> exige desempate por language."""
    return [
        {"name": "boas_vindas", "language": "pt_BR", "status": "APPROVED", "id": "PT111"},
        {"name": "boas_vindas", "language": "en_US", "status": "APPROVED", "id": "EN222"},
    ]


@pytest.fixture
def bloco_xml_valido():
    return (
        "<externalTemplates>"
        "<templateName>validacao_de_instalacao_instalador__v2</templateName>"
        "<language>pt_BR</language>"
        "<templateVersionIdentifier>ID_ANTIGO</templateVersionIdentifier>"
        "</externalTemplates>"
    )


# ---------------------------------------------------------------------------
# carregar_json
# ---------------------------------------------------------------------------

class TestCarregarJson:
    def test_carrega_lista_valida(self, tmp_path):
        caminho = tmp_path / "templates.json"
        caminho.write_text(json.dumps([{"name": "x", "id": "1"}]), encoding="utf-8")

        resultado = gmv2.carregar_json(caminho)

        assert resultado == [{"name": "x", "id": "1"}]

    def test_arquivo_inexistente_encerra_execucao(self, tmp_path):
        caminho = tmp_path / "nao_existe.json"

        with pytest.raises(SystemExit):
            gmv2.carregar_json(caminho)

    def test_json_malformado_encerra_execucao(self, tmp_path):
        caminho = tmp_path / "templates.json"
        caminho.write_text("{ isso nao é json valido", encoding="utf-8")

        with pytest.raises(SystemExit):
            gmv2.carregar_json(caminho)

    def test_json_nao_e_lista_encerra_execucao(self, tmp_path):
        caminho = tmp_path / "templates.json"
        caminho.write_text(json.dumps({"name": "x"}), encoding="utf-8")

        with pytest.raises(SystemExit):
            gmv2.carregar_json(caminho)


# ---------------------------------------------------------------------------
# buscar_id
# ---------------------------------------------------------------------------

class TestBuscarId:
    def test_encontra_id_com_name_unico(self, templates_basico):
        id_, erro = gmv2.buscar_id("confirmacao_pedido", "pt_BR", templates_basico)

        assert id_ == "111222333444555"
        assert erro is None

    def test_name_nao_encontrado(self, templates_basico):
        id_, erro = gmv2.buscar_id("nao_existe", "pt_BR", templates_basico)

        assert id_ is None
        assert erro == "nao_encontrado"

    def test_desempata_por_language_quando_ambiguo(self, templates_ambiguos):
        id_, erro = gmv2.buscar_id("boas_vindas", "en_US", templates_ambiguos)

        assert id_ == "EN222"
        assert erro is None

    def test_ambiguo_sem_language_compativel(self, templates_ambiguos):
        id_, erro = gmv2.buscar_id("boas_vindas", "es_ES", templates_ambiguos)

        assert id_ is None
        assert erro == "ambiguo"

    @pytest.mark.parametrize("idioma_xml", [None, ""])
    def test_ambiguo_sem_idioma_no_xml(self, templates_ambiguos, idioma_xml):
        id_, erro = gmv2.buscar_id("boas_vindas", idioma_xml, templates_ambiguos)

        assert id_ is None
        assert erro == "ambiguo"


# ---------------------------------------------------------------------------
# processar_bloco
# ---------------------------------------------------------------------------

class TestProcessarBloco:
    def test_substitui_version_identifier_com_sucesso(self, bloco_xml_valido, templates_basico):
        novo_bloco, erro = gmv2.processar_bloco(bloco_xml_valido, templates_basico)

        assert erro is None
        assert "<templateVersionIdentifier>860968043551396</templateVersionIdentifier>" in novo_bloco
        assert "ID_ANTIGO" not in novo_bloco

    def test_preserva_resto_do_bloco_intacto(self, bloco_xml_valido, templates_basico):
        novo_bloco, _ = gmv2.processar_bloco(bloco_xml_valido, templates_basico)

        assert "<templateName>validacao_de_instalacao_instalador__v2</templateName>" in novo_bloco
        assert "<language>pt_BR</language>" in novo_bloco

    def test_bloco_sem_template_name(self, templates_basico):
        bloco = "<externalTemplates><language>pt_BR</language></externalTemplates>"

        resultado, erro = gmv2.processar_bloco(bloco, templates_basico)

        assert erro == "sem_templateName"
        assert resultado == bloco  # bloco retornado sem alteração

    def test_bloco_com_template_nao_encontrado_no_json(self, templates_basico):
        bloco = (
            "<externalTemplates>"
            "<templateName>template_fantasma</templateName>"
            "<language>pt_BR</language>"
            "<templateVersionIdentifier>ID_ANTIGO</templateVersionIdentifier>"
            "</externalTemplates>"
        )

        resultado, erro = gmv2.processar_bloco(bloco, templates_basico)

        assert "nao_encontrado" in erro
        assert "template_fantasma" in erro
        assert resultado == bloco

    def test_template_name_com_espacos_e_normalizado(self, templates_basico):
        bloco = (
            "<externalTemplates>"
            "<templateName>\n  confirmacao_pedido  \n</templateName>"
            "<language>pt_BR</language>"
            "<templateVersionIdentifier>ID_ANTIGO</templateVersionIdentifier>"
            "</externalTemplates>"
        )

        novo_bloco, erro = gmv2.processar_bloco(bloco, templates_basico)

        assert erro is None
        assert "111222333444555" in novo_bloco


# ---------------------------------------------------------------------------
# montar_nome_saida
# ---------------------------------------------------------------------------

class TestMontarNomeSaida:
    def test_extensao_conversation_message_definition(self):
        nome = "boas_vindas.conversationMessageDefinition-meta.xml"

        resultado = gmv2.montar_nome_saida(nome)

        assert resultado == "boas_vindas_v2.conversationMessageDefinition-meta.xml"

    def test_fallback_xml_generico(self):
        resultado = gmv2.montar_nome_saida("arquivo_qualquer.xml")

        assert resultado == "arquivo_qualquer_v2.xml"

    def test_fallback_sem_extensao_conhecida(self):
        resultado = gmv2.montar_nome_saida("arquivo_sem_extensao")

        assert resultado == "arquivo_sem_extensao_v2"


# ---------------------------------------------------------------------------
# resolver_config (prioridade CLI > .env)
# ---------------------------------------------------------------------------

class TestResolverConfig:
    def test_usa_argumentos_de_cli_quando_informados(self, monkeypatch):
        monkeypatch.setenv("INPUT_DIR", "/env/input")
        monkeypatch.setenv("JSON_PATH", "/env/templates.json")
        monkeypatch.setenv("OUTPUT_DIR", "/env/output")

        resultado = gmv2.resolver_config("/cli/input", "/cli/templates.json", "/cli/output")

        assert resultado == ("/cli/input", "/cli/templates.json", "/cli/output")

    def test_usa_env_quando_cli_nao_informado(self, monkeypatch):
        monkeypatch.setenv("INPUT_DIR", "/env/input")
        monkeypatch.setenv("JSON_PATH", "/env/templates.json")
        monkeypatch.setenv("OUTPUT_DIR", "/env/output")

        resultado = gmv2.resolver_config(None, None, None)

        assert resultado == ("/env/input", "/env/templates.json", "/env/output")

    def test_mistura_cli_e_env(self, monkeypatch):
        monkeypatch.setenv("INPUT_DIR", "/env/input")
        monkeypatch.setenv("JSON_PATH", "/env/templates.json")
        monkeypatch.setenv("OUTPUT_DIR", "/env/output")

        resultado = gmv2.resolver_config("/cli/input", None, None)

        assert resultado == ("/cli/input", "/env/templates.json", "/env/output")

    def test_encerra_execucao_quando_nada_informado(self):
        with pytest.raises(SystemExit):
            gmv2.resolver_config(None, None, None)


# ---------------------------------------------------------------------------
# processar_arquivo (integração leve, com arquivos reais em tmp_path)
# ---------------------------------------------------------------------------

class TestProcessarArquivo:
    def _escreve_xml(self, tmp_path, nome, conteudo):
        caminho = tmp_path / nome
        caminho.write_text(conteudo, encoding="utf-8")
        return caminho

    def test_gera_arquivo_v2_com_id_atualizado(self, tmp_path, templates_basico, bloco_xml_valido):
        input_dir = tmp_path / "in"
        output_dir = tmp_path / "out"
        input_dir.mkdir()
        output_dir.mkdir()

        conteudo = f"<root>{bloco_xml_valido}</root>"
        xml_path = self._escreve_xml(
            input_dir, "teste.conversationMessageDefinition-meta.xml", conteudo
        )

        gmv2.processar_arquivo(xml_path, templates_basico, output_dir)

        arquivo_saida = output_dir / "teste_v2.conversationMessageDefinition-meta.xml"
        assert arquivo_saida.exists()
        texto_saida = arquivo_saida.read_text(encoding="utf-8")
        assert "860968043551396" in texto_saida
        assert "ID_ANTIGO" not in texto_saida

    def test_arquivo_sem_bloco_externaltemplates_e_copiado_sem_alteracao(
        self, tmp_path, templates_basico
    ):
        input_dir = tmp_path / "in"
        output_dir = tmp_path / "out"
        input_dir.mkdir()
        output_dir.mkdir()

        conteudo = "<root><outraTag>valor</outraTag></root>"
        xml_path = self._escreve_xml(
            input_dir, "sem_bloco.conversationMessageDefinition-meta.xml", conteudo
        )

        gmv2.processar_arquivo(xml_path, templates_basico, output_dir)

        arquivo_saida = output_dir / "sem_bloco_v2.conversationMessageDefinition-meta.xml"
        assert arquivo_saida.read_text(encoding="utf-8") == conteudo

    def test_multiplos_blocos_no_mesmo_arquivo(self, tmp_path, templates_basico):
        input_dir = tmp_path / "in"
        output_dir = tmp_path / "out"
        input_dir.mkdir()
        output_dir.mkdir()

        bloco1 = (
            "<externalTemplates>"
            "<templateName>validacao_de_instalacao_instalador__v2</templateName>"
            "<language>pt_BR</language>"
            "<templateVersionIdentifier>OLD1</templateVersionIdentifier>"
            "</externalTemplates>"
        )
        bloco2 = (
            "<externalTemplates>"
            "<templateName>confirmacao_pedido</templateName>"
            "<language>pt_BR</language>"
            "<templateVersionIdentifier>OLD2</templateVersionIdentifier>"
            "</externalTemplates>"
        )
        conteudo = f"<root>{bloco1}{bloco2}</root>"
        xml_path = self._escreve_xml(
            input_dir, "multi.conversationMessageDefinition-meta.xml", conteudo
        )

        gmv2.processar_arquivo(xml_path, templates_basico, output_dir)

        saida = (output_dir / "multi_v2.conversationMessageDefinition-meta.xml").read_text(
            encoding="utf-8"
        )
        assert "860968043551396" in saida
        assert "111222333444555" in saida

    def test_bloco_com_erro_nao_impede_gravacao_parcial(self, tmp_path, templates_basico):
        """Um bloco com template não encontrado não deve travar o processamento
        dos demais blocos nem impedir a gravação do arquivo."""
        input_dir = tmp_path / "in"
        output_dir = tmp_path / "out"
        input_dir.mkdir()
        output_dir.mkdir()

        bloco_ok = (
            "<externalTemplates>"
            "<templateName>confirmacao_pedido</templateName>"
            "<language>pt_BR</language>"
            "<templateVersionIdentifier>OLD_OK</templateVersionIdentifier>"
            "</externalTemplates>"
        )
        bloco_com_erro = (
            "<externalTemplates>"
            "<templateName>fantasma</templateName>"
            "<language>pt_BR</language>"
            "<templateVersionIdentifier>OLD_ERRO</templateVersionIdentifier>"
            "</externalTemplates>"
        )
        conteudo = f"<root>{bloco_ok}{bloco_com_erro}</root>"
        xml_path = self._escreve_xml(
            input_dir, "parcial.conversationMessageDefinition-meta.xml", conteudo
        )

        gmv2.processar_arquivo(xml_path, templates_basico, output_dir)

        saida = (output_dir / "parcial_v2.conversationMessageDefinition-meta.xml").read_text(
            encoding="utf-8"
        )
        # bloco válido foi atualizado
        assert "111222333444555" in saida
        # bloco com erro permanece com o valor antigo, intacto
        assert "OLD_ERRO" in saida


# ---------------------------------------------------------------------------
# main (fim a fim via CLI args, usando tmp_path)
# ---------------------------------------------------------------------------

class TestMainEndToEnd:
    def test_fluxo_completo_gera_arquivos_v2(self, tmp_path, monkeypatch, templates_basico, bloco_xml_valido):
        input_dir = tmp_path / "in"
        output_dir = tmp_path / "out"
        input_dir.mkdir()

        json_path = tmp_path / "templates.json"
        json_path.write_text(json.dumps(templates_basico), encoding="utf-8")

        (input_dir / "componente.conversationMessageDefinition-meta.xml").write_text(
            f"<root>{bloco_xml_valido}</root>", encoding="utf-8"
        )

        argv = [
            "gerar_messaging_component_v2.py",
            "--input", str(input_dir),
            "--json", str(json_path),
            "--output", str(output_dir),
        ]
        monkeypatch.setattr(sys, "argv", argv)

        gmv2.main()

        arquivo_gerado = output_dir / "componente_v2.conversationMessageDefinition-meta.xml"
        assert arquivo_gerado.exists()
        assert "860968043551396" in arquivo_gerado.read_text(encoding="utf-8")

    def test_pasta_de_entrada_inexistente_encerra_com_erro(self, tmp_path, monkeypatch):
        json_path = tmp_path / "templates.json"
        json_path.write_text("[]", encoding="utf-8")

        argv = [
            "gerar_messaging_component_v2.py",
            "--input", str(tmp_path / "nao_existe"),
            "--json", str(json_path),
            "--output", str(tmp_path / "out"),
        ]
        monkeypatch.setattr(sys, "argv", argv)

        with pytest.raises(SystemExit):
            gmv2.main()

    def test_pasta_sem_xml_encerra_com_erro(self, tmp_path, monkeypatch):
        input_dir = tmp_path / "in"
        input_dir.mkdir()
        json_path = tmp_path / "templates.json"
        json_path.write_text("[]", encoding="utf-8")

        argv = [
            "gerar_messaging_component_v2.py",
            "--input", str(input_dir),
            "--json", str(json_path),
            "--output", str(tmp_path / "out"),
        ]
        monkeypatch.setattr(sys, "argv", argv)

        with pytest.raises(SystemExit):
            gmv2.main()

    def test_fluxo_completo_via_env_sem_argumentos_de_cli(
        self, tmp_path, monkeypatch, templates_basico, bloco_xml_valido
    ):
        input_dir = tmp_path / "in"
        output_dir = tmp_path / "out"
        input_dir.mkdir()

        json_path = tmp_path / "templates.json"
        json_path.write_text(json.dumps(templates_basico), encoding="utf-8")

        (input_dir / "componente.conversationMessageDefinition-meta.xml").write_text(
            f"<root>{bloco_xml_valido}</root>", encoding="utf-8"
        )

        monkeypatch.setenv("INPUT_DIR", str(input_dir))
        monkeypatch.setenv("JSON_PATH", str(json_path))
        monkeypatch.setenv("OUTPUT_DIR", str(output_dir))
        monkeypatch.setattr(sys, "argv", ["mig_waba.py"])

        gmv2.main()

        arquivo_gerado = output_dir / "componente_v2.conversationMessageDefinition-meta.xml"
        assert arquivo_gerado.exists()
        assert "860968043551396" in arquivo_gerado.read_text(encoding="utf-8")

    def test_sem_cli_e_sem_env_encerra_com_erro(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["mig_waba.py"])

        with pytest.raises(SystemExit):
            gmv2.main()
