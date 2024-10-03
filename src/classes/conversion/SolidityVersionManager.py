import subprocess

from rich.console import Console


class SolidityVersionManager:
    def __init__(self, console: Console):
        self.console = console

    def get_installed_versions(self) -> list[str]:
        """
        Retrieves the list of installed Solidity versions using solc-select.

        :return: A list of installed Solidity versions.
        :raises RuntimeError: If the solc-select command fails.
        """
        try:
            result = subprocess.run(['solc-select', 'versions'], capture_output=True, text=True, check=True)
            installed_versions = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return installed_versions
        except subprocess.CalledProcessError as e:
            self.console.print(f"[bold red]Failed to retrieve installed Solidity versions: {e.stderr}[/bold red]")
            raise RuntimeError(f"Error retrieving installed Solidity versions: {e.stderr}") from e

    def get_latest_stable_version(self, version: str) -> str:
        """
        Determines the latest stable version for a given version prefix, ensuring nightly builds are avoided.

        :param version: Base version extracted from pragma solidity (e.g., '0.5.16').
        :return: Latest stable version (e.g., '0.5.17').
        :raises: RuntimeError if no stable version is found or solc-select command fails.
        """
        try:
            # Run solc-select to get available versions
            result = subprocess.run(['solc-select', 'versions'], capture_output=True, text=True, check=True)

            # Extract the base version prefix (e.g., '0.5' from '0.5.16')
            base_version_prefix = version.rsplit('.', 1)[0]

            # Filter for stable versions matching the base prefix and excluding nightly builds
            stable_versions = [
                v for v in result.stdout.splitlines()
                if v.startswith(base_version_prefix) and 'nightly' not in v
            ]

            if not stable_versions:
                raise RuntimeError(f"No stable versions found for {version}")

            latest_version = stable_versions[-1]
            self.console.print(f"[green]Latest stable version for {version}: {latest_version}[/green]")
            return latest_version

        except subprocess.CalledProcessError as e:
            self.console.print(f"[bold red]Failed to retrieve Solidity versions: {e.stderr}[/bold red]")
            raise RuntimeError(f"Error retrieving Solidity versions: {e.stderr}") from e

        except Exception as e:
            self.console.print(f"[bold red]Unexpected error: {str(e)}[/bold red]")
            raise RuntimeError(f"Unexpected error while retrieving stable version for {version}") from e

    @staticmethod
    def get_next_version(version: str) -> str:
        """
        Determines the next version based on the current version.

        :param version: Current version (e.g., '0.5.16').
        :return: Next version (e.g., '0.5.17').
        :raises ValueError: If the version format is invalid.
        """
        version_parts = version.split('.')
        if len(version_parts) < 3:
            raise ValueError(f"Invalid version format: {version}")

        # Increment the patch version
        patch_version = int(version_parts[2]) + 1
        next_version = f"{version_parts[0]}.{version_parts[1]}.{patch_version}"
        return next_version

    def is_version_installed(self, version: str) -> bool:
        """
        Checks if the specified Solidity version is already installed.

        :param version: The version to check (e.g., '0.5.16').
        :return: True if the version is installed, False otherwise.
        """
        installed_versions = self.get_installed_versions()
        return version in installed_versions
