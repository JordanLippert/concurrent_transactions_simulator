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
        Executa a transação simulando o acesso concorrente a recursos.

        A transação:
        - Tenta obter dois recursos em uma ordem dependente do timestamp.
        - Realiza leitura/escrita (simulada com delay).
        - Libera os recursos ao final.
        - Pode ser abortada se houver deadlock ou timeout.

        O método respeita o atributo `self.terminada`, que pode ser marcado
        como True pelo mecanismo de abort. Nesse caso, a transação para.
        """
        while not self.terminada:
            log_info(f"[INÍCIO] T({self.tid}) entrou em execução.")

            try:
                if self.timestamp % 2 == 0:
                    delay()
                    if not self.lock_recurso('X'):
                        return

                    delay()
                    if not self.lock_recurso('Y'):
                        return

                    delay()
                    self.unlock_recurso('X')

                    delay()
                    self.unlock_recurso('Y')

                else:
                    delay()
                    if not self.lock_recurso('Y'):
                        return

                    delay()
                    if not self.lock_recurso('X'):
                        return

                    delay()
                    self.unlock_recurso('Y')

                    delay()
                    self.unlock_recurso('X')

                delay()
                log_success(f"[COMMIT] T({self.tid}) finalizou sua execução.")
                self.terminada = True

            except Exception as e:
                log_error(f"[ERRO] T({self.tid}) encontrou exceção inesperada: {e}")
                self.terminada = True

            finally:
                # Segurança extra — evita reinício indevido
                self.terminada = True
                log_info(f"[FINALIZOU] T({self.tid}) terminou run().")

    def lock_recurso(self, item: str) -> bool:
        """
        Tenta obter o lock exclusivo de um recurso compartilhado.

        Implementa:
        - Lock imediato se o recurso estiver livre.
        - Controle de deadlock com algoritmo wait-die.
        - Espera passiva usando threading.Condition.
        - Timeout de segurança para evitar espera infinita.

        Args:
            item (str): Nome do recurso (ex: 'X', 'Y').

        Returns:
            bool: True se obteve o lock; False se foi abortada.
        """
        recurso = self.recursos[item]

        with recurso._condition:
            # Caso 1: recurso livre
            if recurso.valor_lock is None:
                recurso.valor_lock = True
                recurso.transacao = self.tid
                log_lock_unlock(f"[LOCK] T({self.tid}) obteve lock em {item}")
                return True

            # Caso 2: já possui o lock
            elif recurso.transacao == self.tid:
                return True

            # Caso 3: recurso ocupado
            else:
                other_tid = recurso.transacao
                log_info(f"[ESPERA] T({self.tid}) esperando por {item} que está com T({other_tid})")
                if self.tid not in recurso.fila_espera:
                    recurso.fila_espera.append(self.tid)
                if other_tid:
                    self.grafo_espera.add_edge(self.tid, other_tid)

        # Loop de espera com timeout, deadlock check e log extra
        tentativas = 0
        max_tentativas = 10

        while not self.terminada:
            with recurso._condition:
                recurso._condition.wait(timeout=0.25)
                tentativas += 1

                # Se foi abortada externamente
                if self.terminada:
                    return False

                # Log de monitoramento de espera
                log_info(f"[DEBUG] T({self.tid}) ainda aguardando {item}. Tentativa {tentativas}")

                # Se é a vez da transação
                if recurso.valor_lock is None and recurso.fila_espera and recurso.fila_espera[0] == self.tid:
                    recurso.valor_lock = True
                    recurso.transacao = self.tid
                    recurso.fila_espera.remove(self.tid)  # ✅ remover da fila!

                    self.grafo_espera.remove_edges_from(list(self.grafo_espera.out_edges(self.tid)))
                    log_lock_unlock(f"[LOCK] T({self.tid}) obteve lock em {item}")
                    return True

                # Verifica deadlock
                if self.detect_deadlock():
                    log_warning(
                        f"[DEADLOCK] Detectado envolvendo T({self.tid}) e outras transações."
                    )
                    if recurso.transacao is not None:
                        return self.apply_wait_die(recurso.transacao, recurso)

                # Timeout
                if tentativas >= max_tentativas:
                    log_warning(f"[TIMEOUT] T({self.tid}) esperou demais por {item}. Aborta.")
                    self.abort(recurso)  # Retira da fila e libera locks, se necessário
                    self.terminada = True  # Certifica que a transação será finalizada corretamente
                    return False

        return False

    def unlock_recurso(self, item: str) -> None:
        recurso = self.recursos[item]

        # Verifica se a transação realmente detém o recurso
        if recurso.transacao != self.tid:
            return

        with recurso._condition:
            recurso.valor_lock = None
            recurso.transacao = None
            log_lock_unlock(f"[UNLOCK] T({self.tid}) liberou {item}")

            # Remove a aresta do grafo de espera
            self.grafo_espera.remove_edges_from(list(self.grafo_espera.out_edges(self.tid)))

            # Notifica a próxima transação na fila, para priorizar sua execução
            if recurso.fila_espera:
                prox_tid = recurso.fila_espera.pop(0)  # Remove o próximo da fila
                log_info(f"[NOTIFY] Próximo na fila de {item} é T({prox_tid})")
                recurso._condition.notify_all()

    def detect_deadlock(self) -> bool:
        """
        Detecta a ocorrência de deadlock no grafo de espera.
        Um deadlock ocorre se houver um ciclo no grafo envolvendo a transação atual.

        Returns:
            bool: Retorna True se um deadlock envolvendo `self.tid` for detectado;
                  False caso contrário.
        """
        try:
            # Lista de ciclos simples no grafo de espera
            ciclos = list(simple_cycles(self.grafo_espera))

            # Log de todos os ciclos detectados (para depuração)
            if ciclos:
                log_warning(f"[DEADLOCK] Ciclos detectados no grafo: {ciclos}")

            # Verifica se a transação atual está em algum dos ciclos
            for ciclo in ciclos:
                if self.tid in ciclo:
                    log_critical(
                        f"[DEADLOCK] Detecção de ciclo envolvendo T({self.tid}): {ciclo}"
                    )
                    return True

            # Não há deadlocks envolvendo esta transação
            return False

        except Exception as e:
            log_error(f"[ERRO] Falha ao detectar deadlock: {e}")
            return False

    def apply_wait_die(self, other_tid: str, recurso: Recurso) -> bool:
        minha_ts = self.timestamp
        outra_ts = self.transacoes_timestamp[other_tid].timestamp

        if minha_ts < outra_ts:
            log_critical(f"[WAIT-DIE] T({self.tid}) é mais velha que T({other_tid}) → continua esperando")
            return True
        else:
            log_critical(f"[WAIT-DIE] T({self.tid}) é mais nova que T({other_tid}) → será abortada")
            self.abort(recurso)  # Aborta a transação atual
            recurso._condition.notify_all()  # Notifica todas as transações aguardando esse recurso
            return False

    def abort(self, recurso: Recurso) -> bool:
        try:
            for r in self.recursos.values():
                # Remoção da fila
                if self.tid in r.fila_espera:
                    r.fila_espera.remove(self.tid)

                # Liberação de locks pertencentes à transação abortada
                if r.transacao == self.tid:
                    r.valor_lock = None
                    r.transacao = None
                    log_info(f"[FORCE UNLOCK] T({self.tid}) liberou {r.item_id}")

                    # Notifica as threads que estão esperando esse recurso
                    with r._condition:
                        r._condition.notify_all()

            # Remover a transação do grafo de espera
            if self.grafo_espera.has_node(self.tid):
                self.grafo_espera.remove_node(self.tid)

            self.terminada = True

            log_error(f"[FINALIZAÇÃO] T({self.tid}) abortada com sucesso.")
            return True

        except Exception as e:
            log_error(f"Exceção ao tentar abortar transação: {e}")
            return False

    def add_edge(self, transacao_esperando: str, transacao_segurando: str):
        """Adiciona uma aresta no grafo de espera se ela ainda não existir."""
        with self.grafo_locked:
            if not self.grafo_deadlock.has_edge(transacao_esperando, transacao_segurando):
                self.grafo_deadlock.add_edge(transacao_esperando, transacao_segurando)

    def remove_edges(self):
        with self.lock_global:  # Evita condição de corrida
            edges_to_remove = list(self.grafo_espera.in_edges(self.tid)) + list(self.grafo_espera.out_edges(self.tid))
            self.grafo_espera.remove_edges_from(edges_to_remove)