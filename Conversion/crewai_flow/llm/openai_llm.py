from crewai import LLM
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class OpenAILLM:
    """OpenAI LLM implementation for CrewAI."""

    def __init__(self, config_manager=None):
        """Initialize the OpenAI LLM with configuration.

        Args:
            config_manager: Not used, kept for compatibility with other LLM classes
        """
        # Get values from environment variables
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("OPENAI_MODEL")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))

        # Validate required environment variables
        if not all([self.api_key, self.model_name]):
            missing = []
            if not self.api_key: missing.append("OPENAI_API_KEY")
            if not self.model_name: missing.append("OPENAI_MODEL")
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        # Initialize the CrewAI LLM
        try:
            # For OpenAI, we need to use the format 'openai/<model_name>'
            model_name = f"openai/{self.model_name}"
            self._client = LLM(provider="openai",
                              model=model_name,
                              config={
                                  "api_key": self.api_key,
                                  "temperature": self.temperature,
                                  "max_tokens": self.max_tokens
                              })
            print(f"Successfully initialized OpenAI client with model {model_name}")
        except Exception as e:
            print(f"Error initializing OpenAI client: {str(e)}")
            raise

    @property
    def client(self):
        """Return the CrewAI LLM instance."""
        return self._client