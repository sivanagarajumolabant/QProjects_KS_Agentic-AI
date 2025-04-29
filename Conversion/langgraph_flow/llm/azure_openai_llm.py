from typing import List, Any, Optional
from langchain_openai import AzureChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from config import ConfigManager


class AzureOpenAILLM:

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        azure_config = config_manager.models_config.azure_openai
        self.api_key = azure_config.api_key
        self.endpoint = azure_config.endpoint
        self.deployment_name = azure_config.deployment_name
        self.model_name = azure_config.model_name
        self.api_version = azure_config.api_version


        # Initialize the Azure OpenAI client
        try:
            # Try with the standard initialization
            self.client = AzureChatOpenAI(
                azure_endpoint=self.endpoint,
                azure_deployment=self.deployment_name,
                api_key=self.api_key,
                api_version=self.api_version,
                temperature=azure_config.temperature,
            )
            print("Successfully initialized Azure OpenAI client")
        except Exception as e:
            print(f"Error initializing Azure OpenAI client: {str(e)}")

    def bind_tools(self, tools: List[Any], **kwargs) -> BaseChatModel:
        """Bind tools to the LLM.

        This method is required by LangGraph agents. It returns the LLM client with tools bound to it.

        Args:
            tools: List of tools to bind to the LLM
            **kwargs: Additional keyword arguments

        Returns:
            The LLM client with tools bound to it
        """
        # Since our custom LLM doesn't directly support tool binding,
        # we'll return the client which will be used for direct invocation
        return self.client.bind_tools(tools)