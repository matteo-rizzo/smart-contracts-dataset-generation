import argparse
import os

from src.classes.analysis.SmartbugsRunner import SmartBugsRunner

DEFAULT_CONTRACTS_FOLDER = os.path.join("..", "..", "dataset", "etherscan150")
DEFAULT_OUTPUT_FOLDER = os.path.join("..", "..", "logs")
DEFAULT_ANALYZERS = ["ethor", "mythril"]
DEFAULT_TIMEOUT = 300
DEFAULT_PROCESSES = 2
DEFAULT_MEM_LIMIT = "4g"
DEFAULT_CPU_QUOTA = None
DEFAULT_OUTPUT_FORMAT = "json"

if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(description="Run SmartBugs analyzers on a folder of smart contracts.")
    parser.add_argument('--contracts-folder', '-c', default=DEFAULT_CONTRACTS_FOLDER,
                        help=f"Path to the folder containing smart contracts. (default: {DEFAULT_CONTRACTS_FOLDER})")
    parser.add_argument('--output-folder', '-o', default=DEFAULT_OUTPUT_FOLDER,
                        help=f"Path to the folder where analysis results will be saved. (default: {DEFAULT_OUTPUT_FOLDER})")
    parser.add_argument('--analyzers', '-a', nargs='+', default=DEFAULT_ANALYZERS,
                        help=f"List of analyzers to use (e.g., mythril slither). (default: {DEFAULT_ANALYZERS})")
    parser.add_argument('--timeout', '-t', type=int, default=DEFAULT_TIMEOUT,
                        help=f"Timeout for each analysis in seconds. (default: {DEFAULT_TIMEOUT})")
    parser.add_argument('--processes', '-p', type=int, default=DEFAULT_PROCESSES,
                        help=f"Number of parallel processes to use. (default: {DEFAULT_PROCESSES})")
    parser.add_argument('--mem-limit', '-m', default=DEFAULT_MEM_LIMIT,
                        help=f"Memory limit for each process (e.g., 4g for 4 GB). (default: {DEFAULT_MEM_LIMIT})")
    parser.add_argument('--cpu-quota', '-q', type=int, default=DEFAULT_CPU_QUOTA,
                        help=f"Optional CPU quota for each process (percentage of CPU usage). (default: {DEFAULT_CPU_QUOTA})")
    parser.add_argument('--output-format', '-f', default=DEFAULT_OUTPUT_FORMAT, choices=['json', 'sarif'],
                        help=f"Output format for the analysis results: json or sarif. (default: {DEFAULT_OUTPUT_FORMAT})")

    args = parser.parse_args()

    # Create the SmartBugsRunner instance with command-line arguments or defaults
    runner = SmartBugsRunner(
        contracts_folder=args.contracts_folder,
        output_folder=args.output_folder,
        analyzers=args.analyzers,
        timeout=args.timeout,
        processes=args.processes,
        mem_limit=args.mem_limit,
        cpu_quota=args.cpu_quota,
        output_format=args.output_format
    )

    # Run the analysis
    runner.run()
