from typing import List

from src.classes.contract_fetcher.EtherscanFetcher import EtherscanFetcher


class DeFiProtocolFactory:
    """Factory class to return fetchers for different DeFi protocols."""

    def __init__(self, fetcher: EtherscanFetcher) -> None:
        self.fetcher = fetcher

    def get_fetcher(self, protocol: str) -> List[str]:
        """Return the appropriate fetcher based on the DeFi protocol."""
        protocol_mapping = {
            'uniswap': self.fetch_uniswap_contracts,
            'aave': self.fetch_aave_contracts,
            'compound': self.fetch_compound_contracts,
            'makerdao': self.fetch_makerdao_contracts,
            'curve': self.fetch_curve_contracts,
        }
        return protocol_mapping.get(protocol, lambda: [])()

    def fetch_uniswap_contracts(self) -> List[str]:
        factory_contract = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
        event_signature = "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
        logs = self.fetcher.fetch_logs(factory_contract, event_signature)
        return self.fetcher.extract_addresses_from_logs(logs)

    def fetch_aave_contracts(self) -> List[str]:
        lending_pool_contract = "0x7d2c2f823f6a9f2a7ca287db3f14dbf2191e96eb"
        event_signature = "0xd7aadaae5cda6a7f6a760b7a1ff8f4c8e200f6f6f017bfeee30d9cf964c8ef93"
        logs = self.fetcher.fetch_logs(lending_pool_contract, event_signature)
        return self.fetcher.extract_addresses_from_logs(logs)

    def fetch_compound_contracts(self) -> List[str]:
        comptroller_contract = "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b"
        event_signature = "0x41a01d29b1d19d4f5a5a7df5e0107e2373fe321f3f08d0c134ae5b1b4a0007bd"
        logs = self.fetcher.fetch_logs(comptroller_contract, event_signature)
        return self.fetcher.extract_addresses_from_logs(logs)

    def fetch_makerdao_contracts(self) -> List[str]:
        cdp_manager_contract = "0x1de1f800aadef09a4e060a0b371c33eb9f31ce03"
        event_signature = "0x2ca5101d91d4a07d431f06026c6c1042a747c65e0626265afde9fddf0f7d3ef8"
        logs = self.fetcher.fetch_logs(cdp_manager_contract, event_signature)
        return self.fetcher.extract_addresses_from_logs(logs)

    def fetch_curve_contracts(self) -> List[str]:
        gauge_controller_contract = "0xFA712EE4788C042e2B7BB55E6cb8ec569C4530c1"
        event_signature = "0x12c6caac97a3aa20bdb42e31d6b93f7a418d170504d89ed43e620db37c3b5083"
        logs = self.fetcher.fetch_logs(gauge_controller_contract, event_signature)
        return self.fetcher.extract_addresses_from_logs(logs)
