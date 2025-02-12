from src.classes.config.EtherscanConfig import EtherscanConfig
from src.classes.contract_fetcher.DeFiProtocolFactory import DeFiProtocolFactory
from src.classes.contract_fetcher.EtherscanFetcher import EtherscanFetcher


def main() -> None:
    # Initialize EtherscanConfig (loads API key, setup logger and console)
    config = EtherscanConfig()

    try:
        # Check if API Key is properly set
        if not config.api_key:
            config.console.log("[bold red]API Key not found. Please add it to the .env file.[/bold red]")
            return

        # Initialize Etherscan fetcher with the config
        etherscan_fetcher = EtherscanFetcher(config)
        protocol_factory = DeFiProtocolFactory(etherscan_fetcher)

        # Fetch contract addresses from different DeFi protocols
        protocols = ['uniswap', 'aave', 'compound', 'makerdao', 'curve']
        contract_addresses = []
        for protocol in protocols:
            contract_addresses += protocol_factory.get_fetcher(protocol)

        config.console.log(
            f"[bold green]Fetched {len(contract_addresses)} contract addresses from DeFi protocols.[/bold green]")

        # Fetch and save verified contracts
        etherscan_fetcher.fetch_and_save_contracts(contract_addresses, target_verified_count=100)
        config.console.log(
            f"[bold green]Success! Fetched and saved contracts from multiple DeFi protocols.[/bold green]")

    except Exception as e:
        config.console.log(f"[bold red]An unexpected error occurred: {e}[/bold red]")


if __name__ == "__main__":
    main()
