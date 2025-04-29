import sys
from typing import Any
from config import ConfigManager
from llm import (
    AzureOpenAILLM,
    OpenAILLM,
    AnthropicLLM,
    GroqLLM,
    GeminiLLM
)
from workflow import CodeProcessingFlow, plot_flow
from dotenv import load_dotenv
load_dotenv()


def create_llm(provider: str) -> Any:
    """Create an LLM instance based on the provider."""
    if provider == "azure_openai":
        return AzureOpenAILLM()
    elif provider == "openai":
        return OpenAILLM()
    elif provider == "anthropic":
        return AnthropicLLM()
    elif provider == "groq":
        return GroqLLM()
    elif provider == "gemini":
        return GeminiLLM()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def setup_application() -> Any:
    """Set up the application with configuration and LLM."""
    config_manager = ConfigManager()
    llm_provider = config_manager.get_llm_provider()

    try:
        print(f"Attempting to initialize {llm_provider} LLM...")
        llm = create_llm(llm_provider)
        print(f"Successfully initialized {llm_provider} LLM")
        return llm
    except Exception as e:
        print(f"Error initializing {llm_provider}: {str(e)}")
        sys.exit(1)


def run_code_processing():
    """Run the code processing flow using CrewAI Flow with Crew implementation."""
    # Initialize the LLM
    llm = setup_application()

    # Create the flow with crew implementation
    flow = CodeProcessingFlow(llm.client)

    # Set the input code
    flow.state.input_code = """@app.get('/')
def home():
    return {"Message": 'Hello World'}"""

    # Execute the flow (this will use the crew implementation internally)
    flow.kickoff()

    # Display the results
    print("\n=== WORKFLOW RESULT ===")
    if flow.state.test_code:
        print("\n=== FINAL CODE (TESTS) ===")
        print(flow.state.test_code)
    else:
        print("No test code generated.")

    print("\n=== Flow Complete ===")


def generate_flow_visualization():
    """Generate a visualization of the flow."""
    plot_flow()
    print("Flow visualization saved to code_processing_flow.html")


if __name__ == "__main__":
    run_code_processing()
    generate_flow_visualization()
