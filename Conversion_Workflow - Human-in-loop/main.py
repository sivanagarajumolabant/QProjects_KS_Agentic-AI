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

    input_code = """@app.get('/')
    def home():
        return {"Message": 'Hello World'}"""

    # Start the workflow with the input code
    print("\n=== Starting workflow ===")
    result = graph_builder.start_workflow(input_code)
    task_id = result["task_id"]
    state = result["state"]

    print(f"\nWorkflow started with task ID: {task_id}")
    print("\nCurrent state:")

    # Access state values directly from the dictionary
    if isinstance(state, dict):
        print(f"Input code length: {len(state.get('input_code', ''))} characters")
        print(f"Output code length: {len(state.get('output_code', '')) if state.get('output_code') else 0} characters")
        output_code = state.get('output_code', '')
    else:
        print(f"Input code length: {len(state.input_code)} characters")
        print(f"Output code length: {len(state.output_code) if state.output_code else 0} characters")
        output_code = state.output_code

    # Display the code with documentation added by the LLM
    print("\n=== Human Review ===")
    print("The workflow is now waiting for human review.")
    print("Here's the code with documentation added by the LLM:")
    print("\n" + "=" * 50)
    print(output_code)
    print("=" * 50 + "\n")

    # Get human input
    while True:
        review_status = input("Do you approve this documentation? (approved/feedback): ").strip().lower()
        if review_status in ["approved", "feedback"]:
            break
        print("Invalid input. Please enter 'approved' or 'feedback'.")

    feedback = None
    if review_status == "feedback":
        feedback = input("Please provide your feedback: ")

    # Create the human review input
    human_review_input = {
        "status": review_status,
        "feedback": feedback
    }

    # Resume the workflow with human input
    print("\n=== Resuming workflow with human input ===")
    result = graph_builder.update_and_resume_workflow(task_id, human_review_input)
    final_state = result["state"]

    # Process the final state
    if isinstance(final_state, dict):
        final_output = final_state.get('output_code', '')
        review_status = final_state.get('human_review_status', '')
    else:
        final_output = final_state.output_code
        review_status = final_state.human_review_status

    # Display the final result
    print("\n=== Workflow completed ===")
    if review_status == "approved":
        print("Documentation was approved.")
    else:
        print("Documentation was updated based on feedback.")

    print("\nFinal code:")
    print("\n" + "=" * 50)
    print(final_output)
    print("=" * 50 + "\n")

    # Return the final state
    return final_state


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
