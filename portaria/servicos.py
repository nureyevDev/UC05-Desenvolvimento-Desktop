"""Regras de negócio da portaria.

A interface chama estas funções; elas validam, controlam a transação e
lançam RegraNegocioErro com mensagens prontas para o usuário.
"""

from datetime import datetime

from portaria import repositorio as repo
from portaria.erros import RegraNegocioErro
from portaria.validacao import (
    cpf_valido,
    normalizar_documento,
    normalizar_nome,
)



def agora() -> str:
    return datetime.now().isoformat(sep=" ", timespec="seconds")


def cadastrar_visitante(conn, nome: str, documento: str) -> int:
    nome = normalizar_nome(nome)
    doc = normalizar_documento(documento)
    if not nome:
        raise RegraNegocioErro("Informe o nome do visitante.")
    if not cpf_valido(doc):
        raise RegraNegocioErro("CPF inválido. Confira os 11 dígitos.")
    if repo.buscar_visitante_por_documento(conn, doc):
        raise RegraNegocioErro("Já existe um visitante com este CPF.")
    with conn:  # commit no sucesso, rollback em exceção
        return repo.inserir_visitante(conn, nome, doc)

def registrar_entrada(
    conn,
    documento: str,
    setor_id: int,
    motivo: str = "",
    momento: str | None = None,
    nome: str | None = None,
) -> int:
    """Cria a entrada e ocupa um crachá na mesma transação."""

    doc = normalizar_documento(documento)
    momento = momento or agora()

    setor = repo.obter_setor(conn, setor_id)

    if setor is None or not setor["ativo"]:
        raise RegraNegocioErro(
            "Selecione um setor de destino válido."
        )

    with conn:
        visitante = repo.buscar_visitante_por_documento(
            conn,
            doc,
        )

        if visitante is None:
            nome_normalizado = normalizar_nome(nome)

            if not nome_normalizado:
                raise RegraNegocioErro(
                    "Visitante não cadastrado. Informe o nome."
                )

            if not cpf_valido(doc):
                raise RegraNegocioErro(
                    "CPF inválido."
                )

            visitante_id = repo.inserir_visitante(
                conn,
                nome_normalizado,
                doc,
            )
        else:
            visitante_id = visitante["id"]

        if repo.visita_aberta_do_visitante(
            conn,
            visitante_id,
        ):
            raise RegraNegocioErro(
                "O visitante já está no prédio."
            )

        presentes = repo.contar_presentes_no_setor(
            conn,
            setor_id,
        )

        if presentes >= setor["lotacao_maxima"]:
            raise RegraNegocioErro(
                "O setor atingiu a lotação máxima."
            )

        cracha = repo.buscar_cracha_disponivel(conn)

        if cracha is None:
            raise RegraNegocioErro(
                "Não há crachá disponível."
            )

        visita_id = repo.inserir_visita(
            conn,
            visitante_id,
            setor_id,
            cracha["id"],
            motivo,
            momento,
        )

        repo.atualizar_situacao_cracha(
            conn,
            cracha["id"],
            "em_uso",
        )

        return visita_id

def registrar_saida(conn, visita_id: int, momento: str | None = None) -> None:
    """Check-out: encerra a visita E devolve o crachá na mesma transação."""
    momento = momento or agora()
    with conn:
        visita = repo.obter_visita(conn, visita_id)
        if visita is None:
            raise RegraNegocioErro("Visita não encontrada.")
        if visita["saida"] is not None:
            raise RegraNegocioErro("Esta visita já foi encerrada.")
        if momento < visita["entrada"]:
            raise RegraNegocioErro("A saída não pode ser anterior à entrada.")

        repo.encerrar_visita(conn, visita_id, momento)
        repo.atualizar_situacao_cracha(conn, visita["cracha_id"], "disponivel")
        
    # ---------- setores ----------

def salvar_setor(conn, nome: str, lotacao_maxima: int, ativo: bool = True,
                 setor_id: int | None = None) -> int:
    """Cria (setor_id=None) ou altera um setor, aplicando as regras de cadastro."""
    nome = normalizar_nome(nome)
    if not nome:
        raise RegraNegocioErro("Informe o nome do setor.")
    if lotacao_maxima < 1:
        raise RegraNegocioErro("A lotação máxima precisa ser de pelo menos 1 visitante.")

    # Comparação em Python: o lower() do SQLite não trata letras acentuadas.
    for s in repo.listar_setores(conn):
        if s["nome"].casefold() == nome.casefold() and s["id"] != setor_id:
            raise RegraNegocioErro(f"Já existe o setor {s['nome']}.")

    with conn:
        if setor_id is None:
            return repo.inserir_setor(conn, nome, lotacao_maxima)

        presentes = repo.contar_presentes_no_setor(conn, setor_id)
        if lotacao_maxima < presentes:
            raise RegraNegocioErro(
                f"Há {presentes} visitante(s) no setor agora. "
                "A lotação não pode ficar abaixo disso."
            )
        if not ativo and presentes:
            raise RegraNegocioErro("Não é possível desativar um setor com visitantes no prédio.")
        repo.atualizar_setor(conn, setor_id, nome, lotacao_maxima, ativo)
        return setor_id


def excluir_setor(conn, setor_id: int) -> None:
    """Exclusão protegida: setor com histórico de visitas só pode ser desativado."""
    with conn:
        if repo.contar_visitas_do_setor(conn, setor_id):
            raise RegraNegocioErro(
                "Este setor tem histórico de visitas e não pode ser excluído. Desative-o."
            )
        repo.excluir_setor(conn, setor_id)