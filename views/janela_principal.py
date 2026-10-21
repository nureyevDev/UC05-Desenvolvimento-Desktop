from typing import Any
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QLabel, QLineEdit, 
    QListWidget, QPushButton, QVBoxLayout, QWidget 
)


class JanelaPrincipal(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Registro de Visitantes")
        self.resize(520, 460)
        self.registros: list[Any] = []

        self.titulo = QLabel("Registro de Visitantes")
        self.campo_nome = QLineEdit()
        self.campo_nome.setPlaceholderText("Nome Completo")
        self.combo_destino = QComboBox() 
        self.combo_destino.addItems([
            "Selecione um Setor", "Secretaria", "Coordenação", "Laboratório",   
        ])
        self.botao_cadastrar = QPushButton("Registtrar Visita")
        self.botao_limpar = QPushButton("Limpar Campos")
        self.mensagem = QLabel("Preencha os Campos.")
        self.lista = QListWidget()
        self.contador = QLabel("Visitas nesta sessão: 0")
        
        formulario = QFormLayout()
        formulario.addRow("Nome:", self.campo_nome)
        formulario.addRow("Destino:", self.combo_destino)
        layout = QVBoxLayout()
        
        for widget in (self.titulo, self.botao_cadastrar,
                       self.botao_limpar, self.mensagem):
            if widget is self.botao_cadastrar:
                layout.addLayout(formulario)
            layout.addWidget(widget)
            
        layout.addWidget(QLabel("Visitantes Registrados:"))
        layout.addWidget(self.lista)
        layout.addWidget(self.contador)
        self.setLayout(layout)        
