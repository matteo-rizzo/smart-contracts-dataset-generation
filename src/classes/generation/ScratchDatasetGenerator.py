import random

from rich.table import Table

from src.classes.generation.DatasetGenerator import DatasetGenerator
from src.classes.generation.VulnerabilityScenario import VulnerabilityScenario


class ScratchDatasetGenerator(DatasetGenerator):
    """
    Generates a dataset of Solidity contracts with injected vulnerabilities by creating contracts from scratch.
    """

    def __init__(self, scenarios_dir: str, num_contracts_per_scenario: int, vulnerability_type: str):
        """
        Initializes the generator with directories and sets up logging and the OpenAI client.

        :param scenarios_dir: Directory containing scenario JSON files.
        :type scenarios_dir: str
        :param num_contracts_per_scenario: Number of contracts to generate per scenario.
        :type num_contracts_per_scenario: int
        :param vulnerability_type: The type of vulnerability to inject (e.g., reentrancy, front-running).
        :type vulnerability_type: str
        """
        super().__init__(scenarios_dir, num_contracts_per_scenario, vulnerability_type)

        self.contract_types = [
            "auction", "token transfer", "escrow", "crowdfunding", "staking",
            "lending", "decentralized exchange", "NFT marketplace", "voting system",
            "reward distribution", "liquidity pool", "subscription service", "gaming contract",
            "charity donation", "royalty distribution", "time-locked vault", "payment splitter",
            "insurance contract", "betting contract", "prediction market", "bounty contract",
            "decentralized autonomous organization (DAO)", "flash loan contract", "yield farming",
            "governance contract", "token vesting contract", "stablecoin issuance",
            "decentralized identity verification", "carbon credit trading", "micro-lending platform",
            "social token platform", "automated investment strategies", "NFT minting contract",
            "NFT staking", "cross-chain token bridge", "asset-backed token issuance",
            "revenue sharing contract", "option trading", "synthetic asset issuance",
            "decentralized insurance", "data marketplace", "decentralized gaming platform",
            "digital rights management", "futures trading contract", "liquidity staking",
            "decentralized prediction protocol", "dynamic pricing contract", "fractional NFT ownership",
            "rental contract for digital assets", "crowdsourced security audit contract",
            "privacy-preserving contract", "reputation-based lending"
        ]

    def generate_dataset(self) -> None:
        """
        Generates the dataset by creating contracts from scratch based on random combinations and saving them.
        """

        total_scenarios = len(self.vulnerability_scenarios)

        for scenario_idx, scenario in enumerate(self.vulnerability_scenarios, start=1):
            scenario_name = scenario.name
            self.logger.info(f"[yellow]Processing scenario {scenario_idx}/{total_scenarios}:[/yellow] {scenario_name}")

            for contract_idx in range(1, self.num_contracts_per_scenario + 1):
                # Randomly select contract type, function name, and interaction type
                contract_type = random.choice(self.contract_types)

                # Generate the prompt
                prompt = self.generate_scratch_prompt(contract_type, scenario)

                # Display the generated prompt using Rich table
                prompt_table = Table(title="Generated Prompt")
                prompt_table.add_column("Prompt", justify="left", style="green", no_wrap=False)
                prompt_table.add_row(prompt)
                self.console.print(prompt_table)

                contract_filename = f"{contract_type}_{contract_idx}.sol"
                self.logger.info(
                    f"[yellow]  Generating contract {contract_idx}/{self.num_contracts_per_scenario}:[/yellow] {contract_filename}")

                # Get GPT response using the OpenAIClient
                try:
                    generated_contract = self.openai_client.get_gpt_response(prompt)

                    # Display the generated contract response using Rich table
                    response_table = Table(title=f"Generated Contract for {contract_filename}")
                    response_table.add_column("Contract", justify="left", style="magenta", no_wrap=False)
                    response_table.add_row(generated_contract)
                    self.console.print(response_table)

                    # Clean the response to remove ```solidity and other text
                    cleaned_contract = self.clean_gpt_response(generated_contract)

                    # Save the generated contract
                    self.save_modified_contract(contract_filename, scenario_name, cleaned_contract, contract_idx)

                except Exception as e:
                    self.logger.error(
                        f"[bold red]Error generating contract {contract_filename} with scenario {scenario_name}:[/bold red] {e}")
                    continue

    def generate_scratch_prompt(self, contract_type: str, scenario: VulnerabilityScenario) -> str:
        """
        Generates a prompt for GPT to create a Solidity contract from scratch with a specified vulnerability.

        :param contract_type: The type of contract to generate.
        :type contract_type: str
        :param scenario: The vulnerability scenario describing the type of attack.
        :type scenario: VulnerabilityScenario
        :return: A prompt for GPT to generate the contract with the specified vulnerability.
        :rtype: str
        """
        # Construct the scenario text to include in the prompt
        scenario_text = f"""### Scenario: {scenario.name}
                            **Description**: {scenario.scenario}
                            **Issue**: {scenario.issue}
                            **Example**:
                            ```solidity
                            {scenario.example}
                            ```"""

        prompt = f"""
        You are an expert Solidity smart contract developer with advanced knowledge in secure contract design and real-world contract functionality. Your task is to generate a realistic, fully functional Solidity {contract_type} smart contract that includes a specific {self.vulnerability_type} vulnerability. The contract must implement real-world functionalities relevant to its {contract_type}, along with the vulnerability. Follow the detailed instructions below to ensure the generated contract is practical and deployable in a live blockchain environment:

        1. **Contract Type and Purpose**:
           - Generate a {contract_type} smart contract that reflects real-world use cases.
           - Ensure the contract serves a clear purpose, and all features are related to real-world scenarios commonly seen in {contract_type} smart contracts.

        2. **Vulnerability Injection**:
           - Inject the {self.vulnerability_type} vulnerability into the contract while maintaining its core functionality. The vulnerability should be subtle and not placed in obvious spots. Ensure that it aligns with the following scenario:
             - **Vulnerability Scenario**: {scenario_text}
           - The vulnerability should be realistic and applicable to how the contract interacts with users, funds, or external contracts. It should be embedded within normal contract functionality.

        3. **Real-World Functionality**:
           - Implement real-world features that are essential to the {contract_type}:
             - **For Auction Contracts**: Include logic for bid placement, bid withdrawal, auction end times, and transferring funds to the winner.
             - **For Token Contracts**: Ensure compliance with relevant standards (ERC-20, ERC-721), including functions like `transfer`, `approve`, `burn`, and `mint`.
             - **For Crowdfunding Contracts**: Include mechanisms for accepting contributions, tracking milestones, and issuing refunds when necessary.
           - Avoid unnecessary or abstract logic. Every function should have a clear, practical purpose related to {contract_type}.

        4. **Contract Architecture**:
           - Design the contract with a logical flow that mirrors the requirements of a production-ready contract.
           - Use appropriate data structures (e.g., mappings, arrays, or structs) where necessary, and ensure that control flows (e.g., loops, conditionals) are relevant to the contract's real-world use.
           - Avoid adding redundant or overly complex logic that doesn't add real value to the contract's functionality.

        5. **Method Modifications and Integration of Vulnerabilities**:
           - Modify existing methods to introduce the {self.vulnerability_type} vulnerability while ensuring that all real-world functionality works as expected.
           - The vulnerability should integrate naturally with the contract's logic (e.g., affecting fund transfers, bid management, or token issuance).
           - Avoid making the vulnerability obvious through comments, naming, or placement in critical areas.

        6. **Core Functionality Retention**:
           - The contract must retain its full core functionality despite the vulnerability injection. Ensure it performs the expected actions related to {contract_type}, including user interaction and fund management.

        7. **Compilation and Real-World Usability**:
           - The contract must compile successfully with Solidity version X.X.X and be deployable on the Ethereum blockchain (or another specified chain).
           - Ensure that the contract is realistic, adhering to Solidity best practices, and is free of syntax errors, allowing interaction with blockchain services such as wallets or DeFi platforms.

        8. **Comments and Documentation**:
           - Provide comments explaining the core functionalities and their purpose, such as fund management, token transfers, or bid handling. Avoid explicitly commenting on the vulnerability itself.
           - The documentation should help other developers or auditors understand the intended functionality and use of each function without drawing attention to the vulnerability.

        9. **Output Requirements**:
            - Provide only the full Solidity contract code, including the injected vulnerability and all necessary real-world functionalities. Ensure the code is formatted correctly and adheres to Solidity best practices.
            - Do not include any extra text outside of the contract code itself.

        Please ensure the generated contract reflects real-world use cases and includes realistic logic for {contract_type} while subtly integrating the {self.vulnerability_type} vulnerability.
        """

        return prompt
