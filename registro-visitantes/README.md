"# UC05-Desenvolvimento-Descktop" 

# Registro de Visitantes

Aplicação desktop desenvolvida em Python com PySide6 para registrar visitantes e seus respectivos setores de destino.

## Pré-requisitos

- Python 3.14.6
- pip
- Git

## Tecnologias utilizadas

- Python 3.14.6
- PySide6 6.12.0

## Como executar o projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/nureyevDev/UC05-Desenvolvimento-Descktop.git
cd UC05-Desenvolvimento-Desktop
```

### 2. Criar o ambiente virtual

```bash
python -m venv .venv
```

### 3. Ativar o ambiente virtual

No PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

No Prompt de Comando:

```cmd
.venv\Scripts\activate.bat
```

### 4. Instalar as dependências

```bash
python -m pip install -r requirements.txt
```

### 5. Executar a aplicação

```bash
python main.py
```

## Funcionalidades

- Registro do nome do visitante;
- Seleção do setor de destino;
- Validação de nome vazio ou formado apenas por espaços;
- Validação da seleção do setor;
- Exibição dos visitantes registrados;
- Contador de visitas durante a sessão;
- Limpeza dos campos sem remover os registros.

## Limitação atual

Os registros ficam armazenados somente na memória durante a execução. Ao fechar ou reiniciar a aplicação, a lista de visitantes e o contador retornam ao estado inicial. O projeto ainda não utiliza banco de dados ou arquivo para armazenamento permanente.

## Estrutura do projeto

```text
UC05-Desenvolvimento-Desktop/
├── views/
│   ├── __init__.py
│   └── janela_principal.py
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
```

## Observação

A pasta `.venv` não deve ser enviada ao repositório. Cada pessoa deve criar o próprio ambiente virtual e instalar as dependências registradas no `requirements.txt`.