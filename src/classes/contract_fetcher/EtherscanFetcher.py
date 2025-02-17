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
    A class for fetching verified contract data and saving source code from Etherscan.
    Supports the Etherscan v2 endpoint.
    """

    PRAGMA_PATTERN = re.compile(
        r"pragma\s+solidity\s+([^\s;]+);",
        re.MULTILINE | re.IGNORECASE
    )

    def __init__(self, config: EtherscanConfig) -> None:
        """
        Initializes the fetcher with API key, directories, rate limiter, console, and base URL.
        The base URL and chain ID can be overridden via configuration.
        """
        self.api_key = config.api_key
        self.save_dir = config.save_dir
        self.retry_limit = config.retry_limit
        self.rate_limiter = RateLimiter(config.rate_limit)
        self.console = config.console  # Rich console from config
        self.logger = config.logger

        # Use configurable base URL and chain ID (defaulting to v2 endpoint and chainid=1)
        self.base_url = getattr(config, "base_url", "https://api.etherscan.io/v2/api")
        self.chain_id = getattr(config, "chain_id", 1)

        # Ensure save directory exists
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        self.console.log(f"[green]Initialized EtherscanFetcher with save directory: {self.save_dir}[/green]")

    def fetch_verified_contract(self, contract_address: str, retry_count: int = 0) -> Optional[dict]:
        """
        Fetch the verified source code of a contract.

        Skips the contract if the compiler version is lower than 0.8.*

        :param contract_address: The contract address to query.
        :param retry_count: Current retry count (used internally).
        :return: Contract data if verified, available, and has a compatible compiler version; else None.
        """
        try:
            self.rate_limiter.rate_limit()
            url = (
                f"{self.base_url}?chainid={self.chain_id}&module=contract&action=getsourcecode"
                f"&address={contract_address}&apikey={self.api_key}"
            )
            self.console.log(f"[cyan]Fetching contract for address: {contract_address}[/cyan]")
            response = requests.get(url)
            self.rate_limiter.increment_request_count()
            data = response.json()

            status = str(data.get('status', '0'))
            result = data.get('result', [])
            if status in ['1', "True", "OK"] and result and result[0].get('SourceCode'):
                compiler_version = result[0].get('CompilerVersion', '')
                # Check if the compiler version starts with "0.8." or "v0.8."
                if not (compiler_version.startswith("0.8.") or compiler_version.startswith("v0.8.")):
                    self.console.log(
                        f"[yellow]Skipping {contract_address}: Compiler version {compiler_version} is lower than 0.8.*.[/yellow]"
                    )
                    return None
                self.console.log(f"[green]Contract verified for address: {contract_address}[/green]")
                return result[0]
            else:
                self.console.log(
                    f"[bold red]Error fetching contract or missing source code for {contract_address}: {data.get('message', 'No message provided')}[/bold red]"
                )
                return None
        except requests.RequestException as e:
            if retry_count < self.retry_limit:
                self.console.log(f"[yellow]Retrying... ({retry_count + 1}/{self.retry_limit})[/yellow]")
                return self.fetch_verified_contract(contract_address, retry_count + 1)
            self.console.log(
                f"[bold red]Network error for {contract_address} after {self.retry_limit} retries: {e}[/bold red]"
            )
            return None

    def extract_pragma_versions(self, source_code: str) -> List[str]:
        """
        Extract Solidity version(s) from the pragma statement in the source code.
        """
        return [match.group(1) for match in self.PRAGMA_PATTERN.finditer(source_code)]

    def save_contract_as_sol(self, contract_address: str, contract_data: dict) -> bool:
        """
        Save the contract source code as a .sol file if it uses a compatible Solidity version.
        Returns True if the contract is saved; False if skipped or an error occurs.
        """
        try:
            source_code = contract_data['SourceCode']
            contract_name = contract_data['ContractName']
            saved = False

            if source_code.startswith('{{') and source_code.endswith('}}'):
                # Handle multi-file contracts (JSON formatted)
                # Remove extra curly braces and parse the JSON.
                source_code = source_code[1:-1]
                multi_file_code = json.loads(source_code)['sources']

                for file_name, file_content in multi_file_code.items():
                    file_name = file_name.split(os.sep)[-1]
                    if not file_name.endswith('.sol'):
                        file_name += '.sol'

                    file_text = file_content['content']
                    pragma_versions = self.extract_pragma_versions(file_text)

                    # Only save if at least one pragma starts with "0.8."
                    if not any(version.startswith("0.8.") for version in pragma_versions):
                        self.console.log(
                            f"[yellow]Skipping {contract_address} - {file_name} (no 0.8.* pragma found).[/yellow]"
                        )
                        continue

                    file_path = os.path.join(self.save_dir, f"{contract_address}_{file_name}")
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(file_text)
                    self.console.log(f"[green]Saved: {file_path}[/green]")
                    saved = True

                return saved
            else:
                # Single-file contract
                pragma_versions = self.extract_pragma_versions(source_code)
                self.console.log(f"[cyan]Found pragma versions for {contract_address}: {pragma_versions}[/cyan]")

                if not any(version.startswith("0.8.") for version in pragma_versions):
                    self.console.log(f"[yellow]Skipping {contract_address} (no 0.8.* pragma found).[/yellow]")
                    return False

                file_path = os.path.join(self.save_dir, f"{contract_address}_{contract_name}.sol")
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(source_code)
                self.console.log(f"[green]Saved: {file_path}[/green]")
                return True
        except (json.JSONDecodeError, OSError) as e:
            self.console.log(f"[bold red]Error saving contract {contract_address}: {e}[/bold red]")
            return False

    def fetch_and_save_contracts(self, contract_addresses: List[str], target_verified_count: int) -> int:
        """
        Iterates through contract addresses, fetches verified contracts, and saves them until the target count is reached.

        :param contract_addresses: List of contract addresses to check.
        :param target_verified_count: The desired number of verified contracts to save.
        :return: The number of contracts saved.
        """
        verified_contracts_saved = 0

        for idx, address in track(enumerate(contract_addresses), description="Checking contracts..."):
            if verified_contracts_saved >= target_verified_count:
                self.console.log(f"[bold green]Target of {target_verified_count} contracts reached![/bold green]")
                break

            self.console.log(f"[cyan]Checking contract {idx + 1}/{len(contract_addresses)}: {address}[/cyan]")
            contract_data = self.fetch_verified_contract(address)

            if contract_data:
                saved = self.save_contract_as_sol(address, contract_data)
                if saved:
                    verified_contracts_saved += 1
                    self.console.log(
                        f"[green]Verified contract saved: {address} (Total saved: {verified_contracts_saved})[/green]"
                    )
                else:
                    self.console.log(f"[yellow]Contract {address} skipped (no valid pragma found).[/yellow]")
            else:
                self.console.log(f"[red]Skipping {address} (not verified or an error occurred).[/red]")

        self.console.log(f"[bold green]Finished: Saved {verified_contracts_saved} verified contracts[/bold green]")
        return verified_contracts_saved
