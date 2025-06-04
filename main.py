import threading
import random
import time
import networkx as nx
from typing import Dict
from src.models.recurso import Recurso
from src.models.transacao import Transacao 
from src.models.transacao_info import TransacaoInfo
from src.utils.utils import log_success


def main() -> None:
    # Crie os recursos a serem utilizados
    recursos: Dict[str, Recurso] = {
        'X': Recurso(item_id='X', valor_lock=None, fila_espera=[]),
        'Y': Recurso(item_id='Y', valor_lock=None, fila_espera=[])
    }

    lock_global = threading.Lock()  
    grafo_espera: nx.DiGraph = nx.DiGraph()

    numero_transacoes = 10
    transacoes_timestamp: Dict[str, TransacaoInfo] = {}
    transacoes_threads: Dict[str, Transacao] = {}

    # Inicializa as timestamps das transacoes
    for transacao in range(numero_transacoes):
        tid = f"T{transacao}"
        timestamp = random.randint(1, 1000)
        info = TransacaoInfo(tid=tid, timestamp=timestamp)
        transacoes_timestamp[tid] = info

    # Cria as transacoes
    for info in transacoes_timestamp.values():
        nova_transacao = Transacao(info, recursos, grafo_espera, lock_global, transacoes_timestamp)
        transacoes_threads[info.tid] = nova_transacao

    # Inicia as threads com as transacoes para disputarem pelos recursos X e Y
    for transacao in transacoes_threads.values():
        transacao.start()

    # Junta as threads das transacoes
    for transacao in transacoes_threads.values():
        transacao.join()

    log_success("\n[FIM] Todas as transações foram finalizadas.")


if __name__ == "__main__":
    main()
