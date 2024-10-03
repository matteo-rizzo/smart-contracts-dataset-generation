from pathlib import Path


class FileManager:
    def __init__(self, console):
        self.console = console

    @staticmethod
    def find_solidity_files(folder: str) -> list[Path]:
        """
        Finds all Solidity (.sol) files in the given folder.

        :param folder: Path to search for .sol files.
        :return: List of Path objects representing .sol files.
        """
        return list(Path(folder).rglob("*.sol"))

    @staticmethod
    def split_file_by_pragma(sol_file: Path) -> dict:
        """
        Splits a Solidity file based on pragma directives and returns a dictionary mapping each pragma version to
        the corresponding contract code.

        :param sol_file: Path to the Solidity file.
        :return: Dictionary where keys are pragma versions and values are contract code.
        """
        sections = {}
        current_pragma = None
        current_code = []

        with open(sol_file, 'r') as f:
            for line in f:
                line = line.strip()

                # Detect pragma directives
                if line.startswith("pragma solidity"):
                    # Save the previous section if applicable
                    if current_pragma is not None and current_code:
                        sections[current_pragma] = '\n'.join(current_code).strip()

                    # Start a new section for the new pragma version
                    current_pragma = line
                    current_code = []
                else:
                    # Collect the contract/library code under the current pragma
                    if current_pragma:
                        current_code.append(line)

            # Add the last section after the loop completes
            if current_pragma is not None and current_code:
                sections[current_pragma] = '\n'.join(current_code).strip()

        if not sections:
            raise ValueError(f"No pragma directives found in {sol_file}")

        return sections
