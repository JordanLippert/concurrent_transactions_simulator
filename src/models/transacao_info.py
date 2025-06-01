from pydantic import BaseModel

class TransacaoInfo(BaseModel):
    """
    Represents metadata for a transaction in the simulator.

    Attributes:
        tid (str): The unique identifier of the transaction.
        timestamp (int): The logical timestamp indicating when the transaction started.
    """
    
    tid: str
    timestamp: int