import threading
from typing import Optional, List

from pydantic import BaseModel, PrivateAttr, Field

class Recurso(BaseModel):
    """
    Representa um recurso no simulador.

    Attributes:
        item_id (str): O identificador único do recurso.
    """

    item_id: str
    valor_lock: Optional[bool] = None
    transacao: Optional[str] = None
    fila_espera: List[str] = Field(default_factory=list)

    _lock: threading.Lock = PrivateAttr(default_factory=threading.Lock)

    def __str__(self) -> str:
        return f"Recurso({self.item_id}, lock={self.valor_lock}, transacao={self.transacao})"