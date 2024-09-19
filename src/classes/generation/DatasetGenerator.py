import abc
import logging
import os
import re
from datetime import datetime

from rich.console import Console
from rich.logging import RichHandler

from src.classes.OpenAIClient import OpenAIClient
from src.classes.generation.VulnerabilityScenarioReader import VulnerabilityScenarioReader


class DatasetGenerator(abc.ABC):
    """
    Abstract base class for dataset generators that inject vulnerabilities into smart contracts.
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
        self.scenarios_dir = scenarios_dir
        self.num_contracts_per_scenario = num_contracts_per_scenario
        self.vulnerability_type = vulnerability_type

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
        self.vulnerability_scenarios = self.scenario_reader.read_scenarios()

        # Initialize the OpenAI client
        self.openai_client = OpenAIClient()

    @abc.abstractmethod
    def generate_dataset(self) -> None:
        """
        Abstract method to generate the dataset by processing the specified number of contracts per scenario
        and saving the modified versions.
        """
        pass

    @staticmethod
    def clean_gpt_response(gpt_response: str) -> str:
        """
        Cleans the GPT response to ensure only the Solidity code is saved, removing extra markdown or text.

        :param gpt_response: The raw response from GPT.
        :type gpt_response: str
        :return: Cleaned Solidity code without markdown or other text.
        :rtype: str
        """
        # Remove ```solidity and ``` tags
        cleaned_code = re.sub(r"```solidity|```", "", gpt_response).strip()
        return cleaned_code

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
