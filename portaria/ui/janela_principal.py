import sqlite3


from portaria import repositorio as repo
from portaria import servicos
from portaria.erros import RegraNegocioErro
from portaria.validacao import (
    mascarar_documento,
    normalizar_documento,
)

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

        self.atualizar_tudo()
        
    def atualizar_tudo(self):
        self.carregar_setores()
        self.atualizar_tabela()

    
    def buscar_visitante(self):
        cpf = normalizar_documento(self.campo_cpf.text())
        visitante = repo.buscar_visitante_por_documento(self.conn, cpf)
        if visitante:
            self.campo_nome.setText(visitante["nome"])
            self.campo_nome.setReadOnly(True)
            self.mensagem.setText("Visitante já cadastrado. Escolha o setor.")
        else:
            self.campo_nome.setReadOnly(False)


    def carregar_setores(self):
        """Mostra a ocupação atual de cada setor."""
        selecionado = self.combo_setor.currentData()

        self.combo_setor.clear()
        self.combo_setor.addItem(
            "Selecione um setor",
            None,
        )

        for setor in repo.listar_setores_ativos(self.conn):
            ocupacao = repo.contar_presentes_no_setor(
                self.conn,
                setor["id"],
            )

            self.combo_setor.addItem(
                f"{setor['nome']} "
                f"({ocupacao}/{setor['lotacao_maxima']})",
                setor["id"],
            )

        indice = self.combo_setor.findData(selecionado)

        self.combo_setor.setCurrentIndex(
            max(indice, 0)
        )
        
    def registrar_entrada(self):
        documento = self.campo_cpf.text()
        setor_id = self.combo_setor.currentData()

        if setor_id is None:
            self.mensagem.setText(
                "Selecione o setor de destino."
            )
            return

        try:
            cpf = normalizar_documento(documento)

            visitante = repo.buscar_visitante_por_documento(
                self.conn,
                cpf,
            )

            if visitante is None:
                servicos.cadastrar_visitante(
                    self.conn,
                    self.campo_nome.text(),
                    documento,
                )

            servicos.registrar_entrada(
                self.conn,
                documento,
                setor_id,
            )

        except RegraNegocioErro as erro:
            self.mensagem.setText(str(erro))
            return

        except sqlite3.Error as erro:
            QMessageBox.critical(
                self,
                "Portaria Digital",
                f"Erro no banco: {erro}",
            )
            return

        self.limpar_campos()

        self.mensagem.setText(
            "Entrada registrada. "
            "Entregue o crachá indicado na tabela."
        )

        self.atualizar_tudo()

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
            servicos.registrar_saida(
                self.conn,
                visita_id,
            )

        except RegraNegocioErro as erro:
            self.mensagem.setText(str(erro))
            return

        except sqlite3.Error as erro:
            QMessageBox.critical(
                self,
                "Portaria Digital",
                f"Erro no banco: {erro}",
            )
            return

        self.mensagem.setText(
            "Saída registrada. Crachá devolvido."
        )

        self.atualizar_tudo()

    def atualizar_tudo(self):
        self.carregar_setores()
        self.atualizar_tabela()

    def atualizar_tabela(self):
        presentes = repo.listar_presentes(self.conn)
        termo = self.campo_filtro.text().strip().lower()

        linhas = [
            linha
            for linha in presentes
            if termo
            in f"{linha['nome']} {linha['setor']}".lower()
        ]

        self.tabela.setRowCount(len(linhas))

        for i, linha in enumerate(linhas):
            valores = [
                linha["id"],
                linha["nome"],
                mascarar_documento(
                    linha["documento"]
                ),
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

        crachas = repo.contar_crachas_por_situacao(
            self.conn
        )

        self.contador.setText(
            f"No prédio: {len(presentes)} | "
            f"Crachás livres: "
            f"{crachas.get('disponivel', 0)}"
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