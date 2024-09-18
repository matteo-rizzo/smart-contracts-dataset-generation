import logging
import os
from typing import List, Tuple

from rich.console import Console


class ContractReader:
    """
    Reads Solidity contracts from a directory.
    """

    def __init__(self, contracts_dir: str):
        self.contracts_dir = contracts_dir
        self.console = Console()
        self.logger = logging.getLogger("rich")

    def read_contracts(self) -> List[Tuple[str, str]]:
        """
        Reads Solidity contracts from the specified directory.

        Returns:
            List[Tuple[str, str]]: A list containing tuples of (filename, contract code).
        """
        contracts = []
        try:
            for filename in os.listdir(self.contracts_dir):
                if filename.endswith('.sol'):
                    filepath = os.path.join(self.contracts_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as file:
                        contract_code = file.read()
                        contracts.append((filename, contract_code))
                        self.logger.info(f"[bold green]Read contract:[/bold green] {filename}")
            return contracts
        except Exception as e:
            self.logger.error(f"[bold red]Error reading contracts:[/bold red] {e}")
            raise e
