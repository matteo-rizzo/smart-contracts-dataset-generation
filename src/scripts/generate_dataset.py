import argparse

from src.classes.generation.EtherscanDatasetGenerator import EtherscanDatasetGenerator
from src.classes.generation.ScratchDatasetGenerator import ScratchDatasetGenerator

if __name__ == '__main__':
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate Solidity contract dataset with injected vulnerabilities.")

    parser.add_argument('--generator_type', type=str, choices=['etherscan', 'scratch'], default='scratch',
                        help='Choose the type of dataset generator: "etherscan" to modify existing contracts, "scratch" to generate new contracts from scratch.')
    parser.add_argument('--vulnerability_type', type=str, default='reentrancy',
                        help='The type of vulnerability to inject into the contracts (e.g., reentrancy, front-running).')
    parser.add_argument('--contracts_dir', type=str, default='solidity_contracts',
                        help='Directory containing Solidity contracts. (Only used for "etherscan" generator type).')
    parser.add_argument('--scenarios_dir', type=str, default='kb',
                        help='Directory containing scenario JSON files.')
    parser.add_argument('--num_contracts_per_scenario', type=int, default=5,
                        help='Number of contracts to generate per scenario.')

    args = parser.parse_args()

    # Choose the appropriate dataset generator
    if args.generator_type == 'etherscan':
        # Use the EtherscanDatasetGenerator to modify existing contracts
        generator = EtherscanDatasetGenerator(
            contracts_dir=args.contracts_dir,
            scenarios_dir=args.scenarios_dir,
            num_contracts_per_scenario=args.num_contracts_per_scenario,
            vulnerability_type=args.vulnerability_type
        )
    elif args.generator_type == 'scratch':
        # Use the ScratchDatasetGenerator to generate contracts from scratch
        generator = ScratchDatasetGenerator(
            scenarios_dir=args.scenarios_dir,
            num_contracts_per_scenario=args.num_contracts_per_scenario,
            vulnerability_type=args.vulnerability_type
        )

    # Generate the dataset
    generator.generate_dataset()
