import sys
import uuid
from typing import Dict, Any, Tuple
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
    return llm


def run_workflow(llm: Any) -> Dict[str, Any]:
    graph_builder = GraphBuilder(llm)
    graph_builder.setup_graph()
    graph_builder.save_graph_image(graph_builder.graph)

    input_code = {"input_code": """@app.get('/')
    def home():
        return {"Message": 'Hello World'}"""}

    # Create a unique thread ID for this workflow execution
    thread_id = f"thread_{uuid.uuid4()}"
    print(f"Using thread ID: {thread_id}")

    # Pass the thread ID to the invoke_graph method
    result = graph_builder.invoke_graph(input_code, thread_id=thread_id)
    return result


def main():
    try:
        llm = setup_application()
        result = run_workflow(llm)
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
