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
                 output_format: str = "json", runtime: bool = False) -> None:
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
        :param runtime: Boolean indicating whether to analyze runtime bytecode instead of Solidity source code
        """
        self.contracts_folder = contracts_folder
        self.output_folder = self.create_timestamped_output_folder(output_folder)
        self.analyzers = analyzers
        self.timeout = timeout
        self.processes = processes
        self.mem_limit = mem_limit
        self.cpu_quota = cpu_quota
        self.output_format = output_format
        self.runtime = runtime

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

    def run_smartbugs_subprocess(self, analyzer: str) -> None:
        """
        Run SmartBugs as a subprocess with the given analyzer on all files in the contracts folder.

        :param analyzer: The analysis tool to use (e.g., mythril, slither)
        """
        try:
            # Use "*.sol" for source code and "*.hex" for runtime bytecode
            file_extension = "*.hex" if self.runtime else "*.sol"
            contract_files_pattern = os.path.join(self.contracts_folder, file_extension)

            # Construct the SmartBugs command
            command = [
                "/Users/matteorizzo/bin/smartbugs/smartbugs",  # Path to the SmartBugs executable
                "-t", analyzer,  # Tool to be used for the analysis
                "-f", contract_files_pattern,  # File pattern (e.g., samples/*.sol or samples/*.hex)
                "--processes", str(self.processes),  # Number of processes to run in parallel
                "--timeout", str(self.timeout),  # Timeout for each task
                "--mem-limit", self.mem_limit,  # Memory limit for Docker containers
                "--results", self.output_folder  # Output folder for the results
            ]

            # If the runtime flag is enabled, add the runtime option
            if self.runtime:
                command.append("--runtime")

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
            console.print(f"[bold red]Error running SmartBugs with {analyzer}: {e}[/bold red]")

    def run(self) -> None:
        """
        Main function to execute the SmartBugs analysis on the whole folder.
        """
        # Run the analysis for all contracts in the folder for each analyzer
        for analyzer in self.analyzers:
            self.run_smartbugs_subprocess(analyzer)

        console.print(f"[bold green]Analysis completed! Results stored in {self.output_folder}[/bold green]")
