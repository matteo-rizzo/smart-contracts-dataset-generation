import traceback
from typing import List

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


def main() -> None:
    """
    Fetch contract addresses from multiple DeFi protocols and save verified contracts.
    """
    # Initialize configuration (loads API key, logger, and console)
    config = EtherscanConfig()

    # Validate API key presence
    if not config.api_key:
        config.console.log(
            "[bold red]API Key not found. Please add it to the .env file.[/bold red]"
        )
        return

    try:
        # Initialize the logs fetcher and protocol factory
        abi_provider = ContractABIProvider(config.api_key)
        logs_fetcher = EtherscanLogsFetcher(config)
        protocol_factory = DeFiProtocolFactory(logs_fetcher, abi_provider)

        # Collect contract addresses from all protocols
        contract_addresses: List[str] = collect_contract_addresses(protocol_factory)
        config.console.log(
            f"[bold green]Fetched {len(contract_addresses)} contract addresses from DeFi protocols.[/bold green]"
        )

        # Fetch and save verified contracts
        etherscan_fetcher = EtherscanFetcher(config)
        etherscan_fetcher.fetch_and_save_contracts(
            contract_addresses, target_verified_count=TARGET_VERIFIED_COUNT
        )
        config.console.log(
            "[bold green]Success! Fetched and saved contracts from multiple DeFi protocols.[/bold green]"
        )

    except Exception as e:
        config.console.log(f"[bold red]An unexpected error occurred: {e}[/bold red]")
        config.console.log(traceback.format_exc())


if __name__ == "__main__":
    main()
