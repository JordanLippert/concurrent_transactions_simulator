from threading import Lock, Condition
from typing import Optional, List
from pydantic import BaseModel, PrivateAttr, Field

class Recurso(BaseModel):
    """
    Representa um recurso compartilhado.

    - item_id: identificador único do recurso.
    - valor_lock: indica se o recurso está em uso.
    - transacao: ID da transação que está usando o recurso.
    - fila_espera: lista de transações aguardando o recurso.

    Atributos privados:
    - _lock: trava usada para sincronizar acesso.
    - _condition: condição associada ao lock para espera e notificação.
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
