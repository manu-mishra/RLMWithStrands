"""Terminal display utilities"""

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_progress(text):
    print(f"{Colors.BLUE}▶{Colors.END} {text}")

def print_success(text):
    print(f"{Colors.GREEN}✓{Colors.END} {text}")

def print_error(text):
    print(f"{Colors.RED}✗{Colors.END} {text}")

def print_info(text):
    print(f"{Colors.YELLOW}ℹ{Colors.END} {text}")

def print_divider():
    print(f"{Colors.CYAN}{'─'*70}{Colors.END}")

def format_status(passed):
    """Format pass/fail status with color"""
    if passed:
        return f"{Colors.GREEN}✓ PASS{Colors.END}"
    return f"{Colors.RED}✗ FAIL{Colors.END}"

def format_pass_rate(passed, total):
    """Format pass rate with color based on percentage"""
    rate = (passed/total*100) if total > 0 else 0
    
    if rate == 100:
        color = Colors.GREEN
    elif rate >= 50:
        color = Colors.YELLOW
    else:
        color = Colors.RED
    
    return f"{color}{passed}/{total} passed ({rate:.0f}%){Colors.END}"
