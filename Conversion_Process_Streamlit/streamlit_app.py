import streamlit as st
import uuid
from typing import Any
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


def setup_application() -> tuple[ConfigManager, Any]:
    """Set up the application with configuration and LLM.

    Returns:
        A tuple containing the configuration manager and LLM instance
    """
    config_manager = ConfigManager()
    llm_provider = config_manager.get_llm_provider()

    try:
        st.sidebar.info(f"Initializing {llm_provider} LLM...")
        llm = create_llm(llm_provider, config_manager)
        st.sidebar.success(f"Successfully initialized {llm_provider} LLM")
    except Exception as e:
        st.sidebar.error(f"Error initializing {llm_provider}: {str(e)}")
        st.stop()
    return config_manager, llm


def initialize_session_state():
    """Initialize the session state variables."""
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())

    if "config_manager" not in st.session_state or "graph_builder" not in st.session_state:
        config_manager, llm = setup_application()
        st.session_state.config_manager = config_manager
        st.session_state.graph_builder = GraphBuilder(llm, config_manager)
        st.session_state.graph_builder.build_default_graph()
        st.session_state.graph_builder.compile_graph()

    if "workflow_state" not in st.session_state:
        st.session_state.workflow_state = None

    if "current_step" not in st.session_state:
        st.session_state.current_step = "input"

    if "human_review_completed" not in st.session_state:
        st.session_state.human_review_completed = False


def display_workflow_diagram():
    """Display the workflow diagram."""
    st.sidebar.subheader("Workflow Diagram")

    # Generate and save the diagram
    if "graph_builder" in st.session_state:
        diagram_path = st.session_state.graph_builder.save_graph_visualization("flow.mmd")

        # Read the diagram content
        with open(diagram_path, 'r') as f:
            diagram_content = f.read()

        # Display the diagram using Mermaid
        st.sidebar.markdown(f"```mermaid\n{diagram_content}\n```")


def run_workflow(input_code: str):
    """Run the workflow with the provided input code.

    Args:
        input_code: The input code to process
    """
    graph_builder = st.session_state.graph_builder
    thread_id = st.session_state.thread_id

    # Prepare input data
    input_data = {"input_code": input_code}

    try:
        # Start the workflow and run until human review
        with st.spinner("Processing code..."):
            # We'll run the workflow and it will stop at the human review node
            result = graph_builder.invoke_graph(input_data, thread_id)

            # Store the result in session state
            st.session_state.workflow_state = result

            # Check if we have ai_review (human review step)
            if "ai_review" in result:
                st.session_state.current_step = "human_review"
            # Check if we have final_code (completed)
            elif "final_code" in result and result["final_code"] is not None:
                st.session_state.current_step = "completed"
            else:
                # Default to human review if we're not sure
                st.session_state.current_step = "human_review"
    except Exception as e:
        st.error(f"Error running workflow: {str(e)}")


def handle_human_feedback(approved: bool, comments: str):
    """Handle human feedback and continue the workflow.

    Args:
        approved: Whether the human approved the documentation
        comments: Comments from the human reviewer
    """
    graph_builder = st.session_state.graph_builder
    thread_id = st.session_state.thread_id

    # Prepare human feedback
    human_feedback = {
        "approved": approved,
        "comments": comments
    }

    # Create a new state with the human feedback
    current_state = dict(st.session_state.workflow_state)
    current_state["human_feedback"] = human_feedback

    try:
        # Continue the workflow from human review
        with st.spinner("Processing feedback..."):
            # Continue the workflow with the updated state
            result = graph_builder.invoke_graph(current_state, thread_id)
            st.session_state.workflow_state = result

            # Check if we have final_code (test generation completed)
            if "final_code" in result and result["final_code"] is not None:
                st.session_state.current_step = "completed"
            else:
                # If we don't have final_code, we're still in the human review step
                st.session_state.current_step = "human_review"

            st.session_state.human_review_completed = True
    except Exception as e:
        st.error(f"Error processing feedback: {str(e)}")


def input_code_page():
    """Display the input code page."""
    st.title("Code Documentation and Test Generator")
    st.write("Enter your Python code below to add documentation and generate tests.")

    # Default code example
    default_code = """@app.get('/')
def home():
    return {"Message": 'Hello World'}"""

    # Code input
    input_code = st.text_area("Input Code", value=default_code, height=200)

    # LLM provider selection in sidebar
    st.sidebar.subheader("LLM Provider")
    providers = ["azure_openai", "openai", "anthropic", "groq", "gemini"]
    selected_provider = st.sidebar.selectbox("Select LLM Provider", providers)

    # Update provider if changed
    if "config_manager" in st.session_state and st.session_state.config_manager.provider != selected_provider:
        st.session_state.config_manager.set_llm_provider(selected_provider)
        # Reinitialize the LLM
        st.session_state.pop("graph_builder", None)
        initialize_session_state()

    # Process button
    if st.button("Process Code"):
        if input_code.strip():
            run_workflow(input_code)
            st.rerun()
        else:
            st.error("Please enter some code to process.")


def human_review_page():
    """Display the human review page."""
    st.title("Human Review")
    st.write("Review the documentation added to your code.")

    # Get the current state
    state = st.session_state.workflow_state

    # Display the original code
    st.subheader("Original Code")
    st.code(state["input_code"], language="python")

    # Display the code with documentation
    st.subheader("Code with Documentation")
    st.code(state["coder_code"], language="python")

    # Display the AI review
    st.subheader("AI Review")
    st.write(state["ai_review"])

    # Human feedback form
    st.subheader("Your Feedback")
    comments = st.text_area("Comments", value="", height=100)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Reject & Improve"):
            handle_human_feedback(False, comments)
            st.rerun()

    with col2:
        if st.button("Approve & Generate Tests"):
            handle_human_feedback(True, comments)
            st.rerun()


def completed_page():
    """Display the completed workflow page."""
    st.title("Workflow Completed")
    st.write("The code processing workflow has been completed successfully.")

    # Get the current state
    state = st.session_state.workflow_state

    # Display tabs for different stages
    tab1, tab2, tab3 = st.tabs(["Original Code", "Documented Code", "Generated Tests"])

    with tab1:
        st.subheader("Original Code")
        st.code(state["input_code"], language="python")

    with tab2:
        st.subheader("Code with Documentation")
        st.code(state["coder_code"], language="python")

    with tab3:
        st.subheader("Generated Tests")
        st.code(state["final_code"], language="python")

    # Option to start a new workflow
    if st.button("Start New Workflow"):
        # Reset session state
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.workflow_state = None
        st.session_state.current_step = "input"
        st.session_state.human_review_completed = False
        st.rerun()


def main():
    """Main entry point for the Streamlit application."""
    st.set_page_config(
        page_title="Code Documentation & Test Generator",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize session state
    initialize_session_state()

    # Display workflow diagram in sidebar
    display_workflow_diagram()

    # Display thread ID in sidebar
    st.sidebar.subheader("Session Information")
    st.sidebar.info(f"Thread ID: {st.session_state.thread_id}")

    # Display the appropriate page based on the current step
    if st.session_state.current_step == "input":
        input_code_page()
    elif st.session_state.current_step == "human_review":
        human_review_page()
    elif st.session_state.current_step == "completed":
        completed_page()


if __name__ == "__main__":
    main()
