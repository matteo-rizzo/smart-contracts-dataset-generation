import re
import subprocess
import json
from rich.console import Console
from rich.pretty import pretty_print  # This is used for pretty printing complex objects like JSON

# Initialize a rich console for pretty printing
console = Console()


class SlitherAnalyzer:
    """
    This class is responsible for running Slither on a given Solidity file and determining if it is vulnerable to reentrancy.
    """

    def __init__(self, file_path):
        """
        Initialize the SlitherAnalyzer with the Solidity file path.

        :param file_path: The path to the Solidity file to analyze.
        """
        self.file_path = file_path
        self.solc_version = self.extract_solc_version()  # Automatically extract the version from the file

    def extract_solc_version(self):
        """
        Extract the Solidity version from the file. If not found, return a default version.
        """
        try:
            with open(self.file_path, 'r') as file:
                content = file.read()

                # Find Solidity version pragma
                matches = re.findall(r'pragma\s+solidity\s*(=|>=|<=|\^)?\s*(\d+\.\d+\.\d+);', content)
                if matches:
                    exact_versions = [version for operator, version in matches if operator == '=']
                    chosen_version = exact_versions[0] if exact_versions else matches[0][1]
                    console.print(f"[bold green]Using Solidity version: {chosen_version}[/bold green]")
                    return chosen_version
                else:
                    console.print("[yellow]No Solidity version found. Defaulting to 0.8.10[/yellow]")
                    return "0.8.10"
        except Exception as e:
            console.print(f"[bold red]Error reading Solidity file: {e}[/bold red]")
            raise

    def set_solc_version(self):
        """
        Sets the Solidity compiler version using solc-select. Installs the version if necessary.
        """
        def run_solc_command(command, success_message, error_message):
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                console.print(f"[yellow]{error_message}: {result.stderr}[/yellow]")
                return False
            console.print(f"[bold green]{success_message}[/bold green]")
            return True

        console.print(f"[bold blue]Setting Solidity version to {self.solc_version}...[/bold blue]")
        if not run_solc_command(['solc-select', 'use', self.solc_version],
                                f"Successfully set Solidity version to {self.solc_version}.",
                                f"Error setting Solidity version to {self.solc_version}"):
            # Try installing if version is not available
            if f"'{self.solc_version}' must be installed":
                console.print(f"[yellow]Installing Solidity version {self.solc_version}...[/yellow]")
                if not run_solc_command(['solc-select', 'install', self.solc_version],
                                        f"Installed Solidity version {self.solc_version}.",
                                        f"Failed to install Solidity version {self.solc_version}"):
                    raise Exception("Failed to install and set Solidity version.")

    def run_analysis(self):
        """
        Run Slither analysis and return the result based on reentrancy detection or error code.
        """
        try:
            self.set_solc_version()

            console.print(f"[bold blue]Running Slither on {self.file_path}...[/bold blue]")
            detectors = "reentrancy-eth,reentrancy-no-eth,reentrancy-benign,reentrancy-events,reentrancy-unlimited-gas"
            result = subprocess.run(
                ['slither', self.file_path, "--detect", detectors, "--json", "-"],
                capture_output=True, text=True
            )

            # Print the output as JSON if possible
            self._pretty_print_output(result.stdout, result.stderr)

            if result.returncode in [0, 255]:
                return self._parse_for_reentrancy(result.stdout, result.stderr)

            console.print(f"[bold red]Slither returned code {result.returncode}: {result.stderr}[/bold red]")
            return -1

        except FileNotFoundError:
            console.print("[bold red]Error: Slither not found. Please install Slither.[/bold red]")
            return -2

        except Exception as e:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
            return -2

    @staticmethod
    def _pretty_print_output(stdout, stderr):
        """
        Pretty print stdout and stderr as JSON if possible, otherwise print them as raw output.

        :param stdout: Standard output from Slither.
        :param stderr: Standard error output from Slither.
        """
        try:
            # Attempt to parse and pretty print stdout as JSON
            stdout_json = json.loads(stdout)
            console.print("[bold green]Slither Output (stdout):[/bold green]")
            pretty_print(stdout_json)

        except json.JSONDecodeError:
            console.print("[bold red]Could not parse stdout as JSON. Printing raw output:[/bold red]")
            console.print(stdout)

        try:
            # Attempt to parse and pretty print stderr as JSON
            stderr_json = json.loads(stderr)
            console.print("[bold red]Slither Output (stderr):[/bold red]")
            pretty_print(stderr_json)

        except json.JSONDecodeError:
            console.print("[bold red]Could not parse stderr as JSON. Printing raw output:[/bold red]")
            console.print(stderr)

    def _parse_for_reentrancy(self, stdout, stderr):
        """
        Parse Slither output for reentrancy warnings in both stdout and stderr.

        :param stdout: The standard output from the Slither analysis.
        :param stderr: The standard error output from the Slither analysis.
        :return: 1 if reentrancy is detected, 0 if not, or -1 for unexpected errors.
        """
        output = (stdout + stderr).lower()
        if "reentrancy" in output:
            console.print(f"[green]Reentrancy vulnerability found in {self.file_path}[/green]\n")
            return 1
        else:
            console.print(f"[red]No reentrancy vulnerability found in {self.file_path}[/red]\n")
            return 0
