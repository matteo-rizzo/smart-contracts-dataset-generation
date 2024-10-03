import re
import subprocess

from rich.console import Console

from src.classes.conversion.SolidityVersionManager import SolidityVersionManager


class SolcInstaller:
    def __init__(self, console: Console, version_manager: SolidityVersionManager):
        """
        Initialize SolcInstaller with a console for logging and a version manager for checking installed versions.

        :param console: Rich console instance for logging.
        :param version_manager: SolidityVersionManager instance for version handling.
        """
        self.console = console
        self.version_manager = version_manager

    def install_version(self, version: str) -> None:
        """
        Installs the specified solc version using solc-select if it's not already installed.

        :param version: The version of solc to install (e.g., '0.5.16').
        :raises RuntimeError: If installation fails.
        """
        if self.version_manager.is_version_installed(version):
            self.console.print(f"[bold green]Solc version {version} is already installed.[/bold green]")
            return

        self._log_and_execute(
            f"[yellow]Installing solc version {version}...[/yellow]",
            ['solc-select', 'install', version],
            success_message=f"[bold green]Successfully installed solc version {version}.[/bold green]",
            error_message=f"Installation failed for solc version {version}",
        )

    def set_version(self, version: str, operator: str = None, max_retries: int = 2) -> None:
        """
        Sets the specified solc version using solc-select. Installs the version if it's not already available.
        If the operator is '>=', it installs the latest stable version for the given base version.

        :param version: The version of solc to use (e.g., '0.5.16').
        :param operator: The operator used in the pragma statement (e.g., '>=' or '^'). Defaults to None.
        :param max_retries: Maximum number of retries in case setting or installing the version fails.
        :raises RuntimeError: If setting or installing the version fails after retries.
        """
        retries = 0
        while retries <= max_retries:
            try:
                if not self.version_manager.is_version_installed(version):
                    self.console.print(f"[yellow]Solc version {version} is not installed. Installing...[/yellow]")
                    self.install_version(version)

                self._use_version(version)

                if not self._validate_version(version):
                    raise RuntimeError(f"Failed to set solc version to {version}")

                self.console.print(f"[bold green]Successfully set solc version to {version}.[/bold green]")
                break
            except RuntimeError as e:
                retries += 1
                self.console.print(f"[bold red]Attempt {retries} to set version {version} failed: {e}[/bold red]")
                if retries > max_retries:
                    self.console.print(
                        f"[bold red]Maximum retry limit reached. Failed to set solc version to {version}.[/bold red]")
                    raise

    def _use_version(self, version: str) -> None:
        """
        Attempts to use the specified solc version using solc-select.

        :param version: The solc version to use.
        :raises RuntimeError: If switching to the version fails.
        """
        self._log_and_execute(
            f"[yellow]Switching to solc version {version}...[/yellow]",
            ['solc-select', 'use', version],
            success_message=f"[bold green]Successfully switched to solc version {version}.[/bold green]",
            error_message=f"Failed to switch to solc version {version}",
        )

    def _validate_version(self, version: str) -> bool:
        """
        Validates if the currently set solc version matches the desired version.

        :param version: The required version to validate.
        :return: True if the correct version is set, False otherwise.
        """
        try:
            current_version = self._clean_version(self._run_subprocess(['solc', '--version']).stdout)
            return current_version == version
        except (RuntimeError, ValueError) as e:
            self.console.print(f"[bold red]Validation of solc version failed: {e}[/bold red]")
            return False

    @staticmethod
    def _clean_version(version_output: str) -> str:
        """
        Extracts and cleans the version number from the solc --version output.

        :param version_output: The output string from 'solc --version' or 'solc-select use' command.
        :return: Cleaned version string (e.g., '0.5.16').
        :raises ValueError: If the version cannot be extracted from the output.
        """
        match = re.search(r"(\d+\.\d+\.\d+)", version_output)
        if match:
            return match.group(1)
        raise ValueError("Failed to extract a valid version from the output.")

    def _log_and_execute(self, start_message: str, command: list[str], success_message: str,
                         error_message: str) -> None:
        """
        Helper method to log and execute a subprocess command with error handling.

        :param start_message: The message to log before executing the command.
        :param command: The command to execute as a list of strings.
        :param success_message: The message to log on successful execution.
        :param error_message: The message to log on failed execution.
        :raises RuntimeError: If the command fails.
        """
        self.console.print(start_message)
        result = self._run_subprocess(command)
        if result.returncode == 0:
            self.console.print(success_message)
        else:
            raise RuntimeError(f"{error_message}: {result.stderr.strip()}")

    @staticmethod
    def _run_subprocess(command: list[str]) -> subprocess.CompletedProcess:
        """
        Runs a subprocess command and handles any errors that arise.

        :param command: The command to run as a list of strings.
        :return: The subprocess CompletedProcess object.
        :raises RuntimeError: If the subprocess fails.
        """
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Command '{' '.join(command)}' failed with error: {result.stderr.strip()}")
        return result
