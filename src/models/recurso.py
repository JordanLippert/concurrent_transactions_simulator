from threading import Lock, Condition
from typing import Optional, List
from pydantic import BaseModel, PrivateAttr, Field


class Recurso(BaseModel):
    """
    Modelo para representar um recurso compartilhado no simulador.

    Attributes:
        item_id (str): Identificador único do recurso.
        valor_lock (Optional[bool]): Indica se o recurso está bloqueado.
        transacao (Optional[str]): Identificador da transação que possui o lock do recurso.
        fila_espera (List[str]): Lista de transações aguardando pelo recurso.

    Private Attributes:
        _lock (Lock): Mutex para controlar acesso ao recurso.
        _condition (Condition): Condição que permite sincronizar filas de espera.
    """

    item_id: str
    valor_lock: Optional[bool] = None
    transacao: Optional[str] = None
    fila_espera: List[str] = Field(default_factory=list)
    _lock: Lock = PrivateAttr()
    _condition: Condition = PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)
        lock = Lock()
        self._lock = lock
        self._condition = Condition(lock)