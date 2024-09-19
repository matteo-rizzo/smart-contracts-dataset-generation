import logging
import os

from openai import OpenAI

from dotenv import load_dotenv

# Global constant for the model to use
OPENAI_MODEL = "gpt-4o"

class OpenAIClient:
    """
    A client to interact with OpenAI's GPT API.
    """

    def __init__(self):
        """
        Initializes the OpenAI client by loading the API key from the .env file.
        :raises ValueError: If the OpenAI API key is not found in the environment.
        """
        load_dotenv()
        self.api_key = os.getenv('OPENAI_API_KEY')

        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")

        self.client = OpenAI(api_key=self.api_key)

        self.logger = logging.getLogger("OpenAIClient")
        logging.basicConfig(level=logging.INFO)

    def get_gpt_response(self, prompt: str) -> str:
        """
        Sends a prompt to OpenAI's GPT-4-turbo API and returns the response.

        :param prompt: The prompt to send to GPT.
        :type prompt: str
        :return: The response from GPT.
        :rtype: str
        :raises Exception: If an error occurs while communicating with the OpenAI API.
        """
        try:
            self.logger.info(f"Sending request to OpenAI model: {OPENAI_MODEL}")
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0  # For deterministic results
            )
            self.logger.info(f"Received response from OpenAI model: {OPENAI_MODEL}")
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error getting response from OpenAI API: {e}")
            raise e
