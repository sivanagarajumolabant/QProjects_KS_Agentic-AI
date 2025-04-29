from crewai import LLM
from config import ConfigManager


class AnthropicLLM:
    """Anthropic LLM implementation for CrewAI."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize the Anthropic LLM with configuration.

        Args:
            config_manager: Configuration manager containing Anthropic settings
        """
        self.config_manager = config_manager
        anthropic_config = config_manager.models_config.anthropic
        self.api_key = anthropic_config.api_key
        self.model_name = anthropic_config.model_name
        self.temperature = anthropic_config.temperature
        self.max_tokens = anthropic_config.max_tokens

        # Initialize the CrewAI LLM
        try:
            # For Anthropic, we need to use the format 'anthropic/<model_name>'
            model_name = f"anthropic/{self.model_name}"
            self._client = LLM(provider="anthropic",
                              model=model_name,
                              config={
                                  "api_key": self.api_key,
                                  "temperature": self.temperature,
                                  "max_tokens": self.max_tokens
                              })
            print(f"Successfully initialized Anthropic client with model {model_name}")
        except Exception as e:
            print(f"Error initializing Anthropic client: {str(e)}")
            raise

    @property
    def client(self):
        """Return the CrewAI LLM instance."""
        return self._client