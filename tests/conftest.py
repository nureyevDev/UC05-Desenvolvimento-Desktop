import pytest

from portaria.db import conectar, preparar_banco


# CPFs fictícios com dígitos verificadores válidos,
# usados somente nos testes.
CPF_A = "52998224725"
CPF_B = "11144477735"


@pytest.fixture
def conn():
    """Cria um banco em memória novo para cada teste."""
    conexao = conectar(":memory:")
    preparar_banco(conexao)

    yield conexao

    conexao.close()


@pytest.fixture
def secretaria(conn):
    """Retorna o código do setor Secretaria."""
    linha = conn.execute(
        """
        SELECT id
        FROM setor
        WHERE nome = 'Secretaria'
        """
    ).fetchone()

    return linha["id"]


@pytest.fixture
def coordenacao(conn):
    """Retorna o código do setor Coordenação."""
    linha = conn.execute(
        """
        SELECT id
        FROM setor
        WHERE nome = 'Coordenação'
        """
    ).fetchone()

    return linha["id"]