"""Regras de negócio da portaria.

A interface chama estas funções; elas validam, controlam a transação e
lançam RegraNegocioErro com mensagens prontas para o usuário.
"""

from datetime import datetime

from portaria import repositorio as repo
from portaria.erros import RegraNegocioErro
from portaria.validacao import cpf_valido, normalizar_documento, normalizar_nome


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


def registrar_entrada(conn, documento: str, setor_id: int, motivo: str = "",
                      momento: str | None = None) -> int:
    """Check-in: cria a visita E ocupa um crachá na MESMA transação (RN03)."""
    doc = normalizar_documento(documento)
    visitante = repo.buscar_visitante_por_documento(conn, doc)
    if visitante is None:
        raise RegraNegocioErro("Visitante não cadastrado. Cadastre antes da entrada.")

    setor = repo.obter_setor(conn, setor_id)
    if setor is None or not setor["ativo"]:
        raise RegraNegocioErro("Selecione um setor de destino válido.")

    # Aplicação desktop monousuário: as leituras abaixo e a escrita ficam no
    # mesmo bloco. Com vários terminais no mesmo banco, discutir BEGIN IMMEDIATE.
    with conn:
        if repo.visita_aberta_do_visitante(conn, visitante["id"]):
            raise RegraNegocioErro(
                f"{visitante['nome']} já está no prédio. Registre a saída antes."
            )
        if repo.contar_presentes_no_setor(conn, setor_id) >= setor["lotacao_maxima"]:
            raise RegraNegocioErro(
                f"{setor['nome']} atingiu a lotação de {setor['lotacao_maxima']} visitantes."
            )
        cracha = repo.buscar_cracha_disponivel(conn)
        if cracha is None:
            raise RegraNegocioErro("Não há crachá disponível. Aguarde uma devolução.")

        visita_id = repo.inserir_visita(
            conn, visitante["id"], setor_id, cracha["id"],
            normalizar_nome(motivo) or None, momento or agora(),
        )
        repo.atualizar_situacao_cracha(conn, cracha["id"], "em_uso")
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