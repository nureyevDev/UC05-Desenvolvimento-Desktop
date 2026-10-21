"# UC05-Desenvolvimento-Descktop" 

1 - ETAPA 00:
Hipótese: Um visitante que informar o nome, mas não selecionar um setor, não deve ser registrado, porque o cadastro fica incompleto e não identifica o destino da visita.

Teste: Informei um nome no campo correspondente, mantive a opção padrão do setor sem selecionar um setor válido e tentei realizar o cadastro.

Resultado: O visitante não foi adicionado à lista, a contagem permaneceu sem alteração e a aplicação indicou que era necessário selecionar um setor.

2 = ETAPA 01:
O VS Code é a IDE utilizada para editar, executar e depurar o código. O interpretador Python executa as instruções do programa. O PySide6 fornece os componentes gráficos, como janela, botão e campos. O QApplication inicia e mantém o loop de eventos, que recebe ações do usuário. O caminho do clique ocorre assim: main.py → QApplication → janela e widgets → clique no botão → sinal clicked → método conectado → atualização da interface. Portanto, se a janela abre e somente o botão não funciona, o Python não necessariamente falhou. O erro provavelmente está na conexão do evento ou no método executado.

3 - ETAPA 02:
A evidência de que o PySide6 está no interpretador correto é que tanto o executável do Python quanto o local de instalação da biblioteca apontam para a .venv do projeto. Isso confirma que as dependências estão isoladas da instalação global do Python e que o ambiente pode ser recriado usando o requirements.txt.

4 - ETAPA 03:
A estrutura separa corretamente as responsabilidades. O main.py não precisa conhecer todos os detalhes dos widgets porque sua função é iniciar o QApplication, criar a janela principal e manter o loop de eventos. A criação e a configuração dos widgets ficam em views/janela_principal.py. Essa separação deixa o código mais organizado, facilita a manutenção e evita concentrar toda a aplicação em um único arquivo.

5 - ETAPA 04:
A herança de QWidget permite que JanelaPrincipal utilize recursos de uma janela, como setWindowTitle(), resize() e setLayout(). O self representa a instância atual da janela e permite acessar e modificar seus atributos e métodos. Já super().__init__() inicializa corretamente a classe QWidget da qual JanelaPrincipal herda. Dessa forma, a classe personalizada funciona como uma janela do PySide6 e pode receber widgets, layouts e outras configurações.

6 - ETAPA 05:
A apresentação corresponde à criação e à organização visual dos widgets, como QLineEdit, QComboBox, QPushButton, QLabel e QListWidget, utilizando layouts como QFormLayout e QVBoxLayout. O comportamento corresponde às ações executadas em resposta aos eventos. Para o botão funcionar, o sinal clicked precisa ser conectado a um método, por exemplo, self.botao_cadastrar.clicked.connect(self.cadastrar_visita). Portanto, criar o botão define sua aparência, mas conectar o evento define sua funcionalidade.

7 - ETAPA 06:
Não usamos parênteses em connect(self.registrar_visita) porque precisamos passar uma referência ao método, permitindo que o PySide6 execute o método apenas quando o sinal clicked ocorrer. Se escrevêssemos connect(self.registrar_visita()), o método seria executado imediatamente durante a criação da janela, e o valor retornado seria enviado ao connect. A conexão entre sinal e método é o que determina o comportamento de cada botão.

8 - ETAPA 07:
A QListWidget representa visualmente os visitantes, enquanto self.registros mantém os dados usados pela lógica do programa. Se apenas a lista visual fosse atualizada, a interface e os dados internos ficariam inconsistentes. Outras funcionalidades baseadas em self.registros, como contagem, consulta ou salvamento futuro, não reconheceriam o item mostrado na tela. Portanto, cada cadastro deve primeiro ser incluído em self.registros e depois apresentado na lista visual.

9 - ETAPA = 08
