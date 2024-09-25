import logging
import os

from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler


class EtherscanConfig:
    """
    A configuration class to manage Etherscan-related settings, such as the API key,
    saving directory, and request limits.
    """

    def __init__(self):
        """
        Initializes the configuration by loading environment variables and setting up
        default settings like the save directory and rate limits.
        Also sets up logging with rich's Console for better output.
        """
        load_dotenv()  # Load environment variables from .env file
        self.api_key = os.getenv('ETHERSCAN_API_KEY')
        if not self.api_key:
            raise ValueError("Etherscan API key not found. Please set ETHERSCAN_API_KEY in your .env file.")

        self.save_dir = "solidity_contracts"
        self.rate_limit = 5  # 5 requests per second
        self.retry_limit = 3  # Number of retries for failed requests

        # Initialize rich console for better logging
        self.console = Console()
        self.logger = self.setup_logging()

    def setup_logging(self):
        """
        Configures logging to use RichHandler for better console output.
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[RichHandler(console=self.console)]
        )
        return logging.getLogger("EtherscanConfig")

    def display(self):
        """
        Displays the current configuration settings.
        """
        self.logger.info("Etherscan Configuration:")
        self.console.print(f"[bold green]Etherscan API Key:[/bold green] {self.api_key}")
        self.console.print(f"[bold green]Save Directory:[/bold green] {self.save_dir}")
        self.console.print(f"[bold green]Rate Limit:[/bold green] {self.rate_limit} requests per second")
        self.console.print(f"[bold green]Retry Limit:[/bold green] {self.retry_limit} attempts")
