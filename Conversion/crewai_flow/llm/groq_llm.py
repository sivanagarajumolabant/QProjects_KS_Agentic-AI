from crewai import LLM
from config import ConfigManager


class GroqLLM:
    """Groq LLM implementation for CrewAI."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize the Groq LLM with configuration.

        Args:
            config_manager: Configuration manager containing Groq settings
        """
        self.config_manager = config_manager
        groq_config = config_manager.models_config.groq
        self.api_key = groq_config.api_key
        self.model_name = groq_config.model_name
        self.temperature = groq_config.temperature
        self.max_tokens = groq_config.max_tokens

        # Initialize the CrewAI LLM
        try:
            # For Groq, we need to use the format 'groq/<model_name>'
            model_name = f"groq/{self.model_name}"
            self._client = LLM(provider="groq",
                              model=model_name,
                              config={
                                  "api_key": self.api_key,
                                  "temperature": self.temperature,
                                  "max_tokens": self.max_tokens
                              })
            print(f"Successfully initialized Groq client with model {model_name}")
        except Exception as e:
            print(f"Error initializing Groq client: {str(e)}")
            raise

    @property
    def client(self):
        """Return the CrewAI LLM instance."""
        return self._client