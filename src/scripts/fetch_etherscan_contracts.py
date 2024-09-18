import logging

from rich import Console

from src.classes.contract_fetcher.Config import Config
from src.classes.contract_fetcher.DeFiProtocolFactory import DeFiProtocolFactory
from src.classes.contract_fetcher.EtherscanFetcher import EtherscanFetcher

# Initialize rich console for better logging
console = Console()
logging.basicConfig(level=logging.INFO)


def main() -> None:
    try:
        if not Config.API_KEY:
            console.log("[bold red]API Key not found. Please add it to the .env file.[/bold red]")
            return

        # Initialize Etherscan fetcher
        etherscan_fetcher = EtherscanFetcher(Config)
        protocol_factory = DeFiProtocolFactory(etherscan_fetcher)

        # Fetch contract addresses from different protocols
        protocols = ['uniswap', 'aave', 'compound', 'makerdao', 'curve']
        contract_addresses = []
        for protocol in protocols:
            contract_addresses += protocol_factory.get_fetcher(protocol)

        console.log(
            f"[bold green]Fetched {len(contract_addresses)} contract addresses from DeFi protocols.[/bold green]")

        # Fetch and save verified contracts
        etherscan_fetcher.fetch_and_save_verified_contracts(contract_addresses, target_verified_count=1000)
        console.log(f"[bold green]Success! Fetched and saved contracts from multiple DeFi protocols.[/bold green]")

    except Exception as e:
        console.log(f"[bold red]An unexpected error occurred: {e}[/bold red]")


if __name__ == "__main__":
    main()
