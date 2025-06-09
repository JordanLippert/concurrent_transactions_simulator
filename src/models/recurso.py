import threading
from threading import Lock, Condition
from typing import Optional, List
from pydantic import BaseModel, PrivateAttr, Field


class Recurso(BaseModel):
    """
    Modelo para representar um recurso compartilhado no simulador.

    Attributes:
        item_id (str): Identificador único do recurso.
        valor_lock (Optional[bool]): Indica se o recurso está bloqueado por uma transação.
        transacao (Optional[str]): Identificador da transação que possui atualmente o lock do recurso.
        fila_espera (List[str]): Lista de transações aguardando pelo recurso.

    Private Attributes:
        _lock (Lock): Mutex para controlar acesso exclusivo ao recurso.
        _condition (Condition): Condição para sincronizar filas de espera de threads.
    """

    item_id: str
    valor_lock: Optional[bool] = None
    transacao: Optional[str] = None
    fila_espera: List[str] = Field(default_factory=list)
    _lock: Lock = PrivateAttr()
    _condition: Condition = PrivateAttr()

    def __init__(self, item_id: str, valor_lock=None, fila_espera=None):
        super().__init__(item_id=item_id, valor_lock=valor_lock, fila_espera=fila_espera or [])
        self._lock = threading.Lock()                     # Lock exclusivo para o recurso
        self._condition = threading.Condition(self._lock)  # Condição atrelada ao lock

    def acquire(self, tid: str) -> bool:
        """
        Tenta adquirir o lock do recurso para uma transação específica.

        Args:
            tid (str): Identificador da transação tentando adquirir o recurso.

        Returns:
            bool: Retorna True se a transação conseguiu adquirir o recurso, False caso contrário.
        """
        with self._lock:
            if self.valor_lock is None:  # O recurso está livre
                self.valor_lock = tid
                self.transacao = tid
                return True
            else:
                # Recurso já está bloqueado
                if tid not in self.fila_espera:
                    self.fila_espera.append(tid)  # Adiciona à fila se ainda não estiver
                return False

    def release(self, tid: str) -> None:
        """
        Libera o lock do recurso, permitindo que outras transações aguardando na fila possam adquiri-lo.

        Args:
            tid (str): Identificador da transação que está liberando o recurso.
        """
        with self._lock:
            if self.valor_lock == tid:  # Verifica se a transação atual possui o lock
                self.valor_lock = None
                self.transacao = None

                # Notifica todas as threads aguardando que o recurso foi liberado
                if self.fila_espera:
                    prox_tid = self.fila_espera.pop(0)  # Remove o próximo da fila (prioridade)
                    self._condition.notify_all()  # Informa mudanças no estado do recurso

    def wait_for_release(self, tid: str) -> None:
        """
        Coloca a transação em espera até que o recurso seja liberado.

        Args:
            tid (str): Identificador da transação aguardando pelo recurso.
        """
        with self._condition:  # Sincroniza com base na condição associada ao lock do recurso
            while self.valor_lock is not None and self.valor_lock != tid:
                self._condition.wait()  # Bloqueia até o recurso ser liberado