from langchain_groq import ChatGroq
from config import ConfigManager


class GroqLLM:
    """Groq LLM implementation using LangChain."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize the Groq LLM with configuration.

        Args:
            config_manager: Configuration manager containing Groq settings
        """
        self.config_manager = config_manager
        groq_config = config_manager.models_config.groq
        self.api_key = groq_config.api_key
        self.model_name = groq_config.model_name

        # Initialize the Groq client
        self.client = ChatGroq(
            api_key=self.api_key,
            model=self.model_name,
            temperature=groq_config.temperature,
            max_tokens=groq_config.max_tokens,
        )
