# Simulador de Controle de Concorrência com Detecção e Resolução de Deadlocks

## 🎯 Objetivo

Este projeto simula a execução de transações concorrentes que competem por recursos compartilhados (`X` e `Y`) utilizando `threads` em Python. O principal foco é demonstrar:

- O controle de acesso com bloqueios binários;
- A ocorrência de deadlocks;
- A detecção e resolução de deadlocks usando técnicas baseadas em timestamp (wait-die ou wound-wait).

---

## 🧠 Funcionalidades

- Criação de N transações concorrentes simuladas por threads;
- Acesso aleatório aos recursos `X` e `Y`;
- Implementação de bloqueios binários por recurso;
- Identificação automática de deadlocks;
- Resolução dos deadlocks por timestamp;
- Retomada da execução após resolução de conflito;
- Saída detalhada no terminal informando o estado das transações.

---

## 🛠️ Tecnologias Utilizadas

- Python 3.10+
- `threading` para concorrência
- `networkx` para representar o grafo de espera (wait-for graph)
- `random`, `time` para simulação de comportamento realista

---

## 📦 Instalação

1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
