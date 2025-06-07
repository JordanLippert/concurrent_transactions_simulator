from __future__ import annotations

import threading
from typing import Dict
import networkx as nx
from src.models.transacao_info import TransacaoInfo
from src.models.recurso import Recurso
from src.utils.logging import log_info, log_success, log_error, log_lock_unlock, log_warning, log_critical
from src.utils.control_time import delay

class Transacao(threading.Thread):
    def __init__(
        self,
        info: TransacaoInfo,
        recursos: Dict[str, Recurso],
        todas_transacoes: Dict[str, TransacaoInfo],
        grafo_deadlock: nx.DiGraph, 
        grafo_locked: threading.Lock
    ):
        super().__init__()
        self.tid: str = info.tid
        self.timestamp: int = info.timestamp
        self.recursos: Dict[str, Recurso] = recursos
        self.todas_transacoes: Dict[str, TransacaoInfo] = todas_transacoes
        self.grafo_deadlock = grafo_deadlock
        self.grafo_locked: threading.Lock = grafo_locked
        self.terminada: bool = False

    def run(self) -> None:
        """
        Faz o lock e unlock dos recursos
        """

        while not self.terminada:
            log_info(f"[INÍCIO] T({self.tid}) entrou em execução.")

            recurso_x: Recurso = self.recursos['X']
            recurso_y: Recurso = self.recursos['Y']

            try:
                if self.timestamp % 2 == 0:
                    delay()
                    self.lock_recurso(recurso_x, self)

                    delay()
                    self.lock_recurso(recurso_y, self)

                    delay()
                    self.unlock_recurso(recurso_x, self)

                    delay()
                    self.unlock_recurso(recurso_y, self)

                else:
                    delay()
                    self.lock_recurso(recurso_y, self)

                    delay()
                    self.lock_recurso(recurso_x, self)

                    delay()
                    self.unlock_recurso(recurso_y, self)

                    delay()
                    self.unlock_recurso(recurso_x, self)

            finally:
                delay()
                log_success(f"[COMMIT] T({self.tid}) finalizou sua execução.")  
                
                # Remove o nó
                if self.tid in self.grafo_deadlock:
                    self.grafo_deadlock.remove_node(self.tid)
                    
                self.terminada = True

    def lock_recurso(self, recurso: Recurso, transacao: Transacao) -> bool:
        """
        Tenta adquirir o lock de um recurso. Se não conseguir de imediato,
        entra em modo de espera, detecta deadlock e aplica a política wait-die.
        """
        with recurso._cond:
            # Tenta adquirir o lock imediatamente
            if recurso._lock.acquire(blocking=False):
                recurso.transacao = transacao.tid
                log_lock_unlock(f"[LOCK] T({transacao.tid}) obteve lock em {recurso.item_id}")
                return True

            # Caso o recurso esteja ocupado
            log_info(f"[CHECK] T({transacao.tid}) tentando lock em {recurso.item_id} — ocupado por T({recurso.transacao})? {recurso._lock.locked()}")

            # Adiciona à fila de espera
            if transacao.tid not in recurso.fila_espera:
                recurso.fila_espera.append(transacao.tid)

            log_info(f"[ESPERA] T({transacao.tid}) esperando por {recurso.item_id} que está com T({recurso.transacao})")

            if recurso.transacao is not None:
                self.add_edge(transacao.tid, recurso.transacao)

            # Loop de espera enquanto recurso estiver bloqueado
            while recurso.transacao is not None and recurso.transacao != transacao.tid:
                if self.terminada:
                    return False

                delay(2)
                log_info(f"[ESPERA-LOOP] T({transacao.tid}) dentro do loop de espera por {recurso.item_id}")

                if self.detect_deadlock():
                    log_warning(f"""[DEADLOCK] Detectado envolvendo T({transacao.tid}) e T({recurso.transacao}).
                                    Ambas desejam R({recurso.item_id})""")
                    if self.apply_wait_die(recurso, transacao):
                        return False  # Se a transação for abortada, interrompe

                recurso._cond.wait(timeout=0.1)  # Aguarda liberação do recurso

            # Ao sair do loop, tenta novamente adquirir o lock
            if self.terminada:
                return False

            if recurso._lock.acquire(blocking=False):
                recurso.transacao = transacao.tid
                log_lock_unlock(f"[LOCK] T({transacao.tid}) obteve lock em {recurso.item_id}")
                return True

            return False  # fallback de segurança


    def unlock_recurso(self, recurso: Recurso, transacao: Transacao) -> None:
        """
        Desbloqueia o recurso, para que outros processos
        possam utilizar ele
        """ 

        # Libera o recurso
        tid = recurso.transacao
        recurso.transacao = None
        self.remove_edges(transacao)
        if transacao.tid in recurso.fila_espera:
            recurso.fila_espera.remove(transacao.tid)
        if recurso._lock.locked():
            recurso._lock.release()
        log_info(f"[UNLOCK] T({tid}) liberou {recurso.item_id}")

        recurso._cond.notify_all()  # Notifica todos na espera

        # Se há alguém na fila de espera, tenta acordar a próxima transação
        if recurso.fila_espera:
            proxima_tid = recurso.fila_espera[0] 
            log_info(f"[DESPERTAR] T({proxima_tid}) é a próxima da fila para {recurso.item_id}")


    def detect_deadlock(self) -> bool:
        """
            Detecta a ocorrência de deadlock, onde duas ou mais threads estão bloqueadas, cada uma
            esperando por um recurso que a outra detém, impossibilitando que qualquer uma avance
        """
        print(self.grafo_deadlock)
        # Pega todos os deadlocks do sistema
        cycles = list(nx.simple_cycles(self.grafo_deadlock))

        if cycles:
            print(f"[CICLO] Deadlock detectado: {cycles}")

        # Se tiver algo nos ciclos, há deadlock
        is_there_deadlock = len(cycles) > 0
        return is_there_deadlock
    

    def apply_wait_die(self, recurso: Recurso, transacao: Transacao) -> bool:
        """
        Aplica a política Wait-Die:
        Se a transação atual for mais velha (timestamp menor) que a que detém o recurso, espera.
        Se for mais nova (timestamp maior), aborta.
        """

        if recurso.transacao is None or transacao is None:
            return False 

        # Separa qual a transacao que quer o recurso daquela segurando o recurso
        transacao_querendo = transacao
        transacao_segurando = self.todas_transacoes[recurso.transacao]

        # Compare os timestamps para saber o que fazer
        if transacao_querendo.timestamp < transacao_segurando.timestamp:
            # Transação atual é mais velha, deve esperar
            log_critical(f"[WAIT-DIE] T({transacao_querendo.tid}) é mais velha que T({transacao_segurando.tid}) → continua esperando")
            return False
        else:
            # Transação atual é mais nova, deve abortar
            log_critical(f"[WAIT-DIE] T({transacao_querendo.tid}) é mais nova que T({transacao_segurando.tid}) → será abortada")
            self.abort(recurso, transacao_querendo) 
            return True
    

    def abort(self, recurso: Recurso, transacao: Transacao) -> bool:
        self.terminada = True
        self.unlock_recurso(recurso, transacao)
        log_error(f"[ABORT] T({transacao.tid}) foi abortada.")
        log_info(f"[CHECK] T({transacao.tid}) tentando lock em {recurso.item_id} — ocupado por T({recurso.transacao})? {recurso._lock.locked()}")
        return True

        
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
