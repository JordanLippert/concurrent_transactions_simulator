from __future__ import annotations

import threading
from typing import Dict
import networkx as nx
from networkx import DiGraph, simple_cycles

from src.exceptions.abort_exeception import AbortException
from src.models.transacao_info import TransacaoInfo
from src.models.recurso import Recurso
from src.utils.logging import log_info, log_success, log_error, log_lock_unlock, log_warning, log_critical
from src.utils.control_time import delay

class Transacao(threading.Thread):
    def __init__(
        self,
        info: TransacaoInfo,
        recursos: Dict[str, Recurso],
        grafo_espera: DiGraph,
        lock_global: threading.Lock,
        transacoes_timestamp: Dict[str, TransacaoInfo],
    ):
        super().__init__()
        self.tid: str = info.tid
        self.timestamp: int = info.timestamp
        self.recursos: Dict[str, Recurso] = recursos
        self.grafo_espera: DiGraph = grafo_espera
        self.lock_global: threading.Lock = lock_global
        self.terminada: bool = False
        self.transacoes_timestamp = transacoes_timestamp


    def run(self) -> None:
        """
        Faz o lock e unlock dos recursos
        """
        while not self.terminada:
            log_info(f"[INÍCIO] T({self.tid}) entrou em execução.")

            try:
                if self.timestamp % 2 == 0:
                    delay()
                    self.lock_recurso('X')

                    delay()
                    self.lock_recurso('Y')

                    delay()
                    self.unlock_recurso('X')

                    delay()
                    self.unlock_recurso('Y')

                else:
                    delay()
                    self.lock_recurso('Y')

                    delay()
                    self.lock_recurso('X')

                    delay()
                    self.unlock_recurso('Y')

                    delay()
                    self.unlock_recurso('X')

                delay()
                log_success(f"[COMMIT] T({self.tid}) finalizou sua execução.")

            except AbortException:
                log_error(f"[FINALIZAÇÃO] T({self.tid}) abortada com sucesso.")
                # reinicia a transação após ser abortada

            finally:
                self.terminada = True

    def lock_recurso(self, item: str) -> bool:
        recurso = self.recursos[item]

        with recurso._condition:
            if recurso.valor_lock is None:
                recurso.valor_lock = True
                recurso.transacao = self.tid
                log_lock_unlock(f"[LOCK] T({self.tid}) obteve lock em {item}")
                return True

            elif recurso.transacao == self.tid:
                return True

            else:
                other_tid = recurso.transacao
                log_info(f"[ESPERA] T({self.tid}) esperando por {item} que está com T({other_tid})")
                recurso.fila_espera.append(self.tid)
                if other_tid:
                    self.grafo_espera.add_edge(self.tid, other_tid)

            while recurso.transacao != self.tid and not self.terminada:
                if self.detect_deadlock():
                    log_warning(
                        f"[DEADLOCK] Detectado envolvendo T({self.tid}) e T({recurso.transacao}). Ambas desejam R({recurso.item_id}))")
                    if recurso.transacao is not None:
                        self.apply_wait_die(recurso.transacao, recurso)
                        return False
                    continue

                recurso._condition.wait(timeout=0.5)

                if recurso.valor_lock is None and (not recurso.fila_espera or recurso.fila_espera[0] == self.tid):
                    recurso.valor_lock = True
                    recurso.transacao = self.tid
                    if self.tid in recurso.fila_espera:
                        recurso.fila_espera.remove(self.tid)
                    if self.grafo_espera.has_edge(self.tid, other_tid):
                        self.grafo_espera.remove_edge(self.tid, other_tid)
                    log_lock_unlock(f"[LOCK] T({self.tid}) obteve lock em {item}")
                    return True

        return False

    def unlock_recurso(self, item: str) -> None:
        recurso = self.recursos[item]
        with recurso._condition:
            if recurso.transacao == self.tid:
                recurso.valor_lock = None
                recurso.transacao = None
                log_info(f"[UNLOCK] T({self.tid}) liberou {item}")
                recurso._condition.notify_all()

    def detect_deadlock(self) -> bool:
        """
        Detecta a ocorrência de deadlock, onde duas ou mais threads estão bloqueadas,
        cada uma esperando por um recurso que a outra detém.
        """
        try:
            cycles = list(simple_cycles(self.grafo_espera))
            return any(self.tid in cycle for cycle in cycles)
        except Exception as e:
            log_error(f"Erro ao detectar deadlock: {e}")
            return False

    def apply_wait_die(self, other_tid: str, recurso: Recurso) -> bool:
        minha_ts = self.timestamp
        outra_ts = self.transacoes_timestamp[other_tid].timestamp

        if minha_ts < outra_ts:
            log_critical(f"[WAIT-DIE] T({self.tid}) é mais velha que T({other_tid}) → continua esperando")
            return True
        else:
            log_critical(f"[WAIT-DIE] T({self.tid}) é mais nova que T({other_tid}) → será abortada")
            self.abort(recurso)
            return False

    def abort(self, recurso: Recurso) -> bool:
        """
        Mata a transação que chamou a função.

        Args:
            recurso (Recurso): Recurso que motivou o abort.

        Returns:
            bool: True se foi abortada com sucesso.
        """
        try:
            # Remove das filas de espera e libera recursos
            for r in self.recursos.values():
                if self.tid in r.fila_espera:
                    r.fila_espera.remove(self.tid)

                if r.transacao == self.tid:
                    r.valor_lock = None
                    r.transacao = None
                    log_info(f"[FORCE UNLOCK] T({self.tid}) liberou {r.item_id}")
                    with r._condition:
                        r._condition.notify_all()

            if self.grafo_espera.has_node(self.tid):
                self.grafo_espera.remove_node(self.tid)

            self.terminada = True
            raise AbortException()

        except AbortException:
            return True

        except Exception as e:
            log_error(f"Exceção ao tentar matar transação: {e}")
            return False

    def add_edge(self, transacao_esperando: str, transacao_segurando: str):
        """Adiciona uma aresta no grafo de espera se ela ainda não existir."""
        with self.grafo_locked:
            if not self.grafo_deadlock.has_edge(transacao_esperando, transacao_segurando):
                self.grafo_deadlock.add_edge(transacao_esperando, transacao_segurando)



    def remove_edges(self, transacao: Transacao):
        """Remove todas as arestas de entrada e saída da transação no grafo de espera."""
        with self.grafo_locked:
            tid = transacao.tid
            edges_to_remove = list(self.grafo_deadlock.in_edges(tid)) + list(self.grafo_deadlock.out_edges(tid))
            self.grafo_deadlock.remove_edges_from(edges_to_remove)
