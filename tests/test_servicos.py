import sqlite3

import pytest

from portaria import repositorio as repo
from portaria import servicos
from portaria.erros import RegraNegocioErro
from tests.conftest import CPF_A, CPF_B


def situacao_cracha(conn, cracha_id):
    linha = conn.execute(
        """
        SELECT situacao
        FROM cracha
        WHERE id = ?
        """,
        (cracha_id,),
    ).fetchone()

    return linha["situacao"]


# ---------- cadastro de visitante ----------


def test_cadastra_visitante_normalizando_dados(conn):
    servicos.cadastrar_visitante(
        conn,
        "   Ana   Lima   ",
        "529.982.247-25",
    )

    visitante = repo.buscar_visitante_por_documento(
        conn,
        CPF_A,
    )

    assert visitante["nome"] == "Ana Lima"


def test_recusa_cpf_duplicado_mesmo_com_mascara_diferente(
    conn,
):
    servicos.cadastrar_visitante(
        conn,
        "Ana Lima",
        CPF_A,
    )

    with pytest.raises(
        RegraNegocioErro,
        match="Já existe",
    ):
        servicos.cadastrar_visitante(
            conn,
            "Outra Pessoa",
            "529.982.247-25",
        )


@pytest.mark.parametrize(
    "nome, cpf",
    [
        ("", CPF_A),
        ("   ", CPF_A),
        ("Ana Lima", ""),
        ("Ana Lima", "123"),
    ],
)
def test_recusa_cadastro_invalido(
    conn,
    nome,
    cpf,
):
    with pytest.raises(RegraNegocioErro):
        servicos.cadastrar_visitante(
            conn,
            nome,
            cpf,
        )


# ---------- entrada ----------


def test_entrada_cadastra_visitante_novo_na_mesma_operacao(
    conn,
    secretaria,
):
    visita_id = servicos.registrar_entrada(
        conn,
        CPF_A,
        secretaria,
        nome="   Ana   Lima   ",
    )

    visitante = repo.buscar_visitante_por_documento(
        conn,
        CPF_A,
    )
    visita = repo.obter_visita(
        conn,
        visita_id,
    )

    assert visitante["nome"] == "Ana Lima"
    assert visita["visitante_id"] == visitante["id"]


def test_falha_na_entrada_nao_persiste_visitante_novo(
    conn,
    secretaria,
    monkeypatch,
):
    def falha(*_):
        raise sqlite3.OperationalError(
            "falha simulada"
        )

    monkeypatch.setattr(
        repo,
        "atualizar_situacao_cracha",
        falha,
    )

    with pytest.raises(sqlite3.OperationalError):
        servicos.registrar_entrada(
            conn,
            CPF_A,
            secretaria,
            nome="Ana Lima",
        )

    assert (
        repo.buscar_visitante_por_documento(
            conn,
            CPF_A,
        )
        is None
    )

    assert repo.listar_presentes(conn) == []


def test_entrada_cria_visita_e_ocupa_cracha(
    conn,
    secretaria,
):
    servicos.cadastrar_visitante(
        conn,
        "Ana Lima",
        CPF_A,
    )

    visita_id = servicos.registrar_entrada(
        conn,
        CPF_A,
        secretaria,
    )

    visita = repo.obter_visita(
        conn,
        visita_id,
    )

    assert visita["saida"] is None

    assert (
        situacao_cracha(
            conn,
            visita["cracha_id"],
        )
        == "em_uso"
    )

    assert len(repo.listar_presentes(conn)) == 1


def test_entrada_recusa_visitante_que_ja_esta_no_predio(
    conn,
    secretaria,
):
    servicos.cadastrar_visitante(
        conn,
        "Ana Lima",
        CPF_A,
    )

    servicos.registrar_entrada(
        conn,
        CPF_A,
        secretaria,
    )

    with pytest.raises(
        RegraNegocioErro,
        match="já está no prédio",
    ):
        servicos.registrar_entrada(
            conn,
            CPF_A,
            secretaria,
        )


def test_entrada_respeita_lotacao_do_setor(
    conn,
    coordenacao,
):
    conn.execute(
        """
        UPDATE setor
        SET lotacao_maxima = 1
        WHERE id = ?
        """,
        (coordenacao,),
    )
    conn.commit()

    servicos.cadastrar_visitante(
        conn,
        "Ana Lima",
        CPF_A,
    )
    servicos.cadastrar_visitante(
        conn,
        "Bruno Sousa",
        CPF_B,
    )

    servicos.registrar_entrada(
        conn,
        CPF_A,
        coordenacao,
    )

    with pytest.raises(
        RegraNegocioErro,
        match="lotação",
    ):
        servicos.registrar_entrada(
            conn,
            CPF_B,
            coordenacao,
        )


def test_entrada_sem_cracha_disponivel_nao_cria_visita(
    conn,
    secretaria,
):
    with conn:
        conn.execute(
            """
            UPDATE cracha
            SET situacao = 'extraviado'
            """
        )

    servicos.cadastrar_visitante(
        conn,
        "Ana Lima",
        CPF_A,
    )

    with pytest.raises(
        RegraNegocioErro,
        match="crachá disponível",
    ):
        servicos.registrar_entrada(
            conn,
            CPF_A,
            secretaria,
        )

    assert repo.listar_presentes(conn) == []


def test_entrada_e_atomica_quando_atualizar_cracha_falha(
    conn,
    secretaria,
    monkeypatch,
):
    servicos.cadastrar_visitante(
        conn,
        "Ana Lima",
        CPF_A,
    )

    def falha(*_):
        raise sqlite3.OperationalError(
            "falha simulada"
        )

    monkeypatch.setattr(
        repo,
        "atualizar_situacao_cracha",
        falha,
    )

    with pytest.raises(sqlite3.OperationalError):
        servicos.registrar_entrada(
            conn,
            CPF_A,
            secretaria,
        )

    quantidade = conn.execute(
        "SELECT COUNT(*) FROM visita"
    ).fetchone()[0]

    assert quantidade == 0


# ---------- saída ----------


def test_saida_encerra_visita_e_devolve_cracha(
    conn,
    secretaria,
):
    servicos.cadastrar_visitante(
        conn,
        "Ana Lima",
        CPF_A,
    )

    visita_id = servicos.registrar_entrada(
        conn,
        CPF_A,
        secretaria,
        momento="2026-10-21 08:45:00",
    )

    servicos.registrar_saida(
        conn,
        visita_id,
        momento="2026-10-21 09:30:00",
    )

    visita = repo.obter_visita(
        conn,
        visita_id,
    )

    assert visita["saida"] == "2026-10-21 09:30:00"

    assert (
        situacao_cracha(
            conn,
            visita["cracha_id"],
        )
        == "disponivel"
    )


def test_saida_duplicada_e_recusada(
    conn,
    secretaria,
):
    servicos.cadastrar_visitante(
        conn,
        "Ana Lima",
        CPF_A,
    )

    visita_id = servicos.registrar_entrada(
        conn,
        CPF_A,
        secretaria,
    )

    servicos.registrar_saida(
        conn,
        visita_id,
    )

    with pytest.raises(
        RegraNegocioErro,
        match="já foi encerrada",
    ):
        servicos.registrar_saida(
            conn,
            visita_id,
        )


def test_saida_anterior_a_entrada_e_recusada(
    conn,
    secretaria,
):
    servicos.cadastrar_visitante(
        conn,
        "Ana Lima",
        CPF_A,
    )

    visita_id = servicos.registrar_entrada(
        conn,
        CPF_A,
        secretaria,
        momento="2026-10-21 09:30:00",
    )

    with pytest.raises(
        RegraNegocioErro,
        match="anterior",
    ):
        servicos.registrar_saida(
            conn,
            visita_id,
            momento="2026-10-21 09:00:00",
        )


