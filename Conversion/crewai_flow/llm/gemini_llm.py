from crewai import LLM
from config import ConfigManager


class GeminiLLM:
    """Gemini LLM implementation for CrewAI."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize the Gemini LLM with configuration.

        Args:
            config_manager: Configuration manager containing Gemini settings
        """
        self.config_manager = config_manager
        gemini_config = config_manager.models_config.gemini
        self.api_key = gemini_config.api_key
        self.model_name = gemini_config.model_name
        self.temperature = gemini_config.temperature
        self.max_tokens = gemini_config.max_tokens

        # Initialize the CrewAI LLM
        try:
            # For Gemini, we need to use the format 'gemini/<model_name>'
            model_name = f"gemini/{self.model_name}"
            self._client = LLM(provider="gemini",
                              model=model_name,
                              config={
                                  "api_key": self.api_key,
                                  "temperature": self.temperature,
                                  "max_tokens": self.max_tokens
                              })
            print(f"Successfully initialized Gemini client with model {model_name}")
        except Exception as e:
            print(f"Error initializing Gemini client: {str(e)}")
            raise

    @property
    def client(self):
        """Return the CrewAI LLM instance."""
        return self._client