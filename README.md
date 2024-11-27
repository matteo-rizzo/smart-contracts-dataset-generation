# Synthetic Vulnerable Smart Contracts Dataset Generator

This repository provides tools to generate a synthetic dataset of Solidity smart contracts with injected vulnerabilities. It uses **large language models (LLMs)** to inject vulnerabilities like reentrancy into existing contracts or generate new ones from scratch. Additionally, it includes functionality to fetch verified contracts from Etherscan, run static analysis tools on the contracts, and analyze vulnerabilities.

---

## Features

- **Etherscan-based generation**: Modifies real-world contracts sourced from Etherscan.
- **Scratch-based generation**: Generates entirely new contracts based on user-defined scenarios.
- **Verified contract fetching**: Fetch verified smart contracts from DeFi protocols on Etherscan.
- **Customizable vulnerabilities**: Inject specific vulnerabilities, such as reentrancy or front-running.
- **Scenarios**: Define vulnerabilities with detailed examples for injection.
- **Static analysis**: Use `SmartBugs` analyzers for vulnerability detection in contracts.
- **Scalable generation**: Generate multiple contracts per scenario with ease.

---

## Installation

### Prerequisites

1. **Python 3.8+**: Ensure you have Python installed.
2. **Dependencies**: Install required Python libraries using:

   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**: Populate your `.env` file with the following keys:
   - `ETHERSCAN_API_KEY`: Your Etherscan API key.
   - `OPENAI_API_KEY`: API key for OpenAI models.
   - `OPENAI_MODEL`: Specify the LLM model to use.

---

## Usage

### Fetch Verified Contracts from Etherscan

The script `fetch_contracts.py` fetches verified smart contracts from popular DeFi protocols using the Etherscan API.

#### Example Usage

```bash
python fetch_contracts.py
```

#### Key Functionalities

1. **Fetch Protocol Addresses**: Retrieves smart contract addresses for protocols like Uniswap, Aave, and Compound.
2. **Fetch Verified Contracts**: Downloads and saves verified contracts from Etherscan for dataset augmentation.
3. **Customization**: Modify protocols or the target count of contracts by editing `fetch_contracts.py`.

---

### Generate a Vulnerable Dataset

The main script `main.py` supports flexible generation options based on fetched contracts or from scratch.

#### Command-line Options

| Argument                       | Type  | Default              | Description                                                                     |
|--------------------------------|-------|----------------------|---------------------------------------------------------------------------------|
| `--generator_type`             | `str` | `etherscan`          | Select dataset generator: `etherscan` (modify existing contracts) or `scratch`. |
| `--vulnerability_type`         | `str` | `reentrancy`         | Type of vulnerability to inject (e.g., `reentrancy`, `front-running`).          |
| `--contracts_dir`              | `str` | `solidity_contracts` | Directory containing Solidity contracts (used with `etherscan` generator).      |
| `--scenarios_dir`              | `str` | `kb`                 | Directory containing JSON files defining generation scenarios.                  |
| `--num_contracts_per_scenario` | `int` | `5`                  | Number of contracts to generate per scenario.                                   |

#### Example Commands

##### Modify Existing Contracts

```bash
python main.py --generator_type etherscan --contracts_dir ./contracts --vulnerability_type reentrancy
```

##### Generate Contracts from Scratch

```bash
python main.py --generator_type scratch --scenarios_dir ./scenarios --vulnerability_type reentrancy
```

##### Customize Output

Generate 10 contracts per scenario:

```bash
python main.py --num_contracts_per_scenario 10
```

---

### Static Analysis with SmartBugs

The script `analyze_contracts.py` integrates SmartBugs analyzers for vulnerability detection in Solidity contracts.

#### Command-line Options

| Argument               | Type   | Default                             | Description                                                                 |
|------------------------|--------|-------------------------------------|-----------------------------------------------------------------------------|
| `--contracts-folder`   | `str`  | `dataset/etherscan150/runtime`      | Path to the folder containing smart contracts to analyze.                  |
| `--output-folder`      | `str`  | `logs`                              | Path to the folder where analysis results will be saved.                   |
| `--analyzers`          | `list` | `["ethor"]`                         | List of analyzers to use (e.g., `mythril`, `slither`).                      |
| `--timeout`            | `int`  | `300`                               | Timeout for each analysis in seconds.                                      |
| `--processes`          | `int`  | `2`                                 | Number of parallel processes to use for analysis.                          |
| `--mem-limit`          | `str`  | `4g`                                | Memory limit for each analysis process (e.g., `4g` for 4 GB).              |
| `--cpu-quota`          | `int`  | `None`                              | Optional CPU quota for each process (percentage of CPU usage).             |
| `--output-format`      | `str`  | `json`                              | Format of the analysis results (`json` or `sarif`).                        |
| `--runtime`            | `bool` | `False`                             | Analyze runtime bytecode instead of Solidity source files. Overrides global mode. |

#### Example Commands

##### Run SmartBugs on Runtime Bytecode

```bash
python analyze_contracts.py --runtime
```

##### Analyze Contracts with Custom Settings

```bash
python analyze_contracts.py --contracts-folder ./contracts --analyzers mythril slither --timeout 600 --processes 4
```

---

## Scenarios

Scenarios are defined in JSON format in the `kb/` directory. Each scenario describes:

- **Name**: A short name for the vulnerability.
- **Scenario**: A detailed explanation of the vulnerability and its exploit.
- **Example**: Code snippet illustrating the vulnerability.
- **Issue**: A summary of the flaw being exploited.

### Example Scenario

```json
{
    "name": "Cross-Function Reentrancy",
    "scenario": "An attacker reenters a different function than the one initially called, manipulating shared state variables.",
    "example": "function deposit() public payable {\n    balances[msg.sender] += msg.value;\n}\n\nfunction transfer(address to, uint256 amount) public {\n    require(balances[msg.sender] >= amount, \"Insufficient balance\");\n    balances[to] += amount;\n    balances[msg.sender] -= amount;\n}\n\nfunction withdrawAll() public {\n    uint256 amount = balances[msg.sender];\n    require(amount > 0, \"No funds\");\n    (bool success, ) = msg.sender.call{value: amount}(\"\");\n    require(success, \"Transfer failed\");\n    balances[msg.sender] = 0;\n}",
    "issue": "During `withdrawAll`, an attacker can call `deposit` or `transfer`, manipulating balances before the original function completes."
}
```

---

## Development

### Adding a New Vulnerability

To inject a new vulnerability type:

1. Extend the base functionality in `EtherscanDatasetGenerator` or `ScratchDatasetGenerator`.
2. Define the new injection logic.
3. Update the `--vulnerability_type` argument to include the new type.

### Adding a New Static Analyzer

1. Update the `SmartBugsRunner` class to include the new analyzer.
2. Test compatibility with your contracts.
3. Add the analyzer to the `--analyzers` argument.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.