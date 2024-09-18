import json
import logging
import os
from typing import List, Optional

import requests
from rich.console import Console
from rich.progress import track

from src.classes.contract_fetcher.Config import Config
from src.classes.contract_fetcher.RateLimiter import RateLimiter

# Initialize rich console for better logging
console = Console()
logging.basicConfig(level=logging.INFO)


class EtherscanFetcher:
    """
    A class for fetching contract data and logs from Etherscan using its API.
    """

    def __init__(self, config: Config) -> None:
        """
        Initializes the EtherscanFetcher with API key and directory setup.

        :param config: The configuration object containing API key, save directory, and rate limit.
        :type config: Config
        """
        self.api_key = config.API_KEY
        self.save_dir = config.SAVE_DIR
        self.rate_limiter = RateLimiter(config.RATE_LIMIT)

        # Create the directory if it doesn't exist
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        console.log(f"[green]Initialized EtherscanFetcher with save directory: {self.save_dir}[/green]")

    def fetch_logs(self, contract_address: str, event_signature: str, retry_count: int = 0) -> List[str]:
        """
        Fetch logs from Etherscan using the contract address and event signature.

        :param contract_address: The contract address to fetch logs for.
        :type contract_address: str
        :param event_signature: The event signature (topic) for the logs.
        :type event_signature: str
        :param retry_count: The number of retries attempted in case of failure (default is 0).
        :type retry_count: int
        :return: A list of log data entries.
        :rtype: List[str]
        """
        try:
            self.rate_limiter.rate_limit()
            url = f"https://api.etherscan.io/api?module=logs&action=getLogs&fromBlock=0&toBlock=latest&address={contract_address}&topic0={event_signature}&apikey={self.api_key}"
            response = requests.get(url)
            self.rate_limiter.increment_request_count()
            data = response.json()

            if data['status'] == '1':
                return [log['data'] for log in data['result']]
            else:
                console.log(f"[bold red]Error fetching logs for {contract_address}: {data['message']}[/bold red]")
                return []
        except requests.RequestException as e:
            if retry_count < Config.RETRY_LIMIT:
                console.log(f"[yellow]Retrying... ({retry_count + 1}/{Config.RETRY_LIMIT})[/yellow]")
                return self.fetch_logs(contract_address, event_signature, retry_count + 1)
            console.log(
                f"[bold red]Network error while fetching logs for {contract_address} after {Config.RETRY_LIMIT} retries: {e}[/bold red]")
            return []

    @staticmethod
    def extract_addresses_from_logs(logs: List[str]) -> List[str]:
        """
        Extract contract addresses from log data.

        :param logs: The list of logs containing contract data.
        :type logs: List[str]
        :return: A list of extracted contract addresses.
        :rtype: List[str]
        """
        return ["0x" + log[26:66] for log in logs]

    def fetch_verified_contract(self, contract_address: str, retry_count: int = 0) -> Optional[dict]:
        """
        Fetch the verified source code of a contract from Etherscan.

        :param contract_address: The contract address to fetch the verified source code for.
        :type contract_address: str
        :param retry_count: The number of retries attempted in case of failure (default is 0).
        :type retry_count: int
        :return: A dictionary containing the contract's source code and metadata, or None if not verified.
        :rtype: Optional[dict]
        """
        try:
            self.rate_limiter.rate_limit()
            url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={contract_address}&apikey={self.api_key}"
            console.log(f"[cyan]Fetching contract from Etherscan for address: {contract_address}[/cyan]")
            response = requests.get(url)
            self.rate_limiter.increment_request_count()
            data = response.json()

            if data['status'] == '1' and data['result'][0]['SourceCode']:
                console.log(f"[green]Contract verified and source code found for address: {contract_address}[/green]")
                return data['result'][0]
            else:
                console.log(
                    f"[bold red]Error fetching or contract not verified for {contract_address}[/bold red]: {data['message']}")
                return None
        except requests.RequestException as e:
            if retry_count < Config.RETRY_LIMIT:
                console.log(f"[yellow]Retrying... ({retry_count + 1}/{Config.RETRY_LIMIT})[/yellow]")
                return self.fetch_verified_contract(contract_address, retry_count + 1)
            console.log(
                f"[bold red]Network error while fetching contract {contract_address} after {Config.RETRY_LIMIT} retries: {e}[/bold red]")
            return None

    def save_contract_as_sol(self, contract_address: str, contract_data: dict) -> None:
        """
        Save the fetched contract's source code as a .sol file.

        :param contract_address: The contract address of the source code being saved.
        :type contract_address: str
        :param contract_data: The contract data containing the source code and contract name.
        :type contract_data: dict
        :raises json.JSONDecodeError: If there is an error decoding multi-file source code.
        :raises OSError: If there is an error saving the file to disk.
        """
        try:
            source_code = contract_data['SourceCode']
            contract_name = contract_data['ContractName']

            if source_code.startswith('{{') and source_code.endswith('}}'):
                # Handle multi-file contracts
                source_code = source_code[1:-1]
                multi_file_code = json.loads(source_code)

                for file_name, file_content in multi_file_code.items():
                    file_path = os.path.join(self.save_dir, f"{contract_address}_{file_name}.sol")
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(file_content['content'])
                    console.log(f"[green]Saved multi-file contract: {file_path}[/green]")
            else:
                # Handle single-file contracts
                file_path = os.path.join(self.save_dir, f"{contract_address}_{contract_name}.sol")
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(source_code)
                console.log(f"[green]Saved single file: {file_path}[/green]")

        except (json.JSONDecodeError, OSError) as e:
            console.log(f"[bold red]Error saving contract {contract_address} as a .sol file:[/bold red] {e}")

    def fetch_and_save_verified_contracts(self, contract_addresses: List[str],
                                          target_verified_count: int = 1000) -> int:
        """
        Fetch and save verified contracts until the target number is reached.

        :param contract_addresses: A list of contract addresses to fetch and save.
        :type contract_addresses: List[str]
        :param target_verified_count: The target number of verified contracts to save (default is 1000).
        :type target_verified_count: int
        :return: The total number of verified contracts saved.
        :rtype: int
        """
        verified_contracts_saved = 0

        for idx, address in track(enumerate(contract_addresses), description="Checking contracts..."):
            if verified_contracts_saved >= target_verified_count:
                console.log(f"[bold green]Target of {target_verified_count} contracts reached![/bold green]")
                break

            console.log(f"[cyan]Checking contract {idx + 1}/{len(contract_addresses)}: {address}[/cyan]")
            contract_data = self.fetch_verified_contract(address)

            if contract_data:
                self.save_contract_as_sol(address, contract_data)
                verified_contracts_saved += 1
                console.log(
                    f"[green]Verified contract saved: {address} (Total saved: {verified_contracts_saved})[/green]")
            else:
                console.log(f"[red]Skipping contract {address}, not verified or error occurred[/red]")

        console.log(f"[bold green]Finished: Saved {verified_contracts_saved} verified contracts[/bold green]")
        return verified_contracts_saved
