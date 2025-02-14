import requests
from typing import List, Optional

from src.classes.config.EtherscanConfig import EtherscanConfig
from src.classes.contract_fetcher.RateLimiter import RateLimiter


class EtherscanLogsFetcher:
    """
    A class dedicated to fetching logs from Etherscan and extracting contract addresses,
    using the Etherscan v2 API endpoints if configured.
    """

    def __init__(self, config: EtherscanConfig) -> None:
        """
        Initializes the logs fetcher with API key, rate limiter, console, base URL, and chain ID.

        The base URL can be overridden in the configuration (e.g., to use a v2 endpoint).
        """
        self.api_key = config.api_key
        self.retry_limit = config.retry_limit
        self.rate_limiter = RateLimiter(config.rate_limit)
        self.console = config.console
        # Allow overriding the base URL; default to the v2 endpoint.
        self.base_url = getattr(config, "base_url", "https://api.etherscan.io/v2/api")
        self.chain_id = getattr(config, "chain_id", 1)

    @staticmethod
    def parse_timestamp(ts: str) -> int:
        """
        Converts a timestamp string to an integer.
        Handles both hexadecimal (0x prefixed) and decimal formats.
        """
        if ts.startswith("0x"):
            return int(ts, 16)
        return int(ts)

    def fetch_logs(
        self,
        contract_address: str,
        event_signature: str,
        from_block: str = "0",
        to_block: str = "latest",
        topic1: Optional[str] = None,
        page: int = 1,
        offset: int = 5000,
        retry_count: int = 0,
    ) -> List[dict]:
        """
        Fetch logs for a given contract address and event signature.
        Logs are sorted in descending order by timestamp.

        :param contract_address: The target contract address.
        :param event_signature: The event signature (topic0) to filter logs.
        :param from_block: Starting block number.
        :param to_block: Ending block number.
        :param topic1: Optional additional topic filter (topic1).
        :param page: Page number for pagination.
        :param offset: Number of records per page.
        :param retry_count: Current retry count (used internally for recursion).
        :return: A list of log dictionaries.
        """
        try:
            self.rate_limiter.rate_limit()
            # Build URL for the v2 API endpoint with the new query parameters.
            url = (
                f"{self.base_url}?chainid={self.chain_id}&module=logs&action=getLogs"
                f"&fromBlock={from_block}&toBlock={to_block}&address={contract_address}"
                f"&topic0={event_signature}"
            )
            if topic1 is not None:
                url += f"&topic0_1_opr=and&topic1={topic1}"
            url += f"&page={page}&offset={offset}&apikey={self.api_key}"
            response = requests.get(url)
            self.rate_limiter.increment_request_count()
            data = response.json()

            if data.get('status') == '1':
                logs = data.get('result', [])
                logs.sort(key=lambda log: self.parse_timestamp(log.get('timeStamp', '0')), reverse=True)
                return logs
            else:
                self.console.log(
                    f"[bold red]Error fetching logs for {contract_address}: {data.get('message', 'No message provided')}[/bold red]"
                )
                return []
        except requests.RequestException as e:
            if retry_count < self.retry_limit:
                self.console.log(f"[yellow]Retrying... ({retry_count + 1}/{self.retry_limit})[/yellow]")
                return self.fetch_logs(contract_address, event_signature, from_block, to_block, topic1, page, offset, retry_count + 1)
            self.console.log(
                f"[bold red]Network error for {contract_address} after {self.retry_limit} retries: {e}[/bold red]"
            )
            return []

    def extract_addresses_from_logs(self, logs: List[dict]) -> List[str]:
        """
        Extract unique contract addresses from the log data.

        :param logs: List of log dictionaries.
        :return: A list of unique contract addresses.
        """
        extracted_addresses = set()

        for log in logs:
            if not isinstance(log, dict):
                self.console.log(f"[yellow]Skipping malformed log entry: {log}[/yellow]")
                continue

            if 'data' in log and isinstance(log['data'], str) and len(log['data']) >= 66:
                try:
                    address = "0x" + log['data'][26:66]
                    extracted_addresses.add(address)
                except Exception as e:
                    self.console.log(f"[red]Error extracting from 'data': {e}, log: {log}[/red]")
            elif 'topics' in log and isinstance(log['topics'], list) and len(log['topics']) > 1:
                try:
                    address = "0x" + log['topics'][1][-40:]
                    extracted_addresses.add(address)
                except Exception as e:
                    self.console.log(f"[red]Error extracting from 'topics': {e}, log: {log}[/red]")
            else:
                self.console.log(f"[yellow]No valid address found in log: {log}[/yellow]")

        return list(extracted_addresses)
