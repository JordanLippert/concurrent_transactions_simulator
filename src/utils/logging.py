from colorama import Fore, Style

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