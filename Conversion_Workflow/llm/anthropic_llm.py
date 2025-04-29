from langchain_anthropic import ChatAnthropic
from config import ConfigManager


class AnthropicLLM:
    """Anthropic LLM implementation using LangChain."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize the Anthropic LLM with configuration.

        Args:
            config_manager: Configuration manager containing Anthropic settings
        """
        self.config_manager = config_manager
        anthropic_config = config_manager.models_config.anthropic
        self.api_key = anthropic_config.api_key
        self.model_name = anthropic_config.model_name

        # Initialize the Anthropic client
        self.client = ChatAnthropic(
            api_key=self.api_key,
            model=self.model_name,
            temperature=anthropic_config.temperature,
            max_tokens=anthropic_config.max_tokens,
        )