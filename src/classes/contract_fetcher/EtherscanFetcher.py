import json
import os
import re
from typing import List, Optional

import requests
from rich.progress import track

from src.classes.config.EtherscanConfig import EtherscanConfig
from src.classes.contract_fetcher.RateLimiter import RateLimiter


class EtherscanFetcher:
    """
    A class for fetching contract data and logs from Etherscan using its API.
    """

    PRAGMA_PATTERN = re.compile(
        r"pragma\s+solidity\s+([^\s;]+);",  # Captures everything after 'pragma solidity'
        re.MULTILINE | re.IGNORECASE
    )

    def __init__(self, config: EtherscanConfig) -> None:
        """
        Initializes the EtherscanFetcher with API key, directory setup, and rate limiter.

        :param config: The configuration object containing API key, save directory, rate limit, and retry settings.
        :type config: EtherscanConfig
        """
        self.api_key = config.api_key
        self.save_dir = config.save_dir
        self.retry_limit = config.retry_limit
        self.rate_limiter = RateLimiter(config.rate_limit)
        self.console = config.console  # Use Rich console from the config
        self.logger = config.logger

        # Create the directory if it doesn't exist
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        self.console.log(f"[green]Initialized EtherscanFetcher with save directory: {self.save_dir}[/green]")

    @staticmethod
    def parse_timestamp(ts: str) -> int:
        """
        Convert a timestamp string to an integer.
        If the timestamp is in hexadecimal (starts with '0x'), convert using base 16.
        """
        if ts.startswith("0x"):
            return int(ts, 16)
        return int(ts)

    def fetch_logs(self, contract_address: str, event_signature: str, retry_count: int = 0) -> List[dict]:
        """
        Fetch logs from Etherscan using the contract address and event signature.
        The returned logs are sorted so that the most recent log (by timestamp) comes first.

        :param contract_address: The contract address to fetch logs for.
        :param event_signature: The event signature (topic) for the logs.
        :param retry_count: Number of retries attempted in case of failure (default is 0).
        :return: A list of log dictionaries, sorted by timeStamp in descending order.
        """
        try:
            self.rate_limiter.rate_limit()
            url = (
                f"https://api.etherscan.io/api?module=logs&action=getLogs"
                f"&fromBlock=0&toBlock=latest&address={contract_address}"
                f"&topic0={event_signature}&apikey={self.api_key}"
            )
            response = requests.get(url)
            self.rate_limiter.increment_request_count()
            data = response.json()

            if data['status'] == '1':
                logs = data['result']
                # Sort logs by timeStamp (convert from string to int) in descending order
                logs.sort(key=lambda log: self.parse_timestamp(log['timeStamp']), reverse=True)
                return logs
            else:
                self.console.log(f"[bold red]Error fetching logs for {contract_address}: {data['message']}[/bold red]")
                return []
        except requests.RequestException as e:
            if retry_count < self.retry_limit:
                self.console.log(f"[yellow]Retrying... ({retry_count + 1}/{self.retry_limit})[/yellow]")
                return self.fetch_logs(contract_address, event_signature, retry_count + 1)
            self.console.log(
                f"[bold red]Network error while fetching logs for {contract_address} after {self.retry_limit} retries: {e}[/bold red]"
            )
            return []

    @staticmethod
    def extract_addresses_from_logs(logs: List[dict]) -> List[str]:
        """
        Extract contract addresses from log data, handling different log structures.

        :param logs: A list of log dictionaries (sorted by timeStamp).
        :return: A list of unique extracted contract addresses.
        """
        extracted_addresses = set()  # Use a set to store unique addresses

        for log in logs:
            # Ensure log is a dictionary before processing
            if not isinstance(log, dict):
                print(f"⚠️ Skipping malformed log entry: {log}")
                continue

            # Check if 'data' exists and is valid
            if 'data' in log and isinstance(log['data'], str) and len(log['data']) >= 66:
                try:
                    address = "0x" + log['data'][26:66]  # Extract from 'data' field
                    extracted_addresses.add(address)
                except Exception as e:
                    print(f"❌ Error extracting from 'data': {e}, log: {log}")

            # If 'data' is missing or malformed, try extracting from 'topics'
            elif 'topics' in log and isinstance(log['topics'], list) and len(log['topics']) > 1:
                try:
                    address = "0x" + log['topics'][1][-40:]  # Extract last 40 hex chars (address)
                    extracted_addresses.add(address)
                except Exception as e:
                    print(f"❌ Error extracting from 'topics': {e}, log: {log}")

            else:
                print(f"⚠️ No valid address found in log: {log}")

        return list(extracted_addresses)  # Convert set to list for uniqueness

    def fetch_verified_contract(self, contract_address: str, retry_count: int = 0) -> Optional[dict]:
        """
        Fetch the verified source code of a contract from Etherscan.
        """
        try:
            self.rate_limiter.rate_limit()
            url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={contract_address}&apikey={self.api_key}"
            self.console.log(f"[cyan]Fetching contract from Etherscan for address: {contract_address}[/cyan]")
            response = requests.get(url)
            self.rate_limiter.increment_request_count()
            data = response.json()

            if str(data['status']) == '1' and data['result'][0]['SourceCode']:
                self.console.log(
                    f"[green]Contract verified and source code found for address: {contract_address}[/green]"
                )
                return data['result'][0]
            else:
                self.console.log(
                    f"[bold red]Error fetching contract or missing source code for {contract_address}[/bold red]"
                )
                return None
        except requests.RequestException as e:
            if retry_count < self.retry_limit:
                self.console.log(f"[yellow]Retrying... ({retry_count + 1}/{self.retry_limit})[/yellow]")
                return self.fetch_verified_contract(contract_address, retry_count + 1)
            self.console.log(
                f"[bold red]Network error while fetching contract {contract_address} after {self.retry_limit} retries: {e}[/bold red]"
            )
            return None

    def extract_pragma_versions(self, source_code: str) -> List[str]:
        """
        Extracts all Solidity versions from the pragma statements in the source code.

        :param source_code: Solidity source code.
        :type source_code: str
        :return: A list of all extracted pragma versions.
        :rtype: List[str]
        """
        return [match.group(1) for match in self.PRAGMA_PATTERN.finditer(source_code)]

    def save_contract_as_sol(self, contract_address: str, contract_data: dict) -> None:
        """
        Save the fetched contract's source code as a .sol file only if it has at least one `pragma solidity 0.8.*`.
        """
        try:
            source_code = contract_data['SourceCode']
            contract_name = contract_data['ContractName']

            if source_code.startswith('{{') and source_code.endswith('}}'):
                # Multi-file contracts (JSON formatted)
                source_code = source_code[1:-1]  # Remove extra {}
                multi_file_code = json.loads(source_code)['sources']

                for file_name, file_content in multi_file_code.items():
                    file_name = file_name.split(os.sep)[-1]
                    if not file_name.endswith('.sol'):
                        file_name += '.sol'

                    file_text = file_content['content']
                    pragma_versions = self.extract_pragma_versions(file_text)

                    # Check if at least one pragma is 0.8.*
                    if not any(version.startswith("0.8.") for version in pragma_versions):
                        self.console.log(
                            f"[yellow]Skipping {contract_address} - {file_name} (no 0.8.* pragma found).[/yellow]"
                        )
                        continue

                    file_path = os.path.join(self.save_dir, f"{contract_address}_{file_name}")
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(file_text)
                    self.console.log(f"[green]Saved: {file_path}[/green]")

            else:
                # Single-file contracts
                pragma_versions = self.extract_pragma_versions(source_code)

                # Debug: Print pragma versions found
                self.console.log(f"[cyan]Found pragma versions in {contract_address}: {pragma_versions}[/cyan]")

                # Check if at least one pragma is 0.8.*
                if not any(version.startswith("0.8.") for version in pragma_versions):
                    self.console.log(f"[yellow]Skipping {contract_address} (no 0.8.* pragma found).[/yellow]")
                    return

                file_path = os.path.join(self.save_dir, f"{contract_address}_{contract_name}.sol")
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(source_code)
                self.console.log(f"[green]Saved: {file_path}[/green]")

        except (json.JSONDecodeError, OSError) as e:
            self.console.log(f"[bold red]Error saving contract {contract_address} as a .sol file:[/bold red] {e}")

    def fetch_and_save_contracts(self, contract_addresses: List[str],
                                 target_verified_count: int = 1000) -> int:
        """
        Fetch and save verified contracts until the target number is reached.
        """
        verified_contracts_saved = 0

        # If you want to sort the contract addresses based on some metadata (like creation date),
        # you would need that information (e.g. by calling a different API endpoint).
        # For now, we'll process them in the order provided.
        # If your list is unsorted and you wish to reverse the order, you can simply do:
        # contract_addresses = list(reversed(contract_addresses))

        for idx, address in track(enumerate(contract_addresses), description="Checking contracts..."):
            if verified_contracts_saved >= target_verified_count:
                self.console.log(f"[bold green]Target of {target_verified_count} contracts reached![/bold green]")
                break

            self.console.log(f"[cyan]Checking contract {idx + 1}/{len(contract_addresses)}: {address}[/cyan]")
            contract_data = self.fetch_verified_contract(address)

            if contract_data:
                self.save_contract_as_sol(address, contract_data)
                verified_contracts_saved += 1
                self.console.log(
                    f"[green]Verified contract saved: {address} (Total saved: {verified_contracts_saved})[/green]"
                )
            else:
                self.console.log(f"[red]Skipping contract {address}, not verified or error occurred[/red]")

        self.console.log(f"[bold green]Finished: Saved {verified_contracts_saved} verified contracts[/bold green]")
        return verified_contracts_saved
