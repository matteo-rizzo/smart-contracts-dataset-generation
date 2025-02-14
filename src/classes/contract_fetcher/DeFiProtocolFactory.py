from typing import List

from rich.console import Console

from src.classes.contract_fetcher.ContractABIProvider import ContractABIProvider
from src.classes.contract_fetcher.EtherscanLogsFetcher import EtherscanLogsFetcher


class DeFiProtocolFactory:
    """
    Factory class to return fetchers for different DeFi protocols.
    Combines ABI extraction (via ContractABIProvider) with log fetching.
    Supports checking multiple addresses per protocol.
    """

    def __init__(
        self,
        logs_fetcher: EtherscanLogsFetcher,
        abi_provider: ContractABIProvider
    ) -> None:
        self.logs_fetcher = logs_fetcher
        self.abi_provider = abi_provider
        # Use the same logger/console for consistency.
        self.logger: Console = logs_fetcher.console

        self.protocol_mapping = {
            "sushiswap": self.fetch_sushiswap_contracts,
            "balancer": self.fetch_balancer_contracts,
            "yearn": self.fetch_yearn_contracts,
            "synthetix": self.fetch_synthetix_contracts,
            "frax": self.fetch_frax_contracts,
            "liquity": self.fetch_liquity_contracts,
            "uniswap": self.fetch_uniswap_contracts,
            "aave": self.fetch_aave_contracts,
            "compound": self.fetch_compound_contracts,
            "makerdao": self.fetch_makerdao_contracts,
            "curve": self.fetch_curve_contracts,
        }

    def fetch_logs_for_contract(self, contract_address: str) -> List[str]:
        """
        Fetch logs for a contract by computing event signatures dynamically.

        :param contract_address: Address of the contract.
        :return: List of extracted contract addresses from logs.
        """
        event_signatures = self.abi_provider.get_event_signatures(contract_address)
        if not event_signatures:
            self.logger.log(
                f"[orange]No valid event signatures found for contract:[/orange] {contract_address}"
            )
            return []

        all_logs = []
        for event_signature in event_signatures:
            self.logger.log(
                f"[cyan]Fetching logs for {contract_address} with event {event_signature}[/cyan]"
            )
            logs = self.logs_fetcher.fetch_logs(contract_address, event_signature)
            if logs:
                self.logger.log(
                    f"[green]Retrieved {len(logs)} logs for contract {contract_address}[/green]"
                )
            else:
                self.logger.log(
                    f"[orange]No logs found for {contract_address} with event {event_signature}[/orange]"
                )
            all_logs.extend(logs)

        return self.logs_fetcher.extract_addresses_from_logs(all_logs)

    def fetch_contracts_from_addresses(self, addresses: List[str]) -> List[str]:
        """
        Helper function to iterate through a list of addresses and fetch logs for each.

        :param addresses: List of contract addresses.
        :return: Combined list of extracted addresses.
        """
        results = []
        for address in addresses:
            results.extend(self.fetch_logs_for_contract(address))
        return results

    def get_fetcher(self, protocol: str) -> List[str]:
        """
        Return the contract addresses for the given DeFi protocol.

        :param protocol: Name of the protocol.
        :return: List of contract addresses.
        """
        self.logger.log(
            f"[magenta]Fetching data for DeFi protocol:[/magenta] [bold]{protocol.capitalize()}[/bold]"
        )
        fetch_method = self.protocol_mapping.get(protocol.lower())
        if fetch_method:
            return fetch_method()
        self.logger.log(f"[red]No fetcher found for protocol: {protocol}[/red]")
        return []

    def fetch_uniswap_contracts(self) -> List[str]:
        """Uniswap V4: https://docs.uniswap.org/contracts/v4/deployments"""
        addresses = [
            "0x000000000004444c5dc75cB358380D2e3dE08A90",
            "0xd1428ba554f4c8450b763a0b2040a4935c63f06c",
            "0xbd216513d74c8cf14cf4747e6aaa6420ff64ee9e",
            "0x52f0e24d1c21c8a0cb1e5a5dd6198556bd9e1203",
            "0x7ffe42c4a5deea5b0fec41c94c136cf115597227",
            "0x66a9893cc07d91d95644aedd05d03f95e1dba8af"
        ]
        return self.fetch_contracts_from_addresses(addresses)

    def fetch_aave_contracts(self) -> List[str]:
        """Aave V3: https://aave.com/docs/resources/addresses"""
        addresses = [
            "0x64b761D848206f447Fe2dd461b0c635Ec39EbB27",
            "0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e",
            "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
        ]
        return self.fetch_contracts_from_addresses(addresses)

    def fetch_compound_contracts(self) -> List[str]:
        """Compound III: https://docs.compound.finance/#protocol-contracts"""
        addresses = [
            "0xc3d688B66703497DAA19211EEdff47f25384cdc3",
            "0x528c57A87706C31765001779168b42f24c694E1b",
            "0x285617313887d43256F852cAE0Ee4de4b68D45B0",
            "0x1EC63B5883C3481134FD50D5DAebc83Ecd2E8779"
        ]
        return self.fetch_contracts_from_addresses(addresses)

    def fetch_makerdao_contracts(self) -> List[str]:
        """MakerDAO: https://etherscan.io/address/0x83f20f44975d03b1b09e64809b757c47f942beea"""
        addresses = [
            "0x83F20F44975D03b1b09e64809B757c47f942BEeA"
        ]
        return self.fetch_contracts_from_addresses(addresses)

    def fetch_curve_contracts(self) -> List[str]:
        """Curve: https://etherscan.io/address/0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB"""
        addresses = [
            "0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB"
        ]
        return self.fetch_contracts_from_addresses(addresses)

    def fetch_sushiswap_contracts(self) -> List[str]:
        """SushiSwap Router: https://etherscan.io/address/0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"""
        addresses = [
            "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"
        ]
        return self.fetch_contracts_from_addresses(addresses)

    def fetch_balancer_contracts(self) -> List[str]:
        """Balancer V2 Vault: https://etherscan.io/address/0xBA12222222228d8Ba445958a75a0704d566BF2C8"""
        addresses = [
            "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
            # Additional Balancer addresses can be added here
        ]
        return self.fetch_contracts_from_addresses(addresses)

    def fetch_yearn_contracts(self) -> List[str]:
        """Yearn Finance Vault: https://etherscan.io/address/0xca12459a931643BF28388c67639b3F352fe9e5Ce"""
        addresses = [
            "0xca12459a931643BF28388c67639b3F352fe9e5Ce"
        ]
        return self.fetch_contracts_from_addresses(addresses)

    def fetch_synthetix_contracts(self) -> List[str]:
        """Synthetix Proxy: https://etherscan.io/address/0xefaca6fc316b3b2aa6c55ff5e02a62a85d4391e8?ref=blog.synthetix.io"""
        addresses = [
            "0xefaCa6Fc316B3B2Aa6c55FF5E02a62A85d4391e8"
        ]
        return self.fetch_contracts_from_addresses(addresses)

    def fetch_frax_contracts(self) -> List[str]:
        """Frax Finance: https://etherscan.io/address/0xf8caed1943b15b877d7105b9906a618c154f69e8"""
        addresses = [
            "0xf8caEd1943B15B877D7105B9906a618c154f69E8"
        ]
        return self.fetch_contracts_from_addresses(addresses)

    def fetch_liquity_contracts(self) -> List[str]:
        """Liquity: https://etherscan.io/address/0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2"""
        addresses = [
            "0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2"
        ]
        return self.fetch_contracts_from_addresses(addresses)
