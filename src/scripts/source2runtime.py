import os

from rich.console import Console
from rich.panel import Panel

from src.classes.conversion.FileManager import FileManager
from src.classes.conversion.RuntimeGenerator import RuntimeGenerator
from src.classes.conversion.SolcInstaller import SolcInstaller
from src.classes.conversion.SolidityVersionManager import SolidityVersionManager


def main():
    # Initialize the console for rich logging
    console = Console()

    # Display the start message using a rich panel
    console.print(Panel("[bold yellow]Starting Solidity runtime bytecode generation...[/bold yellow]"))

    # Initialize the required components
    version_manager = SolidityVersionManager(console)
    installer = SolcInstaller(console, version_manager)
    file_manager = FileManager(console)

    # Initialize the RuntimeGenerator with updated dependencies, no need for a separate compiler
    bytecode_generator = RuntimeGenerator(console, installer, file_manager)

    # Define paths for the contracts folder and output folder
    contracts_folder = os.path.join("dataset", "etherscan150", "source")
    output_folder = os.path.join("dataset", "etherscan150", "runtime")

    # Generate the runtime bytecode for all Solidity files in the contracts folder
    bytecode_generator.generate_runtime_bytecode(contracts_folder, output_folder)

    # Display the completion message using a rich panel
    console.print(Panel("[bold green]Bytecode generation completed successfully![/bold green]"))


if __name__ == "__main__":
    main()
