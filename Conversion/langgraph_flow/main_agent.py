import sys
from typing import Dict, Any, Tuple

from config import ConfigManager
from llm import (
    AzureOpenAILLM,
    OpenAILLM,
    AnthropicLLM,
    GroqLLM,
    GeminiLLM
)
from workflow.agent_graph_builder import AgentGraphBuilder
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_llm(provider: str, config_manager: ConfigManager) -> Any:
    """Create an LLM instance based on the provider.

    Args:
        provider: The LLM provider name
        config_manager: Configuration manager for the application

    Returns:
        An LLM instance

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
        print(f"Successfully initialized {llm_provider} LLM")
        return config_manager, llm
    except Exception as e:
        print(f"Error initializing {llm_provider}: {str(e)}")
        sys.exit(1)


def run_workflow(config_manager: ConfigManager, llm: Any) -> Dict[str, Any]:
    """Run the agent-based workflow for code processing.

    Args:
        config_manager: Configuration manager for the application
        llm: The LLM implementation to use for code processing

    Returns:
        Dictionary containing the final workflow state
    """
    # Create the agent graph builder
    graph_builder = AgentGraphBuilder(llm, config_manager)

    # Build and compile the graph
    graph_builder.build_default_graph()
    graph_builder.compile_graph()

    # Save graph visualization
    output_path = "agent_flow.mmd"
    graph_file = graph_builder.save_graph_visualization(output_path)
    print(f"Graph visualization saved as '{graph_file}'")

    # Define input code
    input_code = {"input_code": """@app.get('/')
def home():
    return {"Message": 'Hello World'}"""}

    # Execute the workflow
    result = graph_builder.invoke_graph(input_code)
    return result


def main():
    """Main entry point for the agent-based workflow application."""
    try:
        # Set up the application
        config_manager, llm = setup_application()

        # Run the workflow
        result = run_workflow(config_manager, llm)
        print("\nWorkflow execution result:", result)

        print("\nExecution completed successfully!")

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