# ---------- setores ----------


def test_setor_duplicado_e_recusado_mesmo_com_acento_e_caixa(
    conn,
):
    with pytest.raises(
        RegraNegocioErro,
        match="Já existe",
    ):
        servicos.salvar_setor(
            conn,
            "LABORATÓRIO",
            5,
        )


def test_setor_com_historico_nao_pode_ser_excluido(
    conn,
    secretaria,
):
    servicos.cadastrar_visitante(
        conn,
        "Ana Lima",
        CPF_A,
    )

    servicos.registrar_entrada(
        conn,
        CPF_A,
        secretaria,
    )

    with pytest.raises(
        RegraNegocioErro,
        match="Desative-o",
    ):
        servicos.excluir_setor(
            conn,
            secretaria,
        )


def test_setor_sem_historico_pode_ser_excluido(
    conn,
):
    setor_id = servicos.salvar_setor(
        conn,
        "Auditório",
        50,
    )

    servicos.excluir_setor(
        conn,
        setor_id,
    )

    assert repo.obter_setor(
        conn,
        setor_id,
    ) is None


def test_lotacao_nao_fica_abaixo_dos_presentes(
    conn,
    coordenacao,
):
    servicos.cadastrar_visitante(
        conn,
        "Ana Lima",
        CPF_A,
    )
    servicos.cadastrar_visitante(
        conn,
        "Bruno Sousa",
        CPF_B,
    )

    servicos.registrar_entrada(
        conn,
        CPF_A,
        coordenacao,
    )
    servicos.registrar_entrada(
        conn,
        CPF_B,
        coordenacao,
    )

    with pytest.raises(
        RegraNegocioErro,
        match="abaixo",
    ):
        servicos.salvar_setor(
            conn,
            "Coordenação",
            1,
            setor_id=coordenacao,
        )


# ---------- banco como segunda barreira ----------


def test_banco_impede_duas_visitas_abertas_mesmo_sem_servico(
    conn,
    secretaria,
):
    visitante_id = servicos.cadastrar_visitante(
        conn,
        "Ana Lima",
        CPF_A,
    )

    with conn:
        repo.inserir_visita(
            conn,
            visitante_id,
            secretaria,
            1,
            None,
            "2026-10-21 08:00:00",
        )

    with pytest.raises(sqlite3.IntegrityError):
        with conn:
            repo.inserir_visita(
                conn,
                visitante_id,
                secretaria,
                2,
                None,
                "2026-10-21 09:00:00",
            )


def test_banco_impede_excluir_visitante_com_historico(
    conn,
    secretaria,
):
    visitante_id = servicos.cadastrar_visitante(
        conn,
        "Ana Lima",
        CPF_A,
    )

    servicos.registrar_entrada(
        conn,
        CPF_A,
        secretaria,
    )

    with pytest.raises(sqlite3.IntegrityError):
        with conn:
            conn.execute(
                """
                DELETE FROM visitante
                WHERE id = ?
                """,
                (visitante_id,),
            )


# ---------- consultas ----------


def test_historico_filtra_por_termo_e_calcula_permanencia(
    conn,
    secretaria,
):
    servicos.cadastrar_visitante(
        conn,
        "Ana Lima",
        CPF_A,
    )

    visita_id = servicos.registrar_entrada(
        conn,
        CPF_A,
        secretaria,
        momento="2026-10-21 09:00:00",
    )

    servicos.registrar_saida(
        conn,
        visita_id,
        momento="2026-10-21 09:45:00",
    )

    linhas = repo.listar_historico(
        conn,
        "2026-10-21",
        "2026-10-21",
        "Ana",
    )

    assert len(linhas) == 1
    assert linhas[0]["minutos"] == 45

    assert (
        repo.listar_historico(
            conn,
            "2026-10-21",
            "2026-10-21",
            "Pessoa inexistente",
        )
        == []
    )