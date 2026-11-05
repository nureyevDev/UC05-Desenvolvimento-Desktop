from string import Template

from PySide6.QtCore import QSettings

from portaria.ui import ARQUIVO_ESTILO


PASTA_ICONES = ARQUIVO_ESTILO.with_name("icones")


TEMAS = {
    "claro": {
        "fundo": "#f6f7f9",
        "superficie": "#ffffff",
        "texto": "#1f2328",
        "texto_suave": "#57606a",
        "borda": "#d0d7de",
        "primaria": "#0b5ed7",
        "primaria_hover": "#0a58ca",
        "primaria_texto": "#ffffff",
        "perigo": "#b42318",
        "perigo_texto": "#ffffff",
        "foco": "#052c65",
        "aviso_fundo": "#e7f1ff",
        "aviso_borda": "#b6d4fe",
        "aviso_texto": "#052c65",
        "zebra": "#f3f6fa",
        "selecao": "#cfe2ff",
        "raio": "6px",
    },
    "escuro": {
        "fundo": "#1b1f24",
        "superficie": "#24292f",
        "texto": "#e6edf3",
        "texto_suave": "#9da7b3",
        "borda": "#3d444d",
        "primaria": "#4493f8",
        "primaria_hover": "#539bf5",
        "primaria_texto": "#0d1117",
        "perigo": "#f47067",
        "perigo_texto": "#0d1117",
        "foco": "#a5d6ff",
        "aviso_fundo": "#132339",
        "aviso_borda": "#1f4a7a",
        "aviso_texto": "#c9e1ff",
        "zebra": "#2a3038",
        "selecao": "#1f4a7a",
        "raio": "6px",
    },
        "tema_nureyev": {
        "fundo": "#101827",
        "superficie": "#182338",
        "texto": "#f1f5fb",
        "texto_suave": "#b4c0d4",
        "borda": "#34435e",
        "primaria": "#3867d6",
        "primaria_hover": "#4b7bec",
        "primaria_texto": "#ffffff",
        "perigo": "#dc5a64",
        "perigo_texto": "#ffffff",
        "foco": "#82aaff",
        "aviso_fundo": "#1c3155",
        "aviso_borda": "#466ca6",
        "aviso_texto": "#dce9ff",
        "zebra": "#1d2a42",
        "selecao": "#294b7a",
        "raio": "8px",
    },
}


def gerar_folha(nome_tema: str = "claro") -> str:
    """Troca cada marcador do estilo.qss pelo valor do tema."""

    if nome_tema not in TEMAS:
        nome_tema = "claro"

    valores = dict(TEMAS[nome_tema])
    valores["tema"] = nome_tema
    valores["icones"] = PASTA_ICONES.as_posix()

    modelo = Template(
        ARQUIVO_ESTILO.read_text(
            encoding="utf-8"
        )
    )

    return modelo.substitute(valores)


def _configuracoes() -> QSettings:
    return QSettings(
        "Senac-PI",
        "PortariaDigital",
    )


def tema_salvo() -> str:
    nome = _configuracoes().value(
        "tema",
        "claro",
    )

    return nome if nome in TEMAS else "claro"


def salvar_tema(nome_tema: str) -> None:
    _configuracoes().setValue(
        "tema",
        nome_tema,
    )


def contraste(
    cor_a: str,
    cor_b: str,
) -> float:
    """Calcula a razão de contraste WCAG entre duas cores."""

    def luminancia(cor: str) -> float:
        cor = cor.lstrip("#")

        canais = [
            int(cor[i:i + 2], 16) / 255
            for i in (0, 2, 4)
        ]

        lineares = [
            canal / 12.92
            if canal <= 0.03928
            else ((canal + 0.055) / 1.055) ** 2.4
            for canal in canais
        ]

        vermelho, verde, azul = lineares

        return (
            0.2126 * vermelho
            + 0.7152 * verde
            + 0.0722 * azul
        )

    clara, escura = sorted(
        (
            luminancia(cor_a),
            luminancia(cor_b),
        ),
        reverse=True,
    )

    return (clara + 0.05) / (escura + 0.05)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStyle


def estilizar_botao(
    botao,
    variante=None,
    icone=None,
):
    if variante:
        botao.setProperty("variante", variante)

    botao.setCursor(
        Qt.CursorShape.PointingHandCursor
    )

    if icone is not None:
        botao.setIcon(
            botao.style().standardIcon(icone)
        )

    return botao