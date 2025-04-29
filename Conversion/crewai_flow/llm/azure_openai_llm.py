from crewai import LLM
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AzureOpenAILLM:
    """Azure OpenAI LLM implementation for CrewAI."""

    def __init__(self):
        """Initialize the Azure OpenAI LLM with configuration.

        Args:
            config_manager: Not used, kept for compatibility with other LLM classes
        """
        # Get values from environment variables
        self.api_key = os.getenv("AZURE_API_KEY")
        self.api_base = os.getenv("AZURE_API_BASE")
        self.api_version = os.getenv("AZURE_API_VERSION")
        self.model = os.getenv("AZURE_MODEL")

        # Initialize the CrewAI LLM
        try:
            # For Azure OpenAI, we need to use the format 'azure/<deployment_name>'
            model_name = f"azure/{self.model}"

            # Initialize LLM directly with model and api_version
            self._client = LLM(model=model_name,
                              api_version=self.api_version)

            print(f"Successfully initialized Azure OpenAI client with model {model_name}")
            print(f"Using Azure API base: {self.api_base}")
            print(f"Using Azure API version: {self.api_version}")
        except Exception as e:
            print(f"Error initializing Azure OpenAI client: {str(e)}")
            raise

    @property
    def client(self):
        """Return the CrewAI LLM instance."""
        return self._client