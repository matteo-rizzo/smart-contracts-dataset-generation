import argparse

from src.classes.generation.ReentrancyDatasetGenerator import ReentrancyDatasetGenerator

if __name__ == '__main__':
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate reentrancy dataset.")
    parser.add_argument('--contracts_dir', type=str, default='../../solidity_contracts',
                        help='Directory containing Solidity contracts.')
    parser.add_argument('--scenarios_dir', type=str, default='../../kb',
                        help='Directory containing scenario JSON files.')
    parser.add_argument('--num_contracts_per_scenario', type=int, default=20,
                        help='Number of contracts to generate per scenario.')

    args = parser.parse_args()

    # Create an instance of the generator
    generator = ReentrancyDatasetGenerator(
        contracts_dir=args.contracts_dir,
        scenarios_dir=args.scenarios_dir,
        num_contracts_per_scenario=args.num_contracts_per_scenario
    )

    # Generate the dataset
    generator.generate_dataset()
