import argparse
import os
import time
from pathlib import Path

from rich import print
from rich.progress import Progress

# Predefined input and output directories
INPUT_DIR = os.path.join("dataset", "etherscan150", "source")
OUTPUT_DIR = os.path.join("logs", f"etherscan150_split_{time.time()}", "source")


def split_solidity_files_by_pragma(source_folder, output_folder):
    # Create a directory to save the split files
    split_folder = Path(output_folder)
    split_folder.mkdir(parents=True, exist_ok=True)

    # Iterate over all .sol files in the folder
    sol_files = list(Path(source_folder).rglob("*.sol"))

    if not sol_files:
        print(f"[red]No .sol files found in the source folder: {source_folder}[/red]")
        return

    with Progress() as progress:
        task = progress.add_task(f"[cyan]Processing {len(sol_files)} files...", total=len(sol_files))

        for sol_file in sol_files:
            with open(sol_file, "r", encoding="utf-8") as file:
                lines = file.readlines()

            # Find the indices where "pragma solidity" lines occur
            pragma_indices = [i for i, line in enumerate(lines) if line.strip().startswith("pragma solidity")]

            if len(pragma_indices) <= 1:
                # Skip if there is only one pragma version
                print(f"[yellow]Skipping {sol_file.name}, no need to split.[/yellow]")
                progress.advance(task)
                continue

            print(f"[green]Splitting {sol_file.name} into {len(pragma_indices)} files.[/green]")

            # Split the file based on these indices
            for i, start_idx in enumerate(pragma_indices):
                end_idx = pragma_indices[i + 1] if i + 1 < len(pragma_indices) else len(lines)
                new_file_content = ''.join(lines[start_idx:end_idx])

                # Skip splits containing 'interface' or 'library'
                if "interface" in new_file_content or "library" in new_file_content:
                    print(f"[yellow]Skipping split {i + 1} of {sol_file.name} (contains interface/library).[/yellow]")
                    continue

                # Check if the split contains a contract
                if "contract" not in new_file_content:
                    print(f"[yellow]Skipping split {i + 1} of {sol_file.name} (no contract found).[/yellow]")
                    continue

                # Write each valid split part to a new file
                new_file_name = f"{sol_file.stem}_split_{i + 1}.sol"
                new_file_path = split_folder / new_file_name

                with open(new_file_path, "w", encoding="utf-8") as new_file:
                    new_file.write(new_file_content)

                print(f"[blue]Created: {new_file_path}[/blue]")

            progress.advance(task)

    print("[bold green]Splitting complete.[/bold green]")


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Split Solidity files by pragma version.")
    parser.add_argument("--input_folder", type=str, default=INPUT_DIR, help="Folder containing Solidity files.")
    parser.add_argument("--output_folder", type=str, default=OUTPUT_DIR, help="Folder to save the split files.")

    args = parser.parse_args()

    # Call the function with the provided input and output folders
    split_solidity_files_by_pragma(args.input_folder, args.output_folder)
