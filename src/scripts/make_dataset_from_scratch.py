import random

# Extended lists of variations for contract types, functions, and interaction patterns
contract_types = [
    "auction", "token transfer", "escrow", "crowdfunding", "staking",
    "lending", "decentralized exchange", "NFT marketplace", "voting system",
    "reward distribution", "liquidity pool", "subscription service", "gaming contract",
    "charity donation", "royalty distribution", "time-locked vault", "payment splitter",
    "insurance contract", "betting contract", "prediction market"
]

function_names = [
    "withdraw", "claim", "refund", "distribute", "redeem",
    "release", "payout", "settle", "cancel", "unstake",
    "withdrawStake", "withdrawFunds", "exit", "finalize", "revoke",
    "withdrawBid", "processRefund", "closeAuction", "rewardWinners",
    "withdrawDeposits", "liquidate", "divest"
]

interaction_types = [
    "with another contract", "with an external wallet", "with a user account",
    "with a decentralized application", "with an off-chain oracle",
    "with a DeFi protocol", "with an external exchange", "with an external DeFi lending protocol",
    "with a multisig wallet", "with a hardware wallet",
    "with an external governance contract", "with a DAO",
    "with a batch contract", "with an automated market maker",
    "with a layer-2 scaling solution", "with a token bridging contract",
    "with a liquidity mining program", "with a stablecoin contract",
    "with a yield farming protocol", "with a smart contract wallet"
]

# Function to generate a variety of prompts
def generate_prompt(contract_type, function_name, interaction_type):
    return f"Generate a Solidity {contract_type} smart contract with a reentrancy vulnerability in the {function_name} function, interacting {interaction_type}."

# Generate multiple prompts
for _ in range(10):  # Generating 10 prompts for this example
    contract_type = random.choice(contract_types)
    function_name = random.choice(function_names)
    interaction_type = random.choice(interaction_types)
    prompt = generate_prompt(contract_type, function_name, interaction_type)
    print(prompt)
