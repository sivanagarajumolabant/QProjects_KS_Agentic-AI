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
        # Add Gemini configuration to model_config.py first
        # For now, we'll use a workaround to access the API key
        self.api_key = config_manager.get_llm_config().get("api_key", "")
        self.model_name = config_manager.get_llm_config().get("model_name", "gemini-pro")

        # Initialize the Gemini client
        self.client = ChatGoogleGenerativeAI(
            google_api_key=self.api_key,
            model=self.model_name,
            temperature=config_manager.get_llm_config().get("temperature", 0.7),
            max_output_tokens=config_manager.get_llm_config().get("max_tokens", 4096),
        )