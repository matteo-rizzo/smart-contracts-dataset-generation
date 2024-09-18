import logging
import os

import openai
from dotenv import load_dotenv


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

        openai.api_key = self.api_key
        self.logger = logging.getLogger("rich")

    def get_gpt_response(self, prompt: str) -> str:
        """
        Sends a prompt to OpenAI's GPT API and returns the response.

        :param prompt: The prompt to send to GPT.
        :type prompt: str
        :return: The response from GPT.
        :rtype: str
        :raises Exception: If an error occurs while communicating with the OpenAI API.
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0  # For deterministic results
            )
            return response['choices'][0]['message']['content']
        except Exception as e:
            self.logger.error(f"[bold red]Error getting response from OpenAI API:[/bold red] {e}")
            raise e
