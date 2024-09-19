import random

from rich.table import Table

from src.classes.generation.ContractReader import ContractReader
from src.classes.generation.DatasetGenerator import DatasetGenerator
from src.classes.generation.VulnerabilityScenario import VulnerabilityScenario


class EtherscanDatasetGenerator(DatasetGenerator):
    """
    Generates a dataset of Solidity contracts with injected vulnerabilities by modifying existing contracts.
    """

    def __init__(self, contracts_dir: str, scenarios_dir: str, num_contracts_per_scenario: int,
                 vulnerability_type: str):
        """
        Initializes the generator with directories and sets up logging and the OpenAI client.

        :param contracts_dir: Directory containing Solidity contracts.
        :type contracts_dir: str
        :param scenarios_dir: Directory containing scenario JSON files.
        :type scenarios_dir: str
        :param num_contracts_per_scenario: Number of contracts to generate per scenario.
        :type num_contracts_per_scenario: int
        :param vulnerability_type: The type of vulnerability to inject (e.g., reentrancy, front-running).
        :type vulnerability_type: str
        """
        super().__init__(scenarios_dir, num_contracts_per_scenario, vulnerability_type)
        self.contracts_dir = contracts_dir

        # Read contracts
        self.contract_reader = ContractReader(self.contracts_dir)
        self.contracts = self.contract_reader.read_contracts()

    def generate_vulnerability_prompt(self, contract_code: str, scenario: VulnerabilityScenario) -> str:
        """
        Generates a prompt for GPT to inject a specified vulnerability into the given Solidity contract using a specific scenario.

        :param contract_code: The Solidity contract code.
        :type contract_code: str
        :param scenario: The vulnerability scenario describing the type of attack.
        :type scenario: VulnerabilityScenario
        :return: A prompt for GPT to inject the specified vulnerability into the contract.
        :rtype: str
        """
        scenario_text = f"""### Scenario: {scenario.name}
                            **Description**: {scenario.scenario}
                            **Issue**: {scenario.issue}
                            **Example**:
                            ```solidity
                            {scenario.example}
                            ```"""

        # Construct the prompt
        prompt = f"""
        You are a Solidity smart contract security expert with a deep understanding of both secure and insecure patterns in smart contract development. 
        The following is a Solidity smart contract, which is functioning correctly and securely in its current state:

        {contract_code}

        Your task is to subtly modify this contract by injecting a specific vulnerability based on the provided {self.vulnerability_type} scenario. The details of the vulnerability and its relevant scenario are described below:

        {scenario_text}

        Here are the exact requirements for injecting the vulnerability:
        1. **Vulnerability Injection**: Modify the provided contract code by introducing the {self.vulnerability_type} vulnerability. This modification must adhere strictly to the scenario described above.
           - The vulnerability should not be placed in obvious spots, such as where sensitive operations already exist. Instead, it should be subtly integrated into areas where it is less likely to be immediately detected.
           - Do not use obvious variable names, function names, or comments that could hint at the presence of the vulnerability. Ensure that the vulnerability is concealed within the logic of the contract, blending with existing functionality.

        2. **Method Modifications Only**: You are only allowed to modify existing methods in the contract. Do not add new methods, variables, or libraries unless they are absolutely necessary for the vulnerability itself. Focus on modifying existing logic to reflect the vulnerability without introducing obvious changes.

        3. **Retain Core Functionality**: Ensure that the contract retains its original functionality despite the vulnerability being injected. The contract logic must remain intact, with the vulnerability subtly integrated into existing methods without breaking or altering core functionality.

        4. **Avoid Detection**: The injected vulnerability should be hidden within the contract’s flow. Avoid leaving traces such as unnecessary changes, comments, or obvious indicators that would make the vulnerability easy to spot during a casual review.

        5. **Compilation**: The modified contract must compile successfully with no syntax or structural errors. Ensure that the code is valid Solidity, capable of being deployed on a blockchain.

        6. **No Additional Explanations**: Your response should include only the full modified Solidity contract code with the {self.vulnerability_type} vulnerability injected. Do not include comments, explanations, or extra annotations. Provide the contract code directly, ensuring it is clean and ready for use.

        7. **Consistency**: Keep the original formatting, indentation, and structure of the contract as much as possible. The changes should focus purely on the introduction of the vulnerability, and the rest of the contract should remain untouched unless absolutely necessary.

        Please reply with the full modified contract code, adhering strictly to the instructions above.
        """

        # Pretty-print the prompt in a single-column table
        table = Table(title="Prompt for Vulnerability Injection")
        table.add_column("Prompt", justify="left", style="green", no_wrap=False)
        table.add_row(prompt)

        self.console.print(table)

        return prompt

    def generate_dataset(self) -> None:
        """
        Generates the dataset by modifying existing contracts and injecting vulnerabilities.
        """
        total_scenarios = len(self.vulnerability_scenarios)
        for scenario_idx, scenario in enumerate(self.vulnerability_scenarios, start=1):
            scenario_name = scenario.name
            self.logger.info(f"[yellow]Processing scenario {scenario_idx}/{total_scenarios}:[/yellow] {scenario_name}")

            # Select contracts to process for this scenario
            if self.num_contracts_per_scenario >= len(self.contracts):
                contracts_to_process = self.contracts
            else:
                contracts_to_process = random.sample(self.contracts, self.num_contracts_per_scenario)

            for contract_idx, (contract_filename, contract_code) in enumerate(contracts_to_process, start=1):
                self.logger.info(
                    f"[yellow]  Applying scenario to contract {contract_idx}/{len(contracts_to_process)}:[/yellow] {contract_filename}")

                # Generate prompt
                prompt = self.generate_vulnerability_prompt(contract_code, scenario)

                # Get GPT response using the OpenAIClient
                try:
                    modified_contract = self.openai_client.get_gpt_response(prompt)

                    # Pretty-print GPT's response in a single-column table
                    response_table = Table(title=f"GPT Response for {contract_filename}")
                    response_table.add_column("Response", justify="left", style="magenta", no_wrap=False)
                    response_table.add_row(modified_contract)
                    self.console.print(response_table)

                    # Clean the response to remove ```solidity and other text
                    cleaned_contract = self.clean_gpt_response(modified_contract)

                    # Save the cleaned modified contract
                    self.save_modified_contract(contract_filename, scenario_name, cleaned_contract, contract_idx)
                except Exception as e:
                    self.logger.error(
                        f"[bold red]Error processing {contract_filename} with scenario {scenario_name}:[/bold red] {e}")
                    continue
