# 🧪 Simulador de Controle de Concorrência com Deadlock

## 🎯 Objetivo

Este projeto é um simulador que demonstra a interação de transações concorrentes competindo por **recursos compartilhados**, utilizando **multithreading** em Python. O foco é ilustrar cenários de **deadlock** e implementar estratégias para:

- **Detectar deadlocks automaticamente** por meio de um **grafo de espera**;
- **Aplicar políticas de controle de concorrência**, como **WAIT-DIE**;
- **Resolver dinamicamente deadlocks** para garantir a continuidade da execução.

---

## 🧱 Arquitetura do Projeto

O projeto é composto por diversas classes que representam os principais componentes da simulação:

### 1. `AbortException` (`src/exceptions/abort_exeception.py`)
Exceção personalizada que representa a interrupção forçada de uma transação, geralmente provocada pela política WAIT-DIE ou outros conflitos.

### 2. `TransacaoInfo` (`src/models/transacao_info.py`)
Modelo de metadados para uma transação, contendo:
- Identificador único da transação (**tid**);
- Timestamp lógico que define a ordem de execução (**timestamp**).

### 3. `Recurso` (`src/models/recurso.py`)
Modelo que representa um recurso compartilhado. Cada recurso possui:
- Identificador único (**item_id**);
- Mecanismos de bloqueio e fila de espera para controle de concorrência;
- Métodos como `acquire`, `release` e `wait_for_release` para sincronização.

Utiliza `threading.Lock` e `threading.Condition` para controle de acesso.

### 4. `Transacao` (`src/models/transacao.py`)
Classe que gerencia o ciclo de vida de uma transação, incluindo:
- Bloqueio e liberação de recursos;
- Detecção e resolução de deadlocks via política **WAIT-DIE**;
- Geração de logs detalhados da execução.

Cada transação é executada como uma thread independente.

### 5. `Grafo de Espera` (`src/visualization/grafo_visualizador.py`)
Criado com `networkx` e exibido com `matplotlib`, este grafo:
- Representa dependências entre transações (arestas);
- Detecta ciclos (indicadores de deadlock);
- Exibe visualmente o estado do sistema em tempo real.

### 6. Utilitários (`src/utils/`)
- `logging.py`: Fornece funções de log com cores e formatação para facilitar o monitoramento.
- `control_time.py`: Funções auxiliares para simular tempos de espera e atrasos.

---

## 🧠 Funcionalidades

- Suporte à execução de **transações concorrentes** com threads.
- Implementação da política **WAIT-DIE** para prevenção/resolução de deadlocks.
- Visualização gráfica interativa do **grafo de dependência**.
- Logs coloridos e detalhados para acompanhamento em tempo real.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.12+**
- `networkx`, `matplotlib` – visualização e análise do grafo de espera
- `colorama` – logs com cores no terminal

---

## 📁 Estrutura do Projeto

```
concurrent_transactions_simulator/
├── .venv/                   # Ambiente virtual (opcional)
├── src/                     # Código-fonte
│   ├── exceptions/
│   │   └── abort_exeception.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── recurso.py
│   │   ├── transacao.py
│   │   └── transacao_info.py
│   ├── utils/
│   │   ├── control_time.py
│   │   └── logging.py
│   ├── visualization/
│   │   └── grafo_visualizador.py
│   └── __init__.py
├── main.py                  # Arquivo principal
├── README.md                # Este arquivo
├── pyproject.toml           # Configuração do projeto
├── .gitignore               # Arquivos ignorados pelo Git
├── .python-version          # Versão especificada do Python
├── uv.lock                  # Dependências travadas (opcional)
```

---

## 📦 Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/SeuUsuario/concurrent-transactions-simulator
   cd concurrent-transactions-simulator
   ```

2. Verifique a versão do Python (**3.12+**):
   ```bash
   python --version
   ```

3. Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Linux/macOS
   .venv\Scripts\activate       # Windows
   ```

4. Instale as dependências:
   ```bash
   pip install .
   ```

5. Execute o simulador:
   ```bash
   python main.py
   ```

---

## 📊 Monitoramento

### Logs no console
O sistema exibe logs em tempo real sobre:
- Início e fim de transações;
- Operações de bloqueio e liberação de recursos;
- Detecção e resolução de deadlocks.

### Visualização gráfica
Um **grafo interativo** é atualizado dinamicamente, facilitando a visualização de dependências e ciclos de deadlock.

---
