"""Interactive menu system with arrow key navigation"""
import sys
import tty
import termios
from .display import Colors

class Menu:
    def __init__(self, title, options, descriptions=None):
        self.title = title
        self.options = options
        self.descriptions = descriptions or {}
        self.selected = 0
    
    def _get_key(self):
        """Get a single keypress"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ch == '\x1b':  # Escape sequence
                ch += sys.stdin.read(2)
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def display(self):
        """Display menu and return selected option"""
        while True:
            # Clear screen
            print('\033[2J\033[H', end='')
            
            # Title
            print(f"\n{Colors.BOLD}{Colors.CYAN}{self.title}{Colors.END}\n")
            print(f"{Colors.CYAN}{'─'*70}{Colors.END}\n")
            
            # Options
            for i, option in enumerate(self.options):
                if i == self.selected:
                    # Highlighted option
                    print(f"{Colors.GREEN}▶ {option}{Colors.END}")
                    if option in self.descriptions:
                        print(f"  {Colors.CYAN}{self.descriptions[option]}{Colors.END}")
                else:
                    print(f"  {option}")
                    if option in self.descriptions:
                        print(f"  {Colors.CYAN}{self.descriptions[option]}{Colors.END}")
                print()
            
            # Instructions
            print(f"\n{Colors.CYAN}{'─'*70}{Colors.END}")
            print(f"{Colors.YELLOW}↑/↓{Colors.END} Navigate  {Colors.YELLOW}Enter{Colors.END} Select  {Colors.YELLOW}q{Colors.END} Quit\n")
            
            # Get input
            key = self._get_key()
            
            if key == '\x1b[A':  # Up arrow
                self.selected = (self.selected - 1) % len(self.options)
            elif key == '\x1b[B':  # Down arrow
                self.selected = (self.selected + 1) % len(self.options)
            elif key == '\r' or key == '\n':  # Enter
                return self.options[self.selected]
            elif key == 'q' or key == 'Q':
                return None
