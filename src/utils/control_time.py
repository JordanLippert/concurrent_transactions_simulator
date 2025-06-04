from time import sleep
from random import uniform

def delay(min_time: float =0.1, max_time: float=1):
    """Simula um tempo de execução aleatório entre as etapas."""
    sleep(uniform(min_time, max_time))