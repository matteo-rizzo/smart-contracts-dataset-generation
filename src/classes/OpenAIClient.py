from openai import OpenAI

from src.classes.config.OpenAIConfig import OpenAIConfig


class OpenAIClient:
    """
    A client to interact with OpenAI's GPT API.
    """

    def __init__(self, config: OpenAIConfig):
        """
        Initializes the OpenAI client using the provided configuration.

        :param config: An instance of the OpenAIConfig class containing settings and environment variables.
        """
        self.api_key = config.api_key
        self.model = config.model
        self.logger = config.logger
        self.client = OpenAI(api_key=self.api_key)

    def get_gpt_response(self, prompt: str) -> str:
        """
        Sends a prompt to OpenAI's GPT-4 API and returns the response.

        :param prompt: The prompt to send to GPT.
        :type prompt: str
        :return: The response from GPT.
        :rtype: str
        :raises Exception: If an error occurs while communicating with the OpenAI API.
        """
        try:
            self.logger.info(f"Sending request to OpenAI model: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0  # For deterministic results
            )
            self.logger.info(f"Received response from OpenAI model: {self.model}")
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error getting response from OpenAI API: {e}")
            raise e
