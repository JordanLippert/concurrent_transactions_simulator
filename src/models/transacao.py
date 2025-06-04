import threading
from networkx import DiGraph, simple_cycles
from typing import Dict
from src.models.recurso import Recurso
from src.models.transacao_info import TransacaoInfo
from src.utils.utils import log_info, log_critical, log_error, log_success, log_warning, log_lock_unlock, delay

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
        while not self.terminada:
            log_info(f"[INÍCIO] T({self.tid}) entrou em execução.")

            if self.timestamp % 2 == 0:
                delay()
                self.lock_recurso('X')

                delay()
                self.lock_recurso('Y')

                delay()
                self.unlock_recurso('X')

                delay()
                self.unlock_recurso('Y')

                delay()
                log_success(f"[COMMIT] T({self.tid}) finalizou sua execução.")
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

            self.terminada = True

    def lock_recurso(self, item: str) -> bool:
        recurso = self.recursos[item]

        with self.lock_global:
            # Caso 1: recurso livre → trava imediatamente
            if recurso.valor_lock is None:
                recurso.valor_lock = True
                recurso.transacao = self.tid
                log_lock_unlock(f"[LOCK] T({self.tid}) obteve lock em {item}")
                return True

            # Caso 2: a transação já possui o lock → nada a fazer
            elif recurso.transacao == self.tid:
                return True

            # Caso 3: recurso ocupado por outra transação → entra em espera
            else:
                other_tid = recurso.transacao
                log_info(f"[ESPERA] T({self.tid}) esperando por {item} que está com T({other_tid})")

                # Entra na fila de espera do recurso
                recurso.fila_espera.append(self.tid)

                # Adiciona aresta no grafo de espera (self depende de other)
                if other_tid is not None:
                    self.grafo_espera.add_edge(self.tid, other_tid) 

        # Loop de espera ativo até conseguir o lock ou ser abortada
        while (recurso.transacao != self.tid) and not self.terminada:
            delay(0.5) # verificar a cada 50 milessimos
            with self.lock_global:
                # Se recurso estiver livre e for o primeiro da fila → pega o lock
                # Somente pega quem for o primeiro da fila
                if recurso.valor_lock is None and (not recurso.fila_espera or recurso.fila_espera[0] == self.tid):
                    recurso.valor_lock = True
                    recurso.transacao = self.tid

                    # Remove ele da filou do recurso, pois acabou de pegar o recurso
                    if self.tid in recurso.fila_espera:
                        recurso.fila_espera.remove(self.tid)

                    # Remove do grafo de espera, pois pegou o recurso
                    self.grafo_espera.remove_node(self.tid)

                    log_lock_unlock(f"[LOCK] T({self.tid}) obteve lock em {item}")

                    return True

                # Se foi detectado deadlock, aplicar wait-die
                if self.detect_deadlock():
                    log_warning(f"[DEADLOCK] Detectado envolvendo T({self.tid}) e T({recurso.transacao}). Ambas desejam R({recurso.item_id}))")
                    self.apply_wait_die(recurso.transacao)
                    return False
        
        return False
                        

    def unlock_recurso(self, item: str) -> None:
        recurso = self.recursos[item]
        with self.lock_global:
            if recurso.transacao == self.tid:
                # Libera o recurso
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
            cycles = list(simple_cycles(self.grafo_espera))

            # Check if this transaction is in any of those deadlocks
            deadlock = any(self.tid in cycle for cycle in cycles)
            return deadlock
        except Exception:
            return False
    
    def apply_wait_die(self, other_tid: str | None) -> bool:
        # Se o id do outro processo for nulo, so volta true
        if other_tid == None:
            return True

        minha_ts = self.timestamp
        outra_ts = self.transacoes_timestamp[other_tid].timestamp

        if minha_ts < outra_ts:
            log_critical(f"[WAIT-DIE] T({self.tid}) é mais velha que T({other_tid}) → continua esperando")
            return True
        else:
            log_critical(f"[WAIT-DIE] T({self.tid}) é mais nova que T({other_tid}) → será abortada")
            self.abort()
            return False
    
    def abort(self) -> bool:
        with self.lock_global:

            # 1. Remove from all waiting queues
            for recurso in self.recursos.values():
                if self.tid in recurso.fila_espera:
                    recurso.fila_espera.remove(self.tid)

                if recurso.transacao == self.tid:
                    # Release held lock
                    recurso.valor_lock = None
                    recurso.transacao = None
                    log_info(f"[FORCE UNLOCK] T({self.tid}) liberou {recurso.item_id}")

            # 2. Remove from wait-for graph
            if self.grafo_espera.has_node(self.tid):
                self.grafo_espera.remove_node(self.tid)

            # 3. Mark as terminated
            self.terminada = True

        log_error(f"[ABORTADA] T({self.tid}) morta por wait-die após conflito")

        return False

        