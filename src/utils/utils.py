import time
import random
from colorama import Fore, Style

def delay(min_time=0.1, max_time=0.5):
    """Simula um tempo de execução aleatório entre as etapas."""
    time.sleep(random.uniform(min_time, max_time))

def log_info(message):
    print(f"{Fore.CYAN}[INFO] {message}{Style.RESET_ALL}")

def log_success(message):
    print(f"{Fore.GREEN}[OK] {message}{Style.RESET_ALL}")

def log_warning(message):
    print(f"{Fore.YELLOW}[AGUARDE] {message}{Style.RESET_ALL}")

def log_error(message):
    print(f"{Fore.RED}[ERRO] {message}{Style.RESET_ALL}")

def log_critical(message):
    print(f"{Fore.MAGENTA}[DEADLOCK] {message}{Style.RESET_ALL}")