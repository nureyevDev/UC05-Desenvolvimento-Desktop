from datetime import datetime

from portaria import repositorio as repo
import sqlite3

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QMessageBox, 
)


COLUNAS = ["Visita", "Nome", "CPF", "Setor", "Crachá", "Entrada"]
def agora():
    return datetime.now().isoformat(sep=" ", timespec="seconds")


from portaria.validacao import cpf_valido, mascarar_documento, normalizar_documento


class JanelaPrincipal(QWidget):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn

        self.resize(820, 520)

        
        self.campo_cpf = QLineEdit()
        self.campo_cpf.setPlaceholderText("Somente números")
        self.campo_cpf.setMaxLength(14)
        self.campo_nome = QLineEdit()
        self.combo_setor = QComboBox()
        self.botao_entrada = QPushButton("Registrar entrada")
        self.botao_limpar = QPushButton("Limpar campos")
        self.mensagem = QLabel("Informe o CPF do visitante.")

        formulario = QFormLayout()
        formulario.addRow("CPF:", self.campo_cpf)
        formulario.addRow("Nome:", self.campo_nome)
        formulario.addRow("Setor:", self.combo_setor)

        botoes = QHBoxLayout()
        botoes.addWidget(self.botao_entrada)
        botoes.addWidget(self.botao_limpar)

       
        self.campo_filtro = QLineEdit()
        self.campo_filtro.setPlaceholderText("Filtrar por nome ou setor")
        self.tabela = QTableWidget(0, len(COLUNAS))
        self.tabela.setHorizontalHeaderLabels(COLUNAS)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.verticalHeader().setVisible(False)
        self.botao_saida = QPushButton("Registrar saída da visita selecionada")
        self.contador = QLabel()

        layout = QVBoxLayout()
        layout.addLayout(formulario)
        layout.addLayout(botoes)
        layout.addWidget(self.mensagem)
        layout.addWidget(QLabel("No prédio agora:"))
        layout.addWidget(self.campo_filtro)
        layout.addWidget(self.tabela)
        layout.addWidget(self.botao_saida)
        layout.addWidget(self.contador)
        self.setLayout(layout)

       
        self.campo_cpf.editingFinished.connect(self.buscar_visitante)
        self.botao_entrada.clicked.connect(self.registrar_entrada)
        self.botao_limpar.clicked.connect(self.limpar_campos)
        self.botao_saida.clicked.connect(self.registrar_saida)
        self.campo_filtro.textChanged.connect(self.atualizar_tabela)

        self.carregar_setores()
        self.atualizar_tabela()

    def carregar_setores(self):
        self.combo_setor.clear()
        self.combo_setor.addItem(
            "Selecione um setor",
            None,
        )

        setores = repo.listar_setores_ativos(self.conn)

        for setor in setores:
            self.combo_setor.addItem(
                setor["nome"],
                setor["id"],
            )

    def buscar_visitante(self):
        cpf = normalizar_documento(self.campo_cpf.text())
        visitante = repo.buscar_visitante_por_documento(self.conn, cpf)
        if visitante:
            self.campo_nome.setText(visitante["nome"])
            self.campo_nome.setReadOnly(True)
            self.mensagem.setText("Visitante já cadastrado. Escolha o setor.")
        else:
            self.campo_nome.setReadOnly(False)


    def registrar_entrada(self):
        cpf = normalizar_documento(
            self.campo_cpf.text()
        )

        nome = " ".join(
            self.campo_nome.text().split()
        )

        setor_id = self.combo_setor.currentData()

        if not cpf_valido(cpf):
            self.mensagem.setText(
                "CPF inválido. Confira os 11 dígitos."
            )
            self.campo_cpf.setFocus()
            return

        if not nome:
            self.mensagem.setText(
                "Informe o nome do visitante."
            )
            self.campo_nome.setFocus()
            return

        if setor_id is None:
            self.mensagem.setText(
                "Selecione o setor de destino."
            )
            self.combo_setor.setFocus()
            return

        try:
            with self.conn:
                visitante = (
                    repo.buscar_visitante_por_documento(
                        self.conn,
                        cpf,
                    )
                )

                if visitante is None:
                    visitante_id = repo.inserir_visitante(
                        self.conn,
                        nome,
                        cpf,
                    )
                else:
                    visitante_id = visitante["id"]
                    nome = visitante["nome"]

                visita_aberta = repo.buscar_visita_aberta(
                    self.conn,
                    visitante_id,
                )

                if visita_aberta:
                    raise ValueError(
                        f"{nome} já está no prédio. "
                        "Registre a saída antes."
                    )

                setor = repo.obter_setor(
                    self.conn,
                    setor_id,
                )

                quantidade_presentes = (
                    repo.contar_presentes_no_setor(
                        self.conn,
                        setor_id,
                    )
                )

                if (
                    setor["lotacao_maxima"] is not None
                    and quantidade_presentes
                    >= setor["lotacao_maxima"]
                ):
                    raise ValueError(
                        "O setor atingiu a lotação máxima."
                    )

                cracha = repo.buscar_cracha_disponivel(
                    self.conn
                )

                if cracha is None:
                    raise ValueError(
                        "Não há crachá disponível. "
                        "Aguarde uma devolução."
                    )

                repo.inserir_visita(
                    self.conn,
                    visitante_id,
                    setor_id,
                    cracha["id"],
                    agora(),
                )

                repo.atualizar_situacao_cracha(
                    self.conn,
                    cracha["id"],
                    "em_uso",
                )

        except (sqlite3.Error, ValueError) as erro:
            QMessageBox.warning(
                self,
                "Não foi possível registrar",
                str(erro),
            )
            return

        self.limpar_campos()

        self.mensagem.setText(
            f"Entrada registrada. Entregue o "
            f"crachá {cracha['codigo']}."
        )

        self.atualizar_tabela()

    def registrar_saida(self):
        linha = self.tabela.currentRow()

        if linha < 0:
            self.mensagem.setText(
                "Selecione uma visita na tabela."
            )
            return

        visita_id = int(
            self.tabela.item(linha, 0).text()
        )

        try:
            with self.conn:
                visita = repo.buscar_visita_aberta_por_id(
                    self.conn,
                    visita_id,
                )

                if visita is None:
                    raise ValueError(
                        "A visita selecionada não está aberta."
                    )

                repo.registrar_saida_visita(
                    self.conn,
                    visita_id,
                    agora(),
                )

                repo.atualizar_situacao_cracha(
                    self.conn,
                    visita["cracha_id"],
                    "disponivel",
                )

        except (sqlite3.Error, ValueError) as erro:
            QMessageBox.warning(
                self,
                "Não foi possível registrar a saída",
                str(erro),
            )
            return

        self.mensagem.setText(
            f"Saída registrada. Crachá "
            f"{visita['codigo']} devolvido."
        )

        self.atualizar_tabela()
        
        
    def atualizar_tabela(self):
        filtro = self.campo_filtro.text().strip()

        linhas = repo.listar_presentes(
            self.conn,
            filtro,
        )

        self.tabela.setRowCount(len(linhas))

        for i, linha in enumerate(linhas):
            valores = [
                linha["id"],
                linha["nome"],
                mascarar_documento(linha["cpf"]),
                linha["setor"],
                linha["cracha"],
                linha["entrada"],
            ]

            for j, valor in enumerate(valores):
                self.tabela.setItem(
                    i,
                    j,
                    QTableWidgetItem(str(valor)),
                )

        self.tabela.setCurrentCell(-1, -1)

        quantidade_livres = (
            repo.contar_crachas_disponiveis(
                self.conn
            )
        )

        self.contador.setText(
            f"No prédio: {len(linhas)} | "
            f"Crachás livres: {quantidade_livres}"
        )

    def limpar_campos(self):
        self.campo_cpf.clear()
        self.campo_nome.clear()
        self.campo_nome.setReadOnly(False)
        self.combo_setor.setCurrentIndex(0)
        self.mensagem.setText(
            "Informe o CPF do visitante."
        )
        self.campo_cpf.setFocus()