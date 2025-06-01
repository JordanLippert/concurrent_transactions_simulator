import time
import random
import threading
import networkx as nx
from typing import Dict
from .recurso import Recurso
from .transacao_info import TransacaoInfo
from src.utils.utils import log_info, log_critical, log_error, log_success, log_warning

class Transacao(threading.Thread):
    def __init__(
        self,
        info: TransacaoInfo,
        recursos: Dict[str, Recurso],
        grafo_espera: nx.DiGraph,
        lock_global: threading.Lock,
        transacoes_timestamp: Dict[str, TransacaoInfo],
    ):
        super().__init__()
        self.tid: str = info.tid
        self.timestamp: int = info.timestamp
        self.recursos: Dict[str, Recurso] = recursos
        self.grafo_espera: nx.DiGraph = grafo_espera
        self.lock_global: threading.Lock = lock_global
        self.terminada: bool = False
        self.transacoes_timestamp = transacoes_timestamp

    def run(self) -> None:
        while not self.terminada:
            log_info(f"[INÍCIO] T({self.tid}) entrou em execução.")

            self.random_sleep()
            if not self.lock_recurso('X'):
                continue

            self.random_sleep()
            if not self.lock_recurso('Y'):
                self.unlock_recurso('X')
                continue

            self.random_sleep()
            self.unlock_recurso('X')

            self.random_sleep()
            self.unlock_recurso('Y')

            self.random_sleep()
            log_success(f"[COMMIT] T({self.tid}) finalizou sua execução.")
            self.terminada = True

    def random_sleep(self) -> None:
        """
        Delay execution for [0.5, 1.5] seconds
        """
        time.sleep(random.uniform(0.5, 1.5))

    def lock_recurso(self, item: str) -> bool:
        recurso = self.recursos[item]

        with self.lock_global:
            if recurso.valor_lock is None:
                recurso.valor_lock = True
                recurso.transacao = self.tid
                log_info(f"[LOCK] T({self.tid}) obteve lock em {item}")
                return True

            elif recurso.transacao == self.tid:
                return True

            else:
                other_tid = recurso.transacao

                if other_tid is None: # verificar esta parte
                    return False

                if self.timestamp < self.transacoes_timestamp[other_tid].timestamp:
                    log_info(f"[ESPERA] T({self.tid}) esperando por {item} que está com T({other_tid})")
                    recurso.fila.append(self.tid)
                    self.grafo_espera.add_edge(self.tid, other_tid)
                else:
                    log_error(f"[ABORTADA] T({self.tid}) morta por wait-die (tentou lock em {item})")
                    self.grafo_espera.remove_edges_from(list(self.grafo_espera.edges(self.tid)))
                    return False

        while True:
            time.sleep(0.5)
            with self.lock_global:
                if recurso.valor_lock is None and (not recurso.fila or recurso.fila[0] == self.tid):
                    recurso.valor_lock = True
                    recurso.transacao = self.tid
                    if self.tid in recurso.fila:
                        recurso.fila.remove(self.tid)
                    self.grafo_espera.remove_edges_from(list(self.grafo_espera.edges(self.tid)))
                    log_info(f"[LOCK] T({self.tid}) obteve lock em {item}")
                    return True

                if self.detect_deadlock():
                    log_critical(f"[DEADLOCK] T({self.tid}) detectou deadlock e será finalizada.")
                    self.grafo_espera.remove_edges_from(list(self.grafo_espera.edges(self.tid)))
                    return False

    def unlock_recurso(self, item: str) -> None:
        recurso = self.recursos[item]
        with self.lock_global:
            if recurso.transacao == self.tid:
                recurso.valor_lock = None
                recurso.transacao = None
                log_info(f"[UNLOCK] T({self.tid}) liberou {item}")

    def detect_deadlock(self) -> bool:
        """
            Detecta a ocorrência de deadlock, onde duas ou mais threads estão bloqueadas, cada uma
            esperando por um recurso que a outra detém, impossibilitando que qualquer uma avance

        Returns:
            bool: True if exists an deadlock, else False
        """
        try:
            # Get list of deadlocks (cycles) in the system
            cycles = list(nx.simple_cycles(self.grafo_espera))

            # Check if this transaction is in any of those deadlocks
            deadlock = any(self.tid in cycle for cycle in cycles)
            return deadlock
        except Exception:
            return False