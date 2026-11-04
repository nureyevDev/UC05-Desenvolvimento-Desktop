import logging
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
    QDateEdit,
    QMainWindow,
    QTabWidget, 
)

log = logging.getLogger(__name__)
FALHA = object()

from PySide6.QtCore import QDate

COLUNAS = ["Visita", "Nome", "CPF", "Setor", "Crachá", "Entrada"]

COLUNAS_HISTORICO = ["Visita", "Nome", "CPF", "Setor", "Crachá", "Entrada", "Saída", "Min."]


def nova_tabela(colunas):
    tabela = QTableWidget(0, len(colunas))
    tabela.setHorizontalHeaderLabels(colunas)
    tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
    tabela.setSelectionMode(QAbstractItemView.SingleSelection)
    tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tabela.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
    tabela.verticalHeader().setVisible(False)
    return tabela


def preencher_tabela(tabela, linhas):
    tabela.setRowCount(len(linhas))
    for i, valores in enumerate(linhas):
        for j, valor in enumerate(valores):
            tabela.setItem(i, j, QTableWidgetItem("" if valor is None else str(valor)))
    tabela.setCurrentCell(-1, -1)


class JanelaPrincipal(QMainWindow):
    def __init__(self, conn):
        super().__init__()

        self.conn = conn

        self.setWindowTitle("Portaria Digital")
        self.resize(900, 560)

        abas = QTabWidget()

        abas.addTab(
            self.montar_aba_portaria(),
            "&Portaria",
        )

        abas.addTab(
            self.montar_aba_historico(),
            "&Histórico",
        )

        abas.currentChanged.connect(
            self.atualizar_tudo
        )

        self.setCentralWidget(abas)

        self.atualizar_tudo()
        
    def montar_aba_portaria(self):
        aba = QWidget()

        self.campo_cpf = QLineEdit()
        self.campo_cpf.setPlaceholderText(
            "Somente números"
        )
        self.campo_cpf.setMaxLength(14)

        self.campo_nome = QLineEdit()
        self.combo_setor = QComboBox()

        self.botao_entrada = QPushButton(
            "Registrar entrada"
        )
        self.botao_limpar = QPushButton(
            "Limpar campos"
        )

        self.mensagem = QLabel(
            "Informe o CPF do visitante."
        )

        formulario = QFormLayout()
        formulario.addRow("CPF:", self.campo_cpf)
        formulario.addRow("Nome:", self.campo_nome)
        formulario.addRow("Setor:", self.combo_setor)

        botoes = QHBoxLayout()
        botoes.addWidget(self.botao_entrada)
        botoes.addWidget(self.botao_limpar)

        self.campo_filtro = QLineEdit()
        self.campo_filtro.setPlaceholderText(
            "Filtrar por nome ou setor"
        )

        self.tabela = nova_tabela(COLUNAS)

        self.botao_saida = QPushButton(
            "Registrar saída da visita selecionada"
        )

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

        aba.setLayout(layout)

        self.campo_cpf.editingFinished.connect(
            self.buscar_visitante
        )
        self.botao_entrada.clicked.connect(
            self.registrar_entrada
        )
        self.botao_limpar.clicked.connect(
            self.limpar_campos
        )
        self.botao_saida.clicked.connect(
            self.registrar_saida
        )
        self.campo_filtro.textChanged.connect(
            self.atualizar_tabela
        )

        return aba
        
    def atualizar_tudo(self, indice=None):
        self.carregar_setores()
        self.atualizar_tabela()

    
    def buscar_visitante(self):
        cpf = normalizar_documento(
            self.campo_cpf.text()
        )

        visitante = self._executar(
            repo.buscar_visitante_por_documento,
            self.conn,
            cpf,
        )

        if visitante is FALHA:
            return

        if visitante:
            self.campo_nome.setText(
                visitante["nome"]
            )
            self.campo_nome.setReadOnly(True)
            self.mensagem.setText(
                "Visitante já cadastrado. Escolha o setor."
            )
        else:
            self.campo_nome.clear()
            self.campo_nome.setReadOnly(False)


    def carregar_setores(self):
        setores = self._executar(
            repo.listar_setores_ativos,
            self.conn,
        )

        if setores is FALHA:
            return

        selecionado = self.combo_setor.currentData()

        self.combo_setor.clear()
        self.combo_setor.addItem(
            "Selecione um setor",
            None,
        )

        for setor in setores:
            ocupacao = self._executar(
                repo.contar_presentes_no_setor,
                self.conn,
                setor["id"],
            )

            if ocupacao is FALHA:
                return

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
            self._avisar(
                "Selecione o setor de destino."
            )
            return

        def operacao():
            return servicos.registrar_entrada(
                self.conn,
                documento,
                setor_id,
                nome=self.campo_nome.text(),
            )

        if self._executar(operacao) is FALHA:
            self.mensagem.setText(
                "Entrada não registrada. "
                "Corrija os dados e tente novamente."
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
            self._avisar(
                "Selecione uma visita na tabela."
            )
            return

        visita_id = int(
            self.tabela.item(linha, 0).text()
        )

        if self._executar(
            servicos.registrar_saida,
            self.conn,
            visita_id,
        ) is FALHA:
            return

        self.mensagem.setText(
            "Saída registrada. Crachá devolvido."
        )

        self.atualizar_tudo()
        
        
    def montar_aba_historico(self):
        hoje = QDate.currentDate()

        self.data_inicio = QDateEdit(
            hoje.addDays(-7)
        )
        self.data_fim = QDateEdit(hoje)

        for campo in (
            self.data_inicio,
            self.data_fim,
        ):
            campo.setCalendarPopup(True)
            campo.setDisplayFormat("dd/MM/yyyy")

        self.campo_busca = QLineEdit()
        self.campo_busca.setPlaceholderText(
            "Nome ou setor"
        )

        botao_filtrar = QPushButton("&Filtrar")

        self.tabela_historico = nova_tabela(
            COLUNAS_HISTORICO
        )

        self.resumo = QLabel()
        self.resumo.setWordWrap(True)

        botao_filtrar.clicked.connect(
            self.atualizar_historico
        )
        self.campo_busca.returnPressed.connect(
            self.atualizar_historico
        )

        filtros = QHBoxLayout()
        filtros.addWidget(QLabel("De:"))
        filtros.addWidget(self.data_inicio)
        filtros.addWidget(QLabel("Até:"))
        filtros.addWidget(self.data_fim)
        filtros.addWidget(self.campo_busca, 1)
        filtros.addWidget(botao_filtrar)

        layout = QVBoxLayout()
        layout.addLayout(filtros)
        layout.addWidget(self.tabela_historico)
        layout.addWidget(self.resumo)

        aba = QWidget()
        aba.setLayout(layout)

        return aba

    def atualizar_tudo(self):
        self.carregar_setores()
        self.atualizar_tabela()
        self.atualizar_historico()

    def atualizar_tabela(self):
        presentes = self._executar(
            repo.listar_presentes,
            self.conn,
        )

        if presentes is FALHA:
            return

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

        crachas = self._executar(
            repo.contar_crachas_por_situacao,
            self.conn,
        )

        if crachas is FALHA:
            return

        self.contador.setText(
            f"No prédio: {len(presentes)} | "
            f"Crachás livres: "
            f"{crachas.get('disponivel', 0)}"
        )

    def atualizar_historico(self):
        inicio = self.data_inicio.date().toString(
            "yyyy-MM-dd"
        )
        fim = self.data_fim.date().toString(
            "yyyy-MM-dd"
        )

        linhas = self._executar(
            repo.listar_historico,
            self.conn,
            inicio,
            fim,
            self.campo_busca.text(),
        )

        if linhas is FALHA:
            return

        self.tabela_historico.setRowCount(len(linhas))

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
                linha["saida"] or "Em andamento",
                linha["minutos"] or "",
            ]

            for j, valor in enumerate(valores):
                self.tabela_historico.setItem(
                    i,
                    j,
                    QTableWidgetItem(str(valor)),
                )

        self.tabela_historico.setCurrentCell(-1, -1)

        self.resumo.setText(
            f"Registros encontrados: {len(linhas)}"
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
        
    def _executar(self, funcao, *args):
        """Ponto único de tratamento de exceções da interface.

        Erro de regra: mensagem clara para o operador.
        Erro de banco: registro técnico no log e aviso genérico, sem expor
        detalhes internos nem dados pessoais.
        """
        try:
            return funcao(*args)
        except RegraNegocioError as erro:
            self._avisar(str(erro))
        except sqlite3.Error:
            log.exception("Falha de banco em %s", getattr(funcao, "__name__", "operação"))
            QMessageBox.critical(
                self, "Portaria Digital",
                "Não foi possível acessar o banco de dados. Nenhuma alteração "
                "parcial foi gravada. Tente novamente ou avise o suporte.",
            )
        return FALHA

    def _avisar(self, texto):
        self.statusBar().showMessage(texto, 8000)  # some depois de 8 segundos
        QMessageBox.warning(self, "Portaria Digital", texto)