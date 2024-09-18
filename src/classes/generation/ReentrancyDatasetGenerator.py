import logging
import os
import random
import re
from datetime import datetime

from rich.console import Console
from rich.logging import RichHandler

from src.classes.generation.ContractReader import ContractReader
from src.classes.generation.OpenAIClient import OpenAIClient
from src.classes.generation.VulnerabilityScenario import VulnerabilityScenario
from src.classes.generation.VulnerabilityScenarioReader import VulnerabilityScenarioReader


class ReentrancyDatasetGenerator:
    """
    Generates a dataset of Solidity contracts with injected reentrancy vulnerabilities.
    """

    def __init__(self, contracts_dir: str, scenarios_dir: str, num_contracts_per_scenario: int):
        """
        Initializes the generator with directories and sets up logging and the OpenAI client.

        :param contracts_dir: Directory containing Solidity contracts.
        :type contracts_dir: str
        :param scenarios_dir: Directory containing scenario JSON files.
        :type scenarios_dir: str
        :param num_contracts_per_scenario: Number of contracts to generate per scenario.
        :type num_contracts_per_scenario: int
        """
        self.contracts_dir = contracts_dir
        self.scenarios_dir = scenarios_dir
        self.num_contracts_per_scenario = num_contracts_per_scenario

        # Set up Rich console for enhanced output
        self.console = Console()

        # Configure logging with RichHandler
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s',
            datefmt="[%X]",
            handlers=[
                RichHandler(console=self.console)
            ]
        )
        self.logger = logging.getLogger("rich")

        # Create the output directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"logs/dataset_{timestamp}"
        os.makedirs(self.output_dir, exist_ok=True)
        self.logger.info(f"[bold green]Output directory created:[/bold green] {self.output_dir}")

        # Read scenarios
        self.scenario_reader = VulnerabilityScenarioReader(self.scenarios_dir)
        self.reentrancy_scenarios = self.scenario_reader.read_scenarios()

        # Read contracts
        self.contract_reader = ContractReader(self.contracts_dir)
        self.contracts = self.contract_reader.read_contracts()

        # Initialize the OpenAI client
        self.openai_client = OpenAIClient()

    @staticmethod
    def generate_reentrancy_prompt(contract_code: str, scenario: VulnerabilityScenario) -> str:
        """
        Generates a prompt for GPT to inject a reentrancy vulnerability into the given Solidity contract using a specific scenario.

        :param contract_code: The Solidity contract code.
        :type contract_code: str
        :param scenario: The vulnerability scenario describing the reentrancy attack.
        :type scenario: VulnerabilityScenario
        :return: A prompt for GPT to inject reentrancy into the contract.
        :rtype: str
        """
        # Construct the scenario text to include in the prompt
        scenario_text = f"""### Scenario: {scenario.name}
                            **Description**: {scenario.scenario}
                            **Issue**: {scenario.issue}
                            **Example**:
                            ```solidity
                            {scenario.example}"""
        prompt = f"""You are a Solidity smart contract security expert. The following is a Solidity smart contract:
                    {contract_code}
                    Based on the detailed reentrancy scenario provided, inject a reentrancy vulnerability into this contract.
                    Modify the contract code to include the vulnerability, following the scenario described. Ensure that
                    the injected vulnerability aligns with the following scenario:
                    {scenario_text}
                    Provide the modified contract code with the reentrancy vulnerability injected. Make sure the modified
                    contract compiles and retains its original functionality aside from the injected vulnerability. """
        return prompt

    def generate_dataset(self) -> None:
        """
        Generates the dataset by processing the specified number of contracts per scenario and saving the modified versions.
        """
        total_scenarios = len(self.reentrancy_scenarios)
        for scenario_idx, scenario in enumerate(self.reentrancy_scenarios, start=1):
            scenario_name = scenario.name
            self.logger.info(f"[yellow]Processing scenario {scenario_idx}/{total_scenarios}:[/yellow] {scenario_name}")

            # Select contracts to process for this scenario
            if self.num_contracts_per_scenario >= len(self.contracts):
                # If requested number is more than available, use all contracts
                contracts_to_process = self.contracts
            else:
                # Randomly select the required number of contracts
                contracts_to_process = random.sample(self.contracts, self.num_contracts_per_scenario)

            for contract_idx, (contract_filename, contract_code) in enumerate(contracts_to_process, start=1):
                self.logger.info(
                    f"[yellow]  Applying scenario to contract {contract_idx}/{len(contracts_to_process)}:[/yellow] {contract_filename}")
                # Generate prompt
                prompt = self.generate_reentrancy_prompt(contract_code, scenario)

                # Get GPT response using the OpenAIClient
                try:
                    modified_contract = self.openai_client.get_gpt_response(prompt)
                    # Save the modified contract, include an instance number for uniqueness
                    self.save_modified_contract(contract_filename, scenario_name, modified_contract, contract_idx)
                except Exception as e:
                    self.logger.error(
                        f"[bold red]Error processing {contract_filename} with scenario {scenario_name}:[/bold red] {e}")
                    continue  # Skip to the next contract

    def save_modified_contract(self, contract_filename: str, scenario_name: str, modified_contract: str,
                               instance_number: int) -> None:
        """
        Saves the modified contract to a file in the output directory.

        :param contract_filename: The original contract filename.
        :type contract_filename: str
        :param scenario_name: The name of the scenario used.
        :type scenario_name: str
        :param modified_contract: The modified contract code.
        :type modified_contract: str
        :param instance_number: The instance number for uniqueness.
        :type instance_number: int
        :raises Exception: If there is an error while saving the modified contract.
        """
        try:
            # Sanitize scenario name for filename
            sanitized_scenario_name = self.sanitize_filename(scenario_name)
            # Construct a unique filename combining contract, scenario, and instance number
            base_contract_name = os.path.splitext(contract_filename)[0]
            output_filename = f"{base_contract_name}_{sanitized_scenario_name}_{instance_number}.sol"
            output_filepath = os.path.join(self.output_dir, output_filename)
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(modified_contract)
            self.logger.info(f"[bold cyan]Modified contract saved:[/bold cyan] {output_filepath}")
        except Exception as e:
            self.logger.error(f"[bold red]Error saving modified contract {output_filename}:[/bold red] {e}")
            raise e

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """
        Sanitizes a string to be used as a filename.

        :param name: The original name.
        :type name: str
        :return: A sanitized filename string.
        :rtype: str
        """
        sanitized = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
        return sanitized
