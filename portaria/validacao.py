import re


def normalizar_nome(nome: str | None) -> str:
    return " ".join((nome or "").split())


def normalizar_documento(valor: str | None) -> str:
    return re.sub(r"\D", "", valor or "")


def cpf_valido(valor: str | None) -> bool:
    
    d = normalizar_documento(valor)
    if len(d) != 11 or d == d[0] * 11:
        return False
    for posicao in (9, 10):
        soma = sum(int(d[i]) * (posicao + 1 - i) for i in range(posicao))
        digito = (soma * 10) % 11 % 10
        if digito != int(d[posicao]):
            return False
    return True


def mascarar_documento(valor: str | None) -> str:
    d = normalizar_documento(valor)
    if len(d) != 11:
        return "***"
    return f"***.{d[3:6]}.{d[6:9]}-**"