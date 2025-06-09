# Simulador de Controle de Concorrência com Deadlock

## 🎯 Objetivo

Este projeto simula a execução de transações concorrentes que competem por recursos compartilhados (`X` e `Y`) utilizando `threads` em Python. As funcionalidades principais incluem:

- Controle de acesso concorrente com bloqueios (locks).
- Simulação de cenários de deadlock entre transações.
- Detecção automática de deadlocks com análise de grafos.
- Resolução de deadlocks com a aplicação dinâmica da política `wait-die`.
- Logs detalhados para monitorar acesso a recursos, resolução de deadlocks e outros eventos.

---

## 🧠 Funcionalidades
- Suporte a múltiplas transações concorrentes gerenciadas por threads.
- Ciclo de acesso aleatório aos recursos compartilhados.
- Implementação de políticas de bloqueio e fila de espera para recursos.
- Mecanismo eficiente de detecção e resolução de deadlocks.
- Integração de gráficos ao vivo para visualizar o estado do grafo de espera.

---

## 🛠️ Tecnologias Utilizadas
- **Python 3.12+**
- `threading` para gerenciar transações concorrentes.
- `networkx` para representar e analisar o grafo de espera.
- `matplotlib` para visualização do grafo em tempo real.
- `colorama` para logs coloridos em diferentes níveis.

---

## 📦 Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/SeuUsuario/concurrent-transactions-simulator
   cd concurrent-transactions-simulator
   ```

2. Certifique-se de ter o Python 3.12 (ou superior) instalado em sua máquina. Você pode verificar a versão instalada com:
   ```bash
   python --version
   ```

3. Crie e ative um ambiente virtual (opcional, mas recomendado):
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Linux/Mac
   .venv\Scripts\activate           # Windows
   ```

4. Instale as dependências do projeto usando `pip`:
   ```bash
   pip install .
   ```

   Ou, caso prefira instalar também dependências de desenvolvimento:
   ```bash
   pip install .[dev]
   ```

5. Execute o simulador:
   ```bash
   python main.py
   ```

---

## 📊 Exemplo de Exibição

### Logs no terminal:
Durante a execução, serão exibidas mensagens de log coloridas que detalham o estado do sistema, incluindo bloqueios, esperas, resolução de deadlocks e finalização das transações.

### Visualização do grafo de espera:
É possível habilitar um grafo de espera ao vivo para visualizar o estado atual das dependências entre transações, incluindo detecção de ciclos. Para isso, ative o visualizador editando o seguinte trecho de código no arquivo `main.py`: