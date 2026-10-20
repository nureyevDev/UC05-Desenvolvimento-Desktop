from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class JanelaPrincipal(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Registro de Visitantes")
        self.resize(500, 300)

        titulo = QLabel("Registro de Visitantes")

        layout = QVBoxLayout()
        layout.addWidget(titulo)

        self.setLayout(layout)
        
