from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class JanelaPrincipal(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Registro de Visitantes")
        self.resize(520, 460)

        self.registros = []

        self.titulo = QLabel("Registro de Visitantes")

        self.campo_nome = QLineEdit()
        self.campo_nome.setPlaceholderText("Nome completo")

        self.combo_destino = QComboBox()
        self.combo_destino.addItems(
            [
                "Selecione um setor",
                "Secretaria",
                "Coordenação",
                "Laboratório",
            ]
        )

        self.botao_cadastrar = QPushButton("Registrar visita")
        self.botao_limpar = QPushButton("Limpar campos")

        self.mensagem = QLabel("Preencha os campos.")
        self.lista = QListWidget()
        self.contador = QLabel("Visitas nesta sessão: 0")

        formulario = QFormLayout()
        formulario.addRow("Nome:", self.campo_nome)
        formulario.addRow("Destino:", self.combo_destino)

        layout = QVBoxLayout()

        layout.addWidget(self.titulo)
        layout.addLayout(formulario)
        layout.addWidget(self.botao_cadastrar)
        layout.addWidget(self.botao_limpar)
        layout.addWidget(self.mensagem)
        layout.addWidget(QLabel("Visitantes registrados:"))
        layout.addWidget(self.lista)
        layout.addWidget(self.contador)

        self.setLayout(layout)

        self.botao_cadastrar.clicked.connect(self.registrar_visita)
        self.botao_limpar.clicked.connect(self.limpar_campos)

    def registrar_visita(self):
        nome = self.campo_nome.text()
        destino = self.combo_destino.currentText()

        registro = {
            "nome": nome,
            "destino": destino,
        }

        self.registros.append(registro)
        self.lista.addItem(f"{nome} → {destino}")

        self.contador.setText(
            f"Visitas nesta sessão: {len(self.registros)}"
        )

        self.mensagem.setText(
            "Registro adicionado (ainda sem validação)."
        )

        self.limpar_campos()

    def limpar_campos(self):
        self.campo_nome.clear()
        self.combo_destino.setCurrentIndex(0)
        self.campo_nome.setFocus()