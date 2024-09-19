import subprocess

from rich.console import Console

# Initialize a rich console for pretty printing
console = Console()


class SlitherAnalyzer:
    """
    This class is responsible for running Slither on a given Solidity file and determining if it is vulnerable to reentrancy.
    """

    def __init__(self, file_path):
        self.file_path = file_path

    def run_analysis(self):
        """
        Run the Slither static analysis tool on the provided Solidity file and check if it has reentrancy vulnerabilities.
        Returns True if reentrancy is detected, False otherwise.
        """
        try:
            console.print(f"[bold blue]Running Slither on {self.file_path}...[/bold blue]")
            result = subprocess.run(['slither', self.file_path], capture_output=True, text=True)

            # Check the result to see if it contains reentrancy vulnerability warnings
            if "reentrancy" in result.stdout.lower():
                console.print(f"[red]Reentrancy vulnerability found in {self.file_path}[/red]\n")
                return True  # Reentrancy detected
            else:
                console.print(f"[green]No reentrancy vulnerability in {self.file_path}[/green]\n")
                return False  # No reentrancy detected
        except FileNotFoundError:
            console.print(
                "[bold red]Error: Slither is not installed or not found in your system path. Please install Slither.[/bold red]")
            return False
        except Exception as e:
            console.print(f"[bold red]An error occurred while running Slither on {self.file_path}: {e}[/bold red]")
            return False
