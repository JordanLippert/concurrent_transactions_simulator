import time
import random
from colorama import Fore, Style

def delay(min_time: float =0.1, max_time: float=1):
    """Simula um tempo de execução aleatório entre as etapas."""
    time.sleep(random.uniform(min_time, max_time))

def log_info(message: str):
    print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")

def log_success(message: str):
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

def log_warning(message: str):
    print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")

def log_error(message: str):
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")

def log_critical(message: str):
    print(f"{Fore.MAGENTA}{message}{Style.RESET_ALL}")

def log_lock_unlock(message: str):
    print(f"{Fore.BLUE}{message}{Style.RESET_ALL}")