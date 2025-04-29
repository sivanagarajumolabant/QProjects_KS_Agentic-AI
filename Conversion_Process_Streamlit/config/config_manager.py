"""Configuration manager for QMigrator AI."""

import os
from typing import Optional
from pydantic import BaseModel, Field
from config.model_config import (
    ModelConfig,
    default_model_config,
    AzureOpenAIConfig,
    OpenAIConfig,
    AnthropicConfig,
    GroqConfig,
    OllamaConfig,
    GeminiConfig
)


class ConfigManager(BaseModel):
    """Simple configuration with Pydantic validation."""
    # LLM settings
    provider: str = Field(
        default="azure_openai",
        description="LLM provider (azure_openai, openai, anthropic, groq, ollama)"
    )

    # Model configuration
    models_config: ModelConfig = Field(
        default_factory=lambda: default_model_config,
        description="Model configuration for all supported LLM providers"
    )

    # Workflow settings
    output_path: Optional[str] = Field(
        default="output",
        description="Path to save the output"
    )

    def __init__(self, **data):
        super().__init__(**data)
        self.load_from_env()

    def get_llm_provider(self) -> str:
        """Get the LLM provider (legacy method)."""
        return self.provider

    def set_llm_provider(self, provider: str):
        """Set the LLM provider (legacy method)."""
        self.provider = provider

    def get_llm_config(self):
        """Get LLM configuration as a dictionary."""
        if self.provider == "azure_openai":
            return self.models_config.azure_openai.model_dump()
        elif self.provider == "openai":
            return self.models_config.openai.model_dump()
        elif self.provider == "anthropic":
            return self.models_config.anthropic.model_dump()
        elif self.provider == "groq":
            return self.models_config.groq.model_dump()
        elif self.provider == "ollama":
            return self.models_config.ollama.model_dump()
        elif self.provider == "gemini":
            return self.models_config.gemini.model_dump()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def get_workflow_config(self):
        """Get workflow configuration as a dictionary."""
        return {
            "output_path": self.output_path
        }

    def load_from_env(self):
        """Load configuration from environment variables."""
        # Load provider from environment
        provider = os.getenv('LLM_PROVIDER')
        if provider:
            self.provider = provider

        # Load output path from environment
        output_path = os.getenv('OUTPUT_PATH')
        if output_path:
            self.output_path = output_path

        # Since we're now loading all values directly in the model_config.py file,
        # we don't need to manually set each field here.
        # We just need to create new instances of the config classes to ensure
        # they load their values from environment variables.

        # Load Azure OpenAI configuration
        if self.provider == 'azure_openai':
            self.models_config.azure_openai = AzureOpenAIConfig()

        # Load OpenAI configuration
        elif self.provider == 'openai':
            self.models_config.openai = OpenAIConfig()

        # Load Anthropic configuration
        elif self.provider == 'anthropic':
            self.models_config.anthropic = AnthropicConfig()

        # Load Groq configuration
        elif self.provider == 'groq':
            self.models_config.groq = GroqConfig()

        # Load Gemini configuration
        elif self.provider == 'gemini':
            self.models_config.gemini = GeminiConfig()

        # Load Ollama configuration
        elif self.provider == 'ollama':
            self.models_config.ollama = OllamaConfig()
