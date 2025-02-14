import json
from typing import Optional, List, Dict

import requests
from rich.console import Console
from web3 import Web3


class ContractABIProvider:
    """
    Service for fetching a contract's ABI from Etherscan and extracting event signatures.
    """

    def __init__(self, api_key: str, logger: Optional[Console] = None) -> None:
        self.api_key = api_key
        self.logger = logger if logger is not None else Console()

    def get_contract_abi(self, contract_address: str) -> Optional[List[Dict]]:
        """
        Fetch the contract ABI from Etherscan.

        :param contract_address: Address of the contract.
        :return: ABI as a list of dictionaries if successful, otherwise None.
        """
        url = (
            f"https://api.etherscan.io/api?module=contract&action=getabi"
            f"&address={contract_address}&apikey={self.api_key}"
        )
        self.logger.log(f"[blue]Fetching ABI from:[/blue] {url}")
        try:
            response = requests.get(url)
            data = response.json()

            if data.get("status") == "1":
                self.logger.log(f"[green]Successfully retrieved ABI for:[/green] {contract_address}")
                return json.loads(data["result"])
            else:
                self.logger.log(f"[red]Error fetching ABI for {contract_address}:[/red] {data.get('message')}")
                return None
        except Exception as e:
            self.logger.log(f"[red]Exception fetching ABI for {contract_address}: {e}[/red]")
            return None

    @staticmethod
    def extract_event_declarations(abi: List[Dict]) -> List[str]:
        """
        Extract event declarations from the contract ABI.

        :param abi: Contract ABI.
        :return: List of event declaration strings.
        """
        events = []
        for item in abi:
            if item.get("type") == "event":
                event_name = item.get("name")
                inputs = item.get("inputs", [])
                params = ",".join(inp.get("type", "") for inp in inputs)
                event_declaration = f"{event_name}({params})"
                events.append(event_declaration)
        return events

    def get_event_signatures(self, contract_address: str) -> List[str]:
        """
        Retrieve event signatures for a contract by fetching its ABI and computing
        the keccak256 hash of each event declaration.

        :param contract_address: Address of the contract.
        :return: List of event signature strings.
        """
        self.logger.log(f"[cyan]Fetching ABI for contract:[/cyan] [bold]{contract_address}[/bold]")
        abi = self.get_contract_abi(contract_address)
        if not abi:
            self.logger.log(f"[red]Failed to retrieve ABI for contract: {contract_address}[/red]")
            return []

        self.logger.log(f"[yellow]Extracting event declarations from ABI for contract:[/yellow] {contract_address}")
        event_declarations = self.extract_event_declarations(abi)
        if not event_declarations:
            self.logger.log(f"[orange]No events found in ABI for contract: {contract_address}[/orange]")
            return []

        event_signatures = [Web3.keccak(text=event).hex() for event in event_declarations]
        self.logger.log(f"[green]Computed event signatures:[/green] {event_signatures}")
        return event_signatures
