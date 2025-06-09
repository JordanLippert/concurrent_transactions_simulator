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
    # Ativa modo interativo do matplotlib (para visualização)
    plt.ion()

    # Cria os recursos compartilhados
    recursos: Dict[str, Recurso] = {
        'X': Recurso(item_id='X', valor_lock=None, fila_espera=[]),
        'Y': Recurso(item_id='Y', valor_lock=None, fila_espera=[])
    }

    grafo_espera = nx.DiGraph()
    grafo_lock = threading.Lock()

    numero_transacoes = 10
    transacoes_timestamp: Dict[str, TransacaoInfo] = {}
    transacoes_threads: Dict[str, Transacao] = {}

    # Inicializa timestamps aleatórios
    for i in range(numero_transacoes):
        tid = f"T{i}"
        timestamp = random.randint(1, 1000)
        transacoes_timestamp[tid] = TransacaoInfo(tid=tid, timestamp=timestamp)

    # Cria instâncias de Transacao
    for info in transacoes_timestamp.values():
        transacao = Transacao(info, recursos, grafo_espera, grafo_lock, transacoes_timestamp)
        transacoes_threads[info.tid] = transacao

    # Inicia visualizador de grafo (opcional)
    # grafo_visualizador = GrafoVisualizador(grafo_espera)
    # grafo_visualizador.start()

    # Inicia todas as threads
    for transacao in transacoes_threads.values():
        transacao.start()

    # Aguarda todas finalizarem
    for transacao in transacoes_threads.values():
        transacao.join()

    # Encerra visualizador (se ativado)
    # grafo_visualizador.parar()

    log_success("\n[FIM] Todas as transações foram finalizadas.")

if __name__ == "__main__":
    main()
