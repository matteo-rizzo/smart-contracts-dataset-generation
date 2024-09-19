import csv
import os

from rich.console import Console
from rich.table import Table

from src.classes.SlytherAnalyzer import SlitherAnalyzer

# Initialize a rich console for pretty printing
console = Console()


def main():
    """
    Main function that iterates over all Solidity files in the given folder, runs Slither analysis on each,
    and produces a CSV file indicating whether each contract is vulnerable to reentrancy.
    """

    folder_path = os.path.join("solidity_contracts")

    if not os.path.isdir(folder_path):
        console.print(f"[bold red]Error: {folder_path} is not a valid directory.[/bold red]")
        return

    # Prepare the CSV output
    output_csv = "slither_analysis_results.csv"
    csv_data = [("File", "Reentrancy Detected")]

    # Create a Rich table for better terminal visualization
    table = Table(title="Slither Analysis Results")
    table.add_column("File", justify="left", style="cyan", no_wrap=True)
    table.add_column("Reentrancy Detected", justify="center", style="magenta")

    # Find all Solidity files in the folder
    solidity_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.sol')]

    if not solidity_files:
        console.print(f"[bold yellow]No Solidity files found in {folder_path}[/bold yellow]")
        return

    # Iterate over all found Solidity files and run Slither analysis using the SlitherAnalyzer class
    for solidity_file in solidity_files:
        analyzer = SlitherAnalyzer(solidity_file)
        reentrancy_found = analyzer.run_analysis()

        # Add the result to both CSV data and the Rich table
        csv_data.append((solidity_file, reentrancy_found))
        table.add_row(solidity_file, str(reentrancy_found))

    # Write the results to a CSV file
    with open(output_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)

    # Display the table with rich
    console.print(table)

    console.print(f"[bold green]Analysis complete. Results saved in {output_csv}[/bold green]")


if __name__ == "__main__":
    main()
