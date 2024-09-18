import os

from dotenv import load_dotenv

# Load the API key from the .env file
load_dotenv()
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')


class Config:
    API_KEY = ETHERSCAN_API_KEY
    SAVE_DIR = "solidity_contracts"
    RATE_LIMIT = 5  # 5 requests per second
    RETRY_LIMIT = 3  # Number of retries for failed requests
