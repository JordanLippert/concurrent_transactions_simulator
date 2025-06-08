from colorama import Fore, Style

def log_info(message: str):
    print(f"{Fore.CYAN}[INFO] {message}{Style.RESET_ALL}")

def log_success(message: str):
    print(f"{Fore.GREEN}[SUCCESS] {message}{Style.RESET_ALL}")

def log_warning(message: str):
    print(f"{Fore.YELLOW}[WARNING] {message}{Style.RESET_ALL}")

def log_error(message: str):
    print(f"{Fore.RED}[ERROR] {message}{Style.RESET_ALL}")

def log_critical(message: str):
    print(f"{Fore.MAGENTA}[CRITICAL] {message}{Style.RESET_ALL}")

def log_lock_unlock(message: str):
    print(f"{Fore.BLUE}[LOCK/UNLOCK] {message}{Style.RESET_ALL}")