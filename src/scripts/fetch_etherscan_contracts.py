import argparse
import traceback
from typing import List

import pandas as pd

from src.classes.config.EtherscanConfig import EtherscanConfig
from src.classes.contract_fetcher.ContractABIProvider import ContractABIProvider
from src.classes.contract_fetcher.DeFiProtocolFactory import DeFiProtocolFactory
from src.classes.contract_fetcher.EtherscanFetcher import EtherscanFetcher
from src.classes.contract_fetcher.EtherscanLogsFetcher import EtherscanLogsFetcher

TARGET_VERIFIED_COUNT = 100000


def collect_contract_addresses(protocol_factory: DeFiProtocolFactory) -> List[str]:
    """
    Collects contract addresses from all defined DeFi protocols.

    :param protocol_factory: A DeFiProtocolFactory instance with protocol mappings.
    :return: A flat list of contract addresses.
    """
    return [
        address
        for protocol in protocol_factory.protocol_mapping
        for address in protocol_factory.get_fetcher(protocol)
    ]


def read_addresses_from_csv(csv_file: str) -> List[str]:
    """
    Reads contract addresses from a CSV file.

    :param csv_file: Path to the CSV file.
    :return: A list of contract addresses.
    """
    try:
        df = pd.read_csv(csv_file)
        if 'ContractAddress' not in df.columns:
            raise ValueError("CSV file must contain a column named 'ContractAddress'")
        return df['ContractAddress'].dropna().astype(str).tolist()
    except Exception as e:
        raise RuntimeError(f"Error reading CSV file: {e}")


def main() -> None:
    """
    Fetch contract addresses from multiple DeFi protocols or a CSV file and save verified contracts.
    """
    parser = argparse.ArgumentParser(description="Fetch contract data from DeFi protocols or a CSV file.")
    parser.add_argument("--csv", default="asset/export-verified-contractaddress-opensource-license.csv", type=str,
                        help="Path to a CSV file containing contract addresses.")
    args = parser.parse_args()

    # Initialize configuration (loads API key, logger, and console)
    config = EtherscanConfig()

    # Validate API key presence
    if not config.api_key:
        config.console.log("[bold red]API Key not found. Please add it to the .env file.[/bold red]")
        return

    try:
        # Initialize necessary components
        abi_provider = ContractABIProvider(config.api_key)
        logs_fetcher = EtherscanLogsFetcher(config)
        protocol_factory = DeFiProtocolFactory(logs_fetcher, abi_provider)

        # Decide how to get contract addresses
        if args.csv:
            contract_addresses = read_addresses_from_csv(args.csv)
            config.console.log(
                f"[bold green]Read {len(contract_addresses)} contract addresses from CSV file.[/bold green]")
        else:
            contract_addresses = collect_contract_addresses(protocol_factory)
            config.console.log(
                f"[bold green]Fetched {len(contract_addresses)} contract addresses from DeFi protocols.[/bold green]")

        # Fetch and save verified contracts
        etherscan_fetcher = EtherscanFetcher(config)
        etherscan_fetcher.fetch_and_save_contracts(contract_addresses, target_verified_count=TARGET_VERIFIED_COUNT)
        config.console.log("[bold green]Success! Fetched and saved contracts.[/bold green]")

    except Exception as e:
        config.console.log(f"[bold red]An unexpected error occurred: {e}[/bold red]")
        config.console.log(traceback.format_exc())


if __name__ == "__main__":
    main()
