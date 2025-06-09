import threading
import random
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict
from src.models.recurso import Recurso
from src.models.transacao import Transacao
from src.models.transacao_info import TransacaoInfo
from src.utils.logging import log_success
from src.visualization.grafo_visualizador import GrafoVisualizador

def main() -> None:
    """
    Executa o simulador de controle de concorrência com múltiplas transações competindo por recursos compartilhados.
    """
    # Ativa modo interativo do matplotlib (para visualização)
    plt.ion()

    # Inicializa recursos compartilhados
    recursos: Dict[str, Recurso] = {
        'X': Recurso(item_id='X'),
        'Y': Recurso(item_id='Y')
    }

    # Inicializa o grafo de espera e o lock global para sincronização
    grafo_espera = nx.DiGraph()
    grafo_lock = threading.Lock()

    # Define o número de transações
    numero_transacoes = 10

    # Dicionários para armazenar metadados e threads de transações
    transacoes_timestamp: Dict[str, TransacaoInfo] = {}
    transacoes_threads: Dict[str, Transacao] = {}

    # Inicializa os timestamps das transações de forma aleatória
    for i in range(numero_transacoes):
        tid = f"T{i}"
        timestamp = random.randint(1, 1000)  # Gera um timestamp lógico
        transacoes_timestamp[tid] = TransacaoInfo(tid=tid, timestamp=timestamp)

    # Cria as instâncias de Transacao
    for info in transacoes_timestamp.values():
        transacao = Transacao(
            info=info,
            recursos=recursos,
            grafo_espera=grafo_espera,
            lock_global=grafo_lock,
            transacoes_timestamp=transacoes_timestamp
        )
        transacoes_threads[info.tid] = transacao

    # Inicia visualizador de grafo (opcional)
    #grafo_visualizador = GrafoVisualizador(grafo_espera)
    #grafo_visualizador.start()

    # Inicia todas as threads de transações
    for transacao in transacoes_threads.values():
        transacao.start()

    # Aguarda todas as threads finalizarem
    for transacao in transacoes_threads.values():
        transacao.join()

    # Finaliza o visualizador de grafo
    #grafo_visualizador.parar()

    log_success("\n[FIM] Todas as transações foram finalizadas.")


if __name__ == "__main__":
    main()