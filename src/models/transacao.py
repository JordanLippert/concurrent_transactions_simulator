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
    """
    Representa uma transação concorrente que interage com recursos compartilhados.

    Responsabilidades:
        - Simular operações de leitura/escrita em recursos.
        - Lidar com bloqueios e liberações de recursos.
        - Detectar deadlocks e aplicar políticas de resolução como WAIT-DIE.

    Attributes:
        tid (str): Identificador único da transação.
        timestamp (int): Timestamp lógico da transação.
        recursos (Dict[str, Recurso]): Dicionário com os recursos compartilhados disponíveis.
        grafo_espera (DiGraph): Grafo de espera para detectar ciclos (deadlocks).
        lock_global (threading.Lock): Lock global para coordenar o acesso ao grafo.
        terminada (bool): Indica se a transação foi finalizada/abortada.
        transacoes_timestamp (Dict[str, TransacaoInfo]): Informações de timestamp de todas as transações.
    """

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
        self.transacoes_timestamp: Dict[str, TransacaoInfo] = transacoes_timestamp

    def run(self) -> None:
        """
        Executa a transação simulando o acesso concorrente a recursos.

        A transação:
        - Tenta obter os recursos necessários utilizando o algoritmo WAIT-DIE.
        - Realiza operações simuladas por `delay()`.
        - Libera os recursos ao final, seja no commit ou devido a falhas.
        """
        log_info(f"[INÍCIO] T({self.tid}) iniciou sua execução.")

        try:
            # Itera pelos recursos
            for item in self.recursos.keys():
                if not self.lock_recurso(item):
                    log_critical(f"T({self.tid}) foi abortada durante o lock. Finalizando...")
                    self.terminada = True
                    return

            # Simula execução da transação
            delay()
            log_success(f"T({self.tid}) realizou operações com sucesso.")

            # Libera os recursos ao finalizar
            for item in self.recursos.keys():
                self.unlock_recurso(item)

            log_success(f"[COMMIT] T({self.tid}) finalizou sua execução com sucesso.")

        except AbortException as e:
            log_critical(f"T({self.tid}) abortada: {e}")
            self.terminada = True

        except Exception as e:
            log_error(f"[ERRO] T({self.tid}) encontrou um problema inesperado: {e}")
            self.terminada = True

        finally:
            # Garante que os recursos sejam liberados ao final
            for item in self.recursos.keys():
                self.unlock_recurso(item)
            log_info(f"[FINALIZOU] T({self.tid}) encerrou a execução.")

    def lock_recurso(self, item: str) -> bool:
        """
        Tenta adquirir o lock de um recurso utilizando o algoritmo WAIT-DIE.

        Args:
            item (str): O identificador do recurso.

        Returns:
            bool: True se conseguir o lock, False se for abortada.
        """
        recurso = self.recursos[item]
        log_info(f"T({self.tid}) tentando bloquear o recurso {item}.")

        if recurso.acquire(self.tid):  # Tenta adquirir o lock
            log_success(f"[LOCK] T({self.tid}) bloqueou o recurso {item}.")
            return True

        # Caso não consiga, aplica WAIT-DIE
        outra_tid = recurso.transacao
        if not self.apply_wait_die(outra_tid, recurso):
            log_critical(f"[WAIT-DIE] T({self.tid}) foi abortada.")
            return False

        # Após espera e notificação, tenta novamente
        return self.lock_recurso(item)

    def unlock_recurso(self, item: str) -> None:
        """
        Libera o lock de um recurso compartilhado.

        Args:
            item (str): O identificador do recurso.
        """
        recurso = self.recursos[item]

        # Apenas libera se a transação possuir o lock
        if recurso.transacao == self.tid:
            recurso.release(self.tid)
            log_lock_unlock(f"[UNLOCK] T({self.tid}) liberou o recurso {item}.")

    def apply_wait_die(self, other_tid: str, recurso: Recurso) -> bool:
        """
        Aplica a política WAIT-DIE para evitar deadlocks.

        Args:
            other_tid (str): Transação que detém o lock do recurso.
            recurso (Recurso): Recurso compartilhado em disputa.

        Returns:
            bool: True se continuar esperando, False se for abortada.
        """
        minha_ts = self.timestamp
        outra_ts = self.transacoes_timestamp[other_tid].timestamp

        with recurso._lock:
            if minha_ts < outra_ts:
                log_critical(f"[WAIT-DIE] T({self.tid}) é mais velha que T({other_tid}), continuará esperando.")
                recurso.wait_for_release(self.tid)
                return True
            else:
                log_critical(f"[WAIT-DIE] T({self.tid}) é mais nova que T({other_tid}), será abortada.")
                self.abort(recurso)
                return False

    def abort(self, recurso: Recurso) -> None:
        """
        Aborta a transação e libera todos os recursos bloqueados.

        Args:
            recurso (Recurso): Recurso atual relacionado ao abort.
        """
        self.terminada = True
        log_critical(f"T({self.tid}) foi abortada.")

        # Libera os recursos bloqueados
        for item in self.recursos.keys():
            self.unlock_recurso(item)

        # Lança exceção para interromper execução da transação
        raise AbortException(f"T({self.tid}) foi abortada devido à política WAIT-DIE.")