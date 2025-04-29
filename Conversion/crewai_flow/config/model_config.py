import os
import dotenv
from pydantic import BaseModel, Field

dotenv.load_dotenv()


class AzureOpenAIConfig(BaseModel):
    """Azure OpenAI model configuration."""
    api_key: str = Field(
        default=os.getenv("AZURE_OPENAI_API_KEY", "default-key-for-testing").strip(),
        description="Azure OpenAI API key"
    )
    endpoint: str = Field(
        default=os.getenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/").strip(),
        description="Azure OpenAI endpoint"
    )
    deployment_name: str = Field(
        default="gpt4-deployment",  # Hardcoded deployment name
        description="Azure OpenAI deployment name"
    )
    model_name: str = Field(
        default=os.getenv("AZURE_OAI_MODEL", "gpt-4o"),
        description="Azure OpenAI model name"
    )
    api_version: str = Field(
        default="2023-08-01-preview",  # Hardcoded API version
        description="Azure OpenAI API version"
    )
    temperature: float = Field(
        default=float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.7")),
        description="Temperature for generation"
    )
    max_tokens: int = Field(
        default=int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "4096")),
        description="Maximum number of tokens to generate"
    )


class OpenAIConfig(BaseModel):
    """OpenAI model configuration."""
    api_key: str = Field(
        default=os.getenv("OPENAI_API_KEY", "default-key-for-testing"),
        description="OpenAI API key"
    )
    model_name: str = Field(
        default=os.getenv("OPENAI_MODEL", "gpt-4o"),
        description="OpenAI model name"
    )
    temperature: float = Field(
        default=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        description="Temperature for generation"
    )
    max_tokens: int = Field(
        default=int(os.getenv("OPENAI_MAX_TOKENS", "4096")),
        description="Maximum number of tokens to generate"
    )


class AnthropicConfig(BaseModel):
    """Anthropic model configuration."""
    api_key: str = Field(
        default=os.getenv("ANTHROPIC_API_KEY", "default-key-for-testing"),
        description="Anthropic API key"
    )
    model_name: str = Field(
        default=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229"),
        description="Anthropic model name"
    )
    temperature: float = Field(
        default=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7")),
        description="Temperature for generation"
    )
    max_tokens: int = Field(
        default=int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096")),
        description="Maximum number of tokens to generate"
    )


class GroqConfig(BaseModel):
    """Groq model configuration."""
    api_key: str = Field(
        default=os.getenv("GROQ_API_KEY", "default-key-for-testing"),
        description="Groq API key"
    )
    model_name: str = Field(
        default=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
        description="Groq model name"
    )
    temperature: float = Field(
        default=float(os.getenv("GROQ_TEMPERATURE", "0.7")),
        description="Temperature for generation"
    )
    max_tokens: int = Field(
        default=int(os.getenv("GROQ_MAX_TOKENS", "4096")),
        description="Maximum number of tokens to generate"
    )


class OllamaConfig(BaseModel):
    """Ollama model configuration."""
    base_url: str = Field(
        default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        description="Ollama base URL"
    )
    model_name: str = Field(
        default=os.getenv("OLLAMA_MODEL", "llama3"),
        description="Ollama model name"
    )
    temperature: float = Field(
        default=float(os.getenv("OLLAMA_TEMPERATURE", "0.7")),
        description="Temperature for generation"
    )
    max_tokens: int = Field(
        default=int(os.getenv("OLLAMA_MAX_TOKENS", "4096")),
        description="Maximum number of tokens to generate"
    )


class GeminiConfig(BaseModel):
    """Google Gemini model configuration."""
    api_key: str = Field(
        default=os.getenv("GEMINI_API_KEY", "default-key-for-testing"),
        description="Google API key for Gemini"
    )
    model_name: str = Field(
        default=os.getenv("GEMINI_MODEL", "gemini-pro"),
        description="Gemini model name"
    )
    temperature: float = Field(
        default=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
        description="Temperature for generation"
    )
    max_tokens: int = Field(
        default=int(os.getenv("GEMINI_MAX_TOKENS", "4096")),
        description="Maximum number of tokens to generate"
    )


class ModelConfig(BaseModel):
    """Model configuration for all supported LLM providers."""
    azure_openai: AzureOpenAIConfig = Field(
        default_factory=AzureOpenAIConfig,
        description="Azure OpenAI configuration"
    )
    openai: OpenAIConfig = Field(
        default_factory=OpenAIConfig,
        description="OpenAI configuration"
    )
    anthropic: AnthropicConfig = Field(
        default_factory=AnthropicConfig,
        description="Anthropic configuration"
    )
    groq: GroqConfig = Field(
        default_factory=GroqConfig,
        description="Groq configuration"
    )
    ollama: OllamaConfig = Field(
        default_factory=OllamaConfig,
        description="Ollama configuration"
    )
    gemini: GeminiConfig = Field(
        default_factory=GeminiConfig,
        description="Google Gemini configuration"
    )


# Create a default model configuration
default_model_config = ModelConfig()
