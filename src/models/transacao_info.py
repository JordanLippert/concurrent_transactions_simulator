from pydantic import BaseModel

class TransacaoInfo(BaseModel):
    """
    Representa os metadados de uma transação no simulador.

    Attributes:
        tid (str): O identificador único da transação.
        timestamp (int): O timestamp lógico indicando quando a transação foi iniciada.
    """
    tid: str
    timestamp: int