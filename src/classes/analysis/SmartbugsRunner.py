import os
import subprocess
from datetime import datetime
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel

console = Console()


class SmartBugsRunner:
    def __init__(self, contracts_folder: str, output_folder: str, analyzers: List[str], timeout: int,
                 processes: int = 1, mem_limit: str = "4g", cpu_quota: Optional[int] = None,
                 output_format: str = "json") -> None:
        """
        Initialize the SmartBugsRunner with the given configuration.

        :param contracts_folder: Path to the folder containing the smart contract files (.sol or .hex)
        :param output_folder: Path where analysis results will be stored
        :param analyzers: List of tools (analyzers) to be used for analysis (e.g., mythril, slither)
        :param timeout: Timeout for each analysis in seconds
        :param processes: Number of processes to run in parallel (default: 1)
        :param mem_limit: Memory limit for Docker containers (e.g., "4g" for 4 gigabytes)
        :param cpu_quota: CPU limit for Docker containers (optional, e.g., 100000 for 1 CPU)
        :param output_format: Format for output results (either "json" or "sarif")
        """
        self.contracts_folder = contracts_folder
        self.output_folder = self.create_timestamped_output_folder(output_folder)
        self.analyzers = analyzers
        self.timeout = timeout
        self.processes = processes
        self.mem_limit = mem_limit
        self.cpu_quota = cpu_quota
        self.output_format = output_format

    @staticmethod
    def create_timestamped_output_folder(base_output_folder: str) -> str:
        """
        Create a timestamped folder for storing analysis results.

        :param base_output_folder: Base folder path where the results will be saved
        :return: Full path of the timestamped output folder
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_folder = os.path.join(base_output_folder, f"smartbugs_results_{timestamp}")
        os.makedirs(timestamped_folder, exist_ok=True)
        console.print(f"[bold green]Created output folder: {timestamped_folder}[/bold green]")
        return timestamped_folder

    def get_smart_contracts(self) -> List[str]:
        """
        Collect all Solidity (.sol) and bytecode (.hex) files from the contracts folder.

        :return: List of smart contract file paths to be analyzed
        """
        contracts = [os.path.join(self.contracts_folder, file) for file in os.listdir(self.contracts_folder)
                     if file.endswith(".sol") or file.endswith(".hex")]
        if not contracts:
            console.print(f"[bold red]No smart contract files found in {self.contracts_folder}.[/bold red]")
            return []
        console.print(f"[bold green]Found {len(contracts)} contract(s) to analyze.[/bold green]")
        return contracts

    def run_smartbugs_subprocess(self, analyzer: str, contract_files: List[str]) -> None:
        """
        Run SmartBugs as a subprocess with the given analyzer and contract files.

        :param analyzer: The analysis tool to use (e.g., mythril, slither)
        :param contract_files: List of contract files to analyze
        """
        try:
            # Construct the SmartBugs command
            command = [
                "/Users/matteorizzo/bin/smartbugs/smartbugs",  # Path to the SmartBugs executable
                "-t", analyzer,  # Tool to be used for the analysis
                "-f", ",".join(contract_files),  # Files to analyze (comma-separated)
                "--processes", str(self.processes),  # Number of processes to run in parallel
                "--timeout", str(self.timeout),  # Timeout for each task
                "--mem-limit", self.mem_limit,  # Memory limit for Docker containers
                "--results", self.output_folder  # Output folder for the results
            ]

            # Append options for output format and CPU quota if needed
            if self.output_format == "sarif":
                command.append("--sarif")  # Write results in SARIF format
            elif self.output_format == "json":
                command.append("--json")  # Write results in JSON format

            if self.cpu_quota:
                command.extend(["--cpu-quota", str(self.cpu_quota)])  # CPU quota for Docker

            # Print the command being executed
            console.print(f"[cyan]Running SmartBugs with command: {' '.join(command)}[/cyan]")

            # Execute the command using subprocess
            result = subprocess.run(command, capture_output=True, text=True)

            # Print the output and errors, if any
            console.print(f"[green]SmartBugs output:[/green]\n{result.stdout}")
            if result.stderr:
                console.print(f"[red]SmartBugs errors:[/red]\n{result.stderr}")

        except Exception as e:
            console.print(f"[bold red]Error running SmartBugs for {contract_files} with {analyzer}: {e}[/bold red]")

    def run(self) -> None:
        """
        Main function to execute the SmartBugs analysis on the collected smart contracts.
        """
        contracts = self.get_smart_contracts()
        if not contracts:
            return

        # For each contract and analyzer, run the analysis
        for contract in contracts:
            console.print(Panel(f"[cyan]Analyzing contract: {contract}[/cyan]", expand=False))
            for analyzer in self.analyzers:
                self.run_smartbugs_subprocess(analyzer, [contract])

        console.print(f"[bold green]Analysis completed! Results stored in {self.output_folder}[/bold green]")
