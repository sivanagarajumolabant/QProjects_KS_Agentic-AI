import sys
import uuid
from typing import Dict, Any, Tuple, Optional
from config import ConfigManager
from llm import (
    AzureOpenAILLM,
    OpenAILLM,
    AnthropicLLM,
    GroqLLM,
    GeminiLLM
)
from workflow import GraphBuilder
from dotenv import load_dotenv
load_dotenv()


def create_llm(provider: str, config_manager: ConfigManager) -> Any:
    """Create an LLM instance based on the provider.

    Args:
        provider: The LLM provider name
        config_manager: The configuration manager

    Returns:
        An instance of the appropriate LLM class

    Raises:
        ValueError: If the provider is not supported
    """
    if provider == "azure_openai":
        return AzureOpenAILLM(config_manager)
    elif provider == "openai":
        return OpenAILLM(config_manager)
    elif provider == "anthropic":
        return AnthropicLLM(config_manager)
    elif provider == "groq":
        return GroqLLM(config_manager)
    elif provider == "gemini":
        return GeminiLLM(config_manager)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def setup_application() -> Tuple[ConfigManager, Any]:
    """Set up the application with configuration and LLM.

    Returns:
        A tuple containing the configuration manager and LLM instance
    """
    config_manager = ConfigManager()
    llm_provider = config_manager.get_llm_provider()

    try:
        print(f"Attempting to initialize {llm_provider} LLM...")
        llm = create_llm(llm_provider, config_manager)
    except Exception as e:
        print(f"Error initializing {llm_provider}: {str(e)}")
    return config_manager, llm


def run_workflow(config_manager: ConfigManager, llm: Any, thread_id: Optional[str] = None, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run the workflow with the provided configuration and LLM.

    Args:
        config_manager: Configuration manager for the application
        llm: The LLM implementation to use for code processing
        thread_id: Optional thread ID for memory persistence
        input_data: Optional input data for the workflow

    Returns:
        Dictionary containing the final workflow state
    """
    graph_builder = GraphBuilder(llm, config_manager)
    graph_builder.build_default_graph()
    graph_builder.compile_graph()
    output_path = "flow.mmd"
    graph_file = graph_builder.save_graph_visualization(output_path)
    print(f"Graph visualization saved as '{graph_file}'")

    # Use provided input data or default
    if input_data is None:
        input_data = {"input_code": """@app.get('/')
    def home():
        return {"Message": 'Hello World'}"""}

    # Use the provided thread_id or let the graph_builder generate one
    result = graph_builder.invoke_graph(input_data, thread_id)
    return result





def main():
    """Main entry point for the application."""
    try:
        config_manager, llm = setup_application()
        thread_id = str(uuid.uuid4())
        print(f"Starting workflow with thread ID: {thread_id}")

        result = run_workflow(config_manager, llm, thread_id)
        print("\nWorkflow execution result:", result)

        print("\nExecution completed successfully!")
        print(f"To continue this workflow later, use thread ID: {thread_id}")

        print(f"To continue this workflow later, use thread ID: {thread_id}")

    except ValueError as e:
        print(f"\nConfiguration Error: {str(e)}")
        print("\nPlease check your configuration and try again.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected Error: {str(e)}")
        print("\nPlease report this issue with the error details above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
