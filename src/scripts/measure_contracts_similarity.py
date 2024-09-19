import os

from rich.console import Console

from src.classes.SolidityComparator import SolidityComparator

# Console for rich output
console = Console()


def main() -> None:
    """
    Main function that serves as the entry point of the program.
    It prompts the user for the folder path, initializes the comparator,
    and runs the comparison process.
    """
    folder_path = os.path.join("solidity_contracts")

    # Ensure the folder exists
    if not os.path.isdir(folder_path):
        console.print("[red]The provided folder path does not exist or is invalid.[/red]")
        return

    # Create the comparator and run the comparison process
    comparator = SolidityComparator(folder_path)
    comparator.run()


if __name__ == "__main__":
    main()
