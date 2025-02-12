import json
from typing import List

import requests
from rich.console import Console
from web3 import Web3  # Ensure web3.py is installed

from src.classes.contract_fetcher.EtherscanFetcher import EtherscanFetcher


class DeFiProtocolFactory:
    """Factory class to return fetchers for different DeFi protocols with detailed debugging logs."""

    def __init__(self, fetcher: EtherscanFetcher) -> None:
        self.fetcher = fetcher
        self.logger = Console()

    def get_event_signature(self, contract_address: str) -> List[str]:
        """
        Compute the event signature (topic) dynamically using the keccak256 hash.
        """
        self.logger.log(f"[cyan]Fetching ABI for contract:[/cyan] [bold]{contract_address}[/bold]")
        abi = self.get_contract_abi(contract_address)

        if abi is None:
            self.logger.log(f"[red]Failed to retrieve ABI for contract:[/red] {contract_address}")
            return []

        self.logger.log(f"[yellow]Extracting event declarations from ABI for contract:[/yellow] {contract_address}")
        event_declarations = self.extract_event_declarations(abi)

        if not event_declarations:
            self.logger.log(f"[orange]No events found in ABI for contract:[/orange] {contract_address}")
            return []

        # Compute Keccak-256 hashes for each event
        event_signatures = [Web3.keccak(text=event).hex() for event in event_declarations]
        self.logger.log(f"[green]Computed event signatures:[/green] {event_signatures}")

        return event_signatures

    def get_contract_abi(self, contract_address: str):
        """
        Fetch the contract ABI from Etherscan.
        """
        url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={contract_address}&apikey={self.fetcher.api_key}"
        self.logger.log(f"[blue]Fetching ABI from:[/blue] {url}")

        response = requests.get(url)
        data = response.json()

        if data['status'] == '1':
            self.logger.log(f"[green]Successfully retrieved ABI for:[/green] {contract_address}")
            return json.loads(data['result'])
        else:
            self.logger.log(f"[red]Error fetching ABI for {contract_address}:[/red] {data['message']}")
            return None

    @staticmethod
    def extract_event_declarations(abi):
        """
        Extract event declarations from a contract ABI.
        """
        events = []
        for item in abi:
            if item.get("type") == "event":
                event_name = item["name"]
                params = ",".join([p['type'] for p in item["inputs"]])
                event_signature = f"{event_name}({params})"
                events.append(event_signature)

        return events

    def fetch_logs(self, contract_address: str) -> List[str]:
        """
        Fetch logs for a contract by computing event signatures dynamically.
        """
        event_signatures = self.get_event_signature(contract_address)
        if not event_signatures:
            self.logger.log(f"[orange]No valid event signatures found for contract:[/orange] {contract_address}")
            return []

        all_logs = []
        for event_signature in event_signatures:
            self.logger.log(f"[cyan]Fetching logs for {contract_address} with event {event_signature}[/cyan]")
            logs = self.fetcher.fetch_logs(contract_address, event_signature)
            if logs:
                self.logger.log(f"[green]Retrieved {len(logs)} logs for contract {contract_address}[/green]")
            else:
                self.logger.log(f"[orange]No logs found for {contract_address} with event {event_signature}[/orange]")
            all_logs.extend(logs)

        return self.fetcher.extract_addresses_from_logs(all_logs)

    def get_fetcher(self, protocol: str) -> List[str]:
        """Return the appropriate fetcher based on the DeFi protocol."""
        self.logger.log(f"[magenta]Fetching data for DeFi protocol:[/magenta] [bold]{protocol.capitalize()}[/bold]")
        protocol_mapping = {
            'uniswap': self.fetch_uniswap_contracts,
            'aave': self.fetch_aave_contracts,
            'compound': self.fetch_compound_contracts,
            'makerdao': self.fetch_makerdao_contracts,
            'curve': self.fetch_curve_contracts,
        }
        return protocol_mapping.get(protocol, lambda: [])()

    def fetch_uniswap_contracts(self) -> List[str]:
        """Uniswap V4: https://docs.uniswap.org/contracts/v4/deployments"""
        address = "0x6fF5693b99212Da76ad316178A184AB56D299b43"
        return self.fetch_logs(address)

    def fetch_aave_contracts(self) -> List[str]:
        """Aave V3: https://aave.com/docs/resources/addresses"""
        address = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
        return self.fetch_logs(address)

    def fetch_compound_contracts(self) -> List[str]:
        """Compound III: https://docs.compound.finance/#protocol-contracts"""
        address = "0xc3d688B66703497DAA19211EEdff47f25384cdc3"
        return self.fetch_logs(address)

    def fetch_makerdao_contracts(self) -> List[str]:
        """MakerDAO: https://etherscan.io/address/0x83f20f44975d03b1b09e64809b757c47f942beea"""
        address = "0x83F20F44975D03b1b09e64809B757c47f942BEeA"
        return self.fetch_logs(address)

    def fetch_curve_contracts(self) -> List[str]:
        """Curve: https://etherscan.io/address/0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB"""
        address = "0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB"
        return self.fetch_logs(address)
