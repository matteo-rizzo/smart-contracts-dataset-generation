import logging
import os

from dotenv import load_dotenv


class OpenAIConfig:
    """
    A configuration class to handle environment variables, logging, and other settings.
    """

    def __init__(self):
        """
        Initializes the configuration by loading environment variables and setting up logging.
        """
        load_dotenv()
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")

        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o')  # Default model if not set in .env
        self.logger = self.setup_logging()

    @staticmethod
    def setup_logging():
        """
        Sets up logging for the application.
        """
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger("OpenAIClient")
