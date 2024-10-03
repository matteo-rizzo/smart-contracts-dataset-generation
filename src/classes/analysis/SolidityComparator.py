import json
import os
from difflib import SequenceMatcher
from typing import List, Dict, Any

import matplotlib.pyplot as plt
import networkx as nx
from rich.console import Console
from rich.progress import track
from rich.table import Table

# Import Slither
from slither import Slither

# Console for rich output
console = Console()


class SolidityComparator:
    def __init__(self, folder_path: str) -> None:
        """
        Initialize the SolidityComparator with the folder path.

        :param folder_path: Path to the folder containing Solidity files.
        """
        self.folder_path = folder_path
        self.contracts: List[str] = self._get_contract_files()
        self.results: List[Dict[str, Any]] = []

    def _get_contract_files(self) -> List[str]:
        """
        Recursively finds all .sol files in the given folder.

        :return: List of Solidity file paths.
        """
        contracts = []
        for root, _, files in os.walk(self.folder_path):
            for file in files:
                if file.endswith(".sol"):
                    contracts.append(os.path.join(root, file))
        return contracts

    @staticmethod
    def extract_ast(file_path: str) -> Dict[str, Any]:
        """
        Extract the AST of a Solidity file using Slither.

        :param file_path: Path to the Solidity file.
        :return: The AST as a dictionary.
        """
        try:
            slither_instance = Slither(file_path)
            ast = slither_instance.compilation_units[0].ast
            return ast
        except Exception as e:
            console.print(f"[red]Error extracting AST from {file_path}: {str(e)}[/red]")
            return {}

    @staticmethod
    def extract_cfg(file_path: str) -> List[Any]:
        """
        Extract the CFGs of a Solidity file using Slither.

        :param file_path: Path to the Solidity file.
        :return: List of CFG objects for each function in the contract.
        """
        try:
            slither_instance = Slither(file_path)
            cfgs = []
            for contract in slither_instance.contracts:
                for function in contract.functions_and_modifiers_declared:
                    if function.cfg:
                        cfgs.append(function.cfg)
                # Handle inheritance
                for function in contract.functions_and_modifiers_inherited:
                    if function.cfg:
                        cfgs.append(function.cfg)
            return cfgs
        except Exception as e:
            console.print(f"[red]Error extracting CFG from {file_path}: {str(e)}[/red]")
            return []

    @staticmethod
    def ast_similarity(ast1: Dict[str, Any], ast2: Dict[str, Any]) -> float:
        """
        Compute AST similarity using a simple string comparison.

        :param ast1: AST of the first contract.
        :param ast2: AST of the second contract.
        :return: Similarity score between the two ASTs.
        """
        ast_str1 = json.dumps(ast1, sort_keys=True)
        ast_str2 = json.dumps(ast2, sort_keys=True)
        return SequenceMatcher(None, ast_str1, ast_str2).ratio()

    @staticmethod
    def cfg_similarity(cfg1: Any, cfg2: Any) -> float:
        """
        Compute CFG similarity by comparing the structure of control flow graphs.

        :param cfg1: CFG of the first contract.
        :param cfg2: CFG of the second contract.
        :return: Similarity score between the two CFGs.
        """

        def cfg_to_networkx(cfg: Any) -> nx.DiGraph:
            """
            Convert a Slither CFG into a NetworkX graph.

            :param cfg: Control Flow Graph (CFG) of a function.
            :return: A NetworkX DiGraph representing the CFG.
            """
            graph = nx.DiGraph()
            for node in cfg.nodes:
                graph.add_node(node, label=str(node))
                for edge in node.succ_edges:
                    graph.add_edge(node, edge.dest)
            return graph

        g1 = cfg_to_networkx(cfg1)
        g2 = cfg_to_networkx(cfg2)

        # Graph similarity can be computed with graph edit distance
        try:
            distance = nx.graph_edit_distance(g1, g2)
            # Normalize the distance to a similarity score between 0 and 1
            max_distance = max(g1.size(), g2.size())
            if max_distance == 0:
                return 1.0
            similarity = 1 - (distance / max_distance)
            return similarity
        except Exception as e:
            console.print(f"[red]Error computing CFG similarity: {str(e)}[/red]")
            return 0.0

    def compute_similarity(self, ast1: Dict[str, Any], ast2: Dict[str, Any],
                           cfgs1: List[Any], cfgs2: List[Any]) -> float:
        """
        Compute overall similarity between two contracts by combining AST and CFG similarity.

        :param ast1: AST of the first contract.
        :param ast2: AST of the second contract.
        :param cfgs1: List of CFGs of the first contract.
        :param cfgs2: List of CFGs of the second contract.
        :return: Combined similarity score.
        """
        ast_sim = self.ast_similarity(ast1, ast2)

        # CFG similarity (average over all CFGs)
        cfg_sim_total = 0.0
        count = 0
        for cfg1 in cfgs1:
            for cfg2 in cfgs2:
                cfg_sim_total += self.cfg_similarity(cfg1, cfg2)
                count += 1

        if count > 0:
            cfg_sim = cfg_sim_total / count
        else:
            cfg_sim = 1.0  # Consider them identical if no CFG exists

        # Combine AST and CFG similarity
        return (ast_sim + cfg_sim) / 2

    def compare_contracts(self) -> None:
        """
        Compare all smart contracts in the folder and store the similarity results.
        """
        total_pairs = (len(self.contracts) * (len(self.contracts) - 1)) // 2
        progress = track(range(len(self.contracts)), description="Comparing contracts...", total=total_pairs)
        for i in progress:
            for j in range(i + 1, len(self.contracts)):
                try:
                    ast1 = self.extract_ast(self.contracts[i])
                    cfgs1 = self.extract_cfg(self.contracts[i])

                    ast2 = self.extract_ast(self.contracts[j])
                    cfgs2 = self.extract_cfg(self.contracts[j])

                    if ast1 and ast2:
                        similarity = self.compute_similarity(ast1, ast2, cfgs1, cfgs2)
                        self.results.append({
                            'contract_1': self.contracts[i],
                            'contract_2': self.contracts[j],
                            'similarity': similarity
                        })
                except Exception as e:
                    console.print(f"[red]Error comparing {self.contracts[i]} and {self.contracts[j]}: {str(e)}[/red]")

    def display_results(self) -> None:
        """
        Display the comparison results in a rich table.
        """
        table = Table(title="Solidity Contract Similarities")

        table.add_column("Contract 1", justify="left", style="cyan", no_wrap=True)
        table.add_column("Contract 2", justify="left", style="cyan", no_wrap=True)
        table.add_column("Similarity", justify="right", style="green")

        for result in self.results:
            contract_1 = os.path.basename(result['contract_1'])
            contract_2 = os.path.basename(result['contract_2'])
            similarity = f"{result['similarity']:.4f}"
            table.add_row(contract_1, contract_2, similarity)

        console.print(table)

    def plot_similarity_heatmap(self) -> None:
        """
        Plot a heatmap of contract similarities.
        """
        num_contracts = len(self.contracts)
        similarity_matrix = [[1.0 for _ in range(num_contracts)] for _ in range(num_contracts)]

        contract_index = {contract: i for i, contract in enumerate(self.contracts)}

        for result in self.results:
            i = contract_index[result['contract_1']]
            j = contract_index[result['contract_2']]
            similarity_matrix[i][j] = result['similarity']
            similarity_matrix[j][i] = result['similarity']

        plt.figure(figsize=(10, 8))
        plt.imshow(similarity_matrix, cmap='coolwarm', interpolation='nearest')
        plt.colorbar(label="Similarity")
        plt.xticks(range(num_contracts), [os.path.basename(c) for c in self.contracts], rotation=90)
        plt.yticks(range(num_contracts), [os.path.basename(c) for c in self.contracts])
        plt.title("Contract Similarity Heatmap")
        plt.tight_layout()
        plt.show()

    def run(self) -> None:
        """
        Main execution method to run the comparison and display results.
        """
        self.compare_contracts()
        if self.results:
            console.print("\n[bold green]Similarity results:[/bold green]")
            self.display_results()
            self.plot_similarity_heatmap()
        else:
            console.print("[red]No Solidity files found or comparison failed.[/red]")


if __name__ == "__main__":
    folder_path = input("Enter the path to the folder containing Solidity files: ")

    # Check if the folder path exists
    if not os.path.isdir(folder_path):
        console.print("[red]The provided folder path does not exist or is invalid.[/red]")
    else:
        comparator = SolidityComparator(folder_path)
        comparator.run()
