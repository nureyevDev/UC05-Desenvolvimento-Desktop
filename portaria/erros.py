class RegraNegocioErro(Exception):
    """Erro previsto do usuário ou do processo.

    A mensagem é exibida na interface. Erros de programação e de banco
    NÃO usam esta classe.
    """
    pass