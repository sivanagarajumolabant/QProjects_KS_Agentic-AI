from langchain_openai import ChatOpenAI
from config import ConfigManager


class OpenAILLM:
    """OpenAI LLM implementation using LangChain."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize the OpenAI LLM with configuration.

        Args:
            config_manager: Configuration manager containing OpenAI settings
        """
        self.config_manager = config_manager
        openai_config = config_manager.models_config.openai
        self.api_key = openai_config.api_key
        self.model_name = openai_config.model_name

        # Initialize the OpenAI client
        self.client = ChatOpenAI(
            api_key=self.api_key,
            model=self.model_name,
            temperature=openai_config.temperature,
            max_tokens=openai_config.max_tokens,
        )
