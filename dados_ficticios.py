import argparse
import random
from datetime import datetime, timedelta

from portaria import servicos
from portaria.db import conectar, preparar_banco
from portaria.erros import RegraNegocioErro


PRIMEIROS = [
    "Ana",
    "Bruno",
    "Carla",
    "Davi",
    "Elisa",
    "Fábio",
    "Gabriel",
    "Joana",
    "João",
    "Luana",
    "Marcos",
    "Nina",
    "Otávio",
]

SOBRENOMES = [
    "Lima",
    "Sousa",
    "Nunes",
    "Rocha",
    "Prado",
    "Melo",
    "Torres",
    "Alves",
    "Campos",
    "Reis",
]


def gerar_cpf(rng):
    digitos = [
        rng.randint(0, 9)
        for _ in range(9)
    ]

    for posicao in (9, 10):
        soma = sum(
            digitos[i] * (posicao + 1 - i)
            for i in range(posicao)
        )

        digitos.append(
            (soma * 10) % 11 % 10
        )

    return "".join(
        map(str, digitos)
    )


def formatar(momento):
    return momento.isoformat(
        sep=" ",
        timespec="seconds",
    )


def popular(
    conn,
    visitantes=10,
    dias=5,
    semente=None,
):
    rng = random.Random(semente)

    cpfs = []

    for _ in range(visitantes):
        nome = (
            f"{rng.choice(PRIMEIROS)} "
            f"{rng.choice(SOBRENOMES)}"
        )

        cpf = gerar_cpf(rng)

        try:
            servicos.cadastrar_visitante(
                conn,
                nome,
                cpf,
            )
        except RegraNegocioErro:
            # CPF repetido ou cadastro já existente.
            pass

        cpfs.append(cpf)

    setores = [
        linha["id"]
        for linha in conn.execute(
            """
            SELECT id
            FROM setor
            WHERE ativo = 1
            """
        ).fetchall()
    ]

    if not setores:
        print(
            "Nenhum setor ativo encontrado. "
            "Cadastre um setor antes de gerar os dados."
        )
        return 0

    hoje = datetime.now().replace(
        hour=8,
        minute=0,
        second=0,
        microsecond=0,
    )

    criadas = 0

    for dia in range(dias, 0, -1):
        quantidade = min(
            4,
            len(cpfs),
        )

        for cpf in rng.sample(
            cpfs,
            quantidade,
        ):
            entrada = (
                hoje
                - timedelta(days=dia)
                + timedelta(
                    minutes=rng.randint(0, 480)
                )
            )

            saida = entrada + timedelta(
                minutes=rng.randint(10, 120)
            )

            try:
                visita_id = servicos.registrar_entrada(
                    conn,
                    cpf,
                    rng.choice(setores),
                    momento=formatar(entrada),
                )

                servicos.registrar_saida(
                    conn,
                    visita_id,
                    momento=formatar(saida),
                )

                criadas += 1

            except RegraNegocioErro:
                # Lotação ou visitante já presente.
                # A regra da aplicação decide se permite.
                pass

    return criadas


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Gera dados fictícios para a "
            "Portaria Digital."
        )
    )

    parser.add_argument(
        "--visitantes",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--dias",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--semente",
        type=int,
        default=None,
        help=(
            "A mesma semente gera os mesmos dados."
        ),
    )

    parser.add_argument(
        "--banco",
        default="portaria.db",
        help=(
            "Arquivo SQLite de laboratório. "
            "Padrão: portaria.db"
        ),
    )

    args = parser.parse_args()

    conn = conectar(args.banco)

    try:
        preparar_banco(conn)

        criadas = popular(
            conn,
            args.visitantes,
            args.dias,
            args.semente,
        )

    finally:
        conn.close()

    print(
        f"{criadas} visita(s) fictícia(s) "
        f"gravada(s) em {args.banco}"
    )


if __name__ == "__main__":
    main()