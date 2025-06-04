from threading import Lock
from typing import Optional, List
from pydantic import BaseModel, PrivateAttr, Field

class Recurso(BaseModel):
    """
    Representa um recurso no simulador de controle de concorrência.

    Atributos:
        item_id (str): Identificador único do recurso.
        valor_lock (Optional[bool]): Indica se o recurso está logicamente bloqueado (True), desbloqueado (False) ou indefinido (None).
        transacao (Optional[str]): Nome da transação que está utilizando o recurso, se houver.
        fila_espera (List[str]): Lista de identificadores de transações aguardando o recurso.
        _lock (threading.Lock): Lock interno usado para controle de acesso concorrente ao recurso (não exposto externamente).
    """

    item_id: str
    valor_lock: Optional[bool] = None
    transacao: Optional[str] = None
    fila_espera: List[str] = Field(default_factory=list)

    _lock: Lock = PrivateAttr(default_factory=Lock)

    def __str__(self) -> str:
        return f"Recurso({self.item_id}, lock={self.valor_lock}, transacao={self.transacao})"