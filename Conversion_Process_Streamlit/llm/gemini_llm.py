from langchain_google_genai import ChatGoogleGenerativeAI
from config import ConfigManager


class GeminiLLM:
    """Gemini LLM implementation using LangChain."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize the Gemini LLM with configuration.

        Args:
            config_manager: Configuration manager containing Gemini settings
        """
        self.config_manager = config_manager
        gemini_config = config_manager.models_config.gemini
        self.api_key = gemini_config.api_key
        self.model_name = gemini_config.model_name

        # Initialize the Gemini client
        self.client = ChatGoogleGenerativeAI(
            google_api_key=self.api_key,
            model=self.model_name,
            temperature=gemini_config.temperature,
            max_output_tokens=gemini_config.max_tokens,
        )
