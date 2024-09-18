import json
import os
import re
from typing import List, Dict

from rich.console import Console


class ReentrancyScenarioExtractor:
    """
    A class to extract reentrancy scenarios from a markdown file and save them as JSON files.
    """

    def __init__(self, input_file: str, output_dir: str):
        """
        Initializes the extractor with the input file and output directory.

        Args:
            input_file (str): Path to the input markdown file.
            output_dir (str): Directory to save the output JSON files.
        """
        self.input_file = input_file
        self.output_dir = output_dir
        self.console = Console()

    def read_input_file(self) -> str:
        """
        Reads the input markdown file.

        Returns:
            str: The content of the input file.
        """
        try:
            with open(self.input_file, 'r', encoding='utf-8') as file:
                text = file.read()
            self.console.print(f"[green]Successfully read input file:[/green] {self.input_file}")
            return text
        except FileNotFoundError:
            self.console.print(f"[red]Input file not found:[/red] {self.input_file}")
            raise
        except Exception as e:
            self.console.print(f"[red]Error reading input file:[/red] {e}")
            raise

    def split_scenarios(self, text: str) -> List[Dict[str, str]]:
        """
        Splits the input text into individual reentrancy scenarios.

        Args:
            text (str): The full text containing all scenarios.

        Returns:
            List[Dict[str, str]]: A list of dictionaries, each containing scenario details.
        """
        # Split the text into individual scenarios using the '---' separator
        raw_scenarios = re.split(r'\n-{3,}\n', text)
        scenario_list: List[Dict[str, str]] = []

        for scenario_text in raw_scenarios:
            # Use regex to extract the scenario components
            name_match = re.search(r'^###\s\*\*(\d+\.\s+.+?)\*\*', scenario_text, re.MULTILINE)
            scenario_match = re.search(r'\*\*Scenario\*\*:\s*(.+?)(?=\n\n\*\*Example\*\*|$)', scenario_text, re.DOTALL)
            example_match = re.search(r'\*\*Example\*\*:\s*\n\n```solidity\n(.*?)\n```', scenario_text, re.DOTALL)
            issue_match = re.search(r'\*\*Issue\*\*:\s*(.+?)(?=\n)', scenario_text, re.DOTALL)

            if name_match and scenario_match and example_match and issue_match:
                name_with_number = name_match.group(1).strip()
                # Remove the numbering from the name
                name = re.sub(r'^\d+\.\s+', '', name_with_number)
                scenario_description = scenario_match.group(1).strip()
                example_code = example_match.group(1).strip()
                issue_description = issue_match.group(1).strip()

                scenario_data: Dict[str, str] = {
                    'name': name,
                    'scenario': scenario_description,
                    'example': example_code,
                    'issue': issue_description
                }

                scenario_list.append(scenario_data)
            else:
                # Handle scenarios that don't match the expected pattern
                self.console.print("[yellow]Warning:[/yellow] Could not parse a scenario section correctly.")

        return scenario_list

    def save_scenarios_to_json(self, scenarios: List[Dict[str, str]]) -> None:
        """
        Saves each scenario to a separate JSON file.

        Args:
            scenarios (List[Dict[str, str]]): A list of scenario dictionaries.
        """
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        total_scenarios = len(scenarios)
        if total_scenarios == 0:
            self.console.print("[red]No scenarios to save.[/red]")
            return

        for idx, scenario in enumerate(scenarios, start=1):
            filename = f"reentrancy_scenario_{idx}.json"
            filepath = os.path.join(self.output_dir, filename)

            try:
                with open(filepath, 'w', encoding='utf-8') as json_file:
                    json.dump(scenario, json_file, indent=4)
                self.console.print(f"[green]Saved scenario {idx}/{total_scenarios}:[/green] {filepath}")
            except Exception as e:
                self.console.print(f"[red]Error saving {filepath}:[/red] {e}")

    def extract_and_save(self) -> None:
        """
        Orchestrates the extraction and saving of reentrancy scenarios.
        """
        text = self.read_input_file()
        scenarios = self.split_scenarios(text)
        self.save_scenarios_to_json(scenarios)
