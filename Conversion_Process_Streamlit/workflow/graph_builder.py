import os
import uuid
from typing import Dict, Any, Optional, Literal, Callable
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from config import ConfigManager
from pydantic import BaseModel, Field
from models import CoderOutput, TestGeneratorOutput


class WorkflowState(BaseModel):
    """Workflow state for code processing pipeline.

    This model tracks the state of code as it moves through the workflow,
    from input to final processed output with documentation and tests.
    """
    input_code: str = Field(
        description="Original input code to be processed"
    )
    coder_code: Optional[str] = Field(
        default=None,
        description="Code after documentation has been added"
    )
    human_feedback: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Human feedback data including approval status and comments"
    )
    final_code: Optional[str] = Field(
        default=None,
        description="Final code with tests added"
    )
    ai_review: Optional[str] = Field(
        default=None,
        description="AI-generated review of the documentation"
    )


class GraphBuilder:
    """Builds and manages the workflow graph for code processing with human-in-the-loop support.

    This class handles the creation, compilation, and execution of the LangGraph
    workflow that processes code through documentation addition, human review and approval,
    and test generation. It includes memory persistence using LangGraph's MemorySaver
    and human-in-the-loop functionality for Streamlit.
    """
    def __init__(self, llm: Any, config_manager: ConfigManager):
        """Initialize the GraphBuilder with LLM and configuration.

        Args:
            llm: The LLM implementation to use for code processing
            config_manager: Configuration manager for the application
        """
        self.llm = llm
        self.config_manager = config_manager
        self.graph = None
        self.compiled_graph = None
        self.memory_saver = MemorySaver()  # Initialize memory saver for persistence
        self.human_feedback_callback = None

    def coder(self, state: WorkflowState) -> Dict[str, str]:
        """Add documentation to the input code.

        Args:
            state: Current workflow state containing input code

        Returns:
            Dictionary with updated coder_code field
        """
        print('========== CODER NODE: Adding documentation to code ==========')
        print(f'Current state: {state.model_dump()}')
        try:
            # Create a prompt dictionary for the LLM
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert Python developer specializing in code documentation. Add clear, concise docstrings to the provided code following PEP 257 standards."
                },
                {
                    "role": "user",
                    "content": f"Please add proper docstrings to this Python code and return the complete documented code:\n\n{state.input_code}"
                }
            ]

            # Get structured output using the CoderOutput model
            structured_llm = self.llm.client.with_structured_output(CoderOutput)
            result = structured_llm.invoke(messages)

            return {"coder_code": result.coder_code}
        except Exception as e:
            print(f"Error in coder node: {str(e)}")
            return {"coder_code": f"Error processing code: {str(e)}"}


    def human_review(self, state: WorkflowState) -> Dict[str, Any]:
        """Human review of the code documentation.

        This node prepares the state for human review in Streamlit.
        It generates an AI review to help the human make a decision.

        Args:
            state: Current workflow state containing documented code

        Returns:
            Dictionary with the coder_code and AI review for the human to review
        """
        print('========== HUMAN REVIEW NODE: Preparing for human review ==========')
        print(f'Current state: {state.model_dump()}')

        # Generate an AI review to help the human
        try:
            # Create a prompt dictionary for the LLM
            messages = [
                {
                    "role": "system",
                    "content": "You are a code quality reviewer specializing in documentation standards. Check if the provided code has proper docstrings for all functions and classes."
                },
                {
                    "role": "user",
                    "content": f"Check if this code has proper docstrings for all functions and classes. Provide a detailed assessment of the documentation quality to help a human reviewer make a decision.\n\n{state.coder_code}"
                }
            ]

            # Get the review from the LLM
            review_result = self.llm.client.invoke(messages)
            ai_review = review_result.content if hasattr(review_result, 'content') else str(review_result)
        except Exception as e:
            print(f"Error generating AI review: {str(e)}")
            ai_review = "Error generating AI review. Please review the code manually."

        # In Streamlit, we'll wait for human feedback in the UI
        # For now, we'll just return the state with the AI review
        return {
            "coder_code": state.coder_code,
            "ai_review": ai_review
        }

    def set_human_feedback(self, feedback: Dict[str, Any]) -> None:
        """Set the human feedback callback function.

        Args:
            feedback: Dictionary containing human feedback
        """
        self.human_feedback = feedback
        if self.human_feedback_callback:
            self.human_feedback_callback(feedback)

    def register_human_feedback_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback function for human feedback.

        Args:
            callback: Function to call when human feedback is received
        """
        self.human_feedback_callback = callback

    def route_based_on_feedback(self, state: WorkflowState) -> Literal['approved', 'rejected', 'end']:
        """Determine next step based on human feedback.

        Args:
            state: Current workflow state containing human feedback

        Returns:
            'approved' if human approved and wants tests,
            'rejected' if human rejected,
            'end' if human approved but wants to end workflow
        """
        # Check if human_feedback exists
        if not state.human_feedback:
            # In Streamlit, we need to handle this case differently
            # We'll just return to the human_review node and wait for feedback
            print("========== ROUTING NODE: No human feedback provided yet ==========")
            print("Waiting for human feedback in Streamlit UI")
            # For Streamlit, we'll just stay in the current state
            # This is handled in the invoke_graph method
            return 'rejected'  # This won't actually be used in Streamlit mode

        # Check if the user wants to end the workflow directly
        if state.human_feedback.get("end_workflow", False):
            print("========== ROUTING NODE: Human chose to end workflow ==========")
            return 'end'

        approved = state.human_feedback.get("approved", False)
        print(f'========== ROUTING NODE: Human approved? {approved} ==========')

        if approved:
            return 'approved'
        else:
            return 'rejected'

    def test_generator(self, state: WorkflowState) -> Dict[str, str]:
        """Generate test cases for the documented code.

        Args:
            state: Current workflow state containing documented code

        Returns:
            Dictionary with generated test code
        """
        print('========== TEST GENERATOR NODE: Creating test cases ==========')
        print(f'Current state: {state.model_dump()}')
        try:
            # Create a prompt dictionary for the LLM
            messages = [
                {
                    "role": "system",
                    "content": "You are a test automation expert specializing in pytest. Create comprehensive test cases for the provided code that verify functionality."
                },
                {
                    "role": "user",
                    "content": f"Create pytest test cases for this code and include a description of the test coverage:\n\n{state.coder_code}"
                }
            ]

            # Get structured output using the TestGeneratorOutput model
            structured_llm = self.llm.client.with_structured_output(TestGeneratorOutput)
            result = structured_llm.invoke(messages)

            return {"final_code": result.final_code}
        except Exception as e:
            print(f"Error in test generator node: {str(e)}")
            return {"final_code": f"Error generating tests: {str(e)}"}


    def build_default_graph(self) -> None:
        """Build the default workflow graph for code processing.

        Creates a graph with the following flow:
        1. START -> coder (add documentation)
        2. coder -> human_review (human reviews documentation with AI assistance)
        3. human_review -> [conditional based on feedback]:
           - If human rejects ('rejected') -> back to coder
           - If human approves ('approved') -> test_generator
        4. test_generator -> END
        """
        self.graph = StateGraph(WorkflowState)

        # Add nodes to the graph
        self.graph.add_node("coder", self.coder)
        self.graph.add_node("human_review", self.human_review)
        self.graph.add_node("test_generator", self.test_generator)

        # Define the edges
        self.graph.add_edge(START, "coder")
        self.graph.add_edge("coder", "human_review")

        # Conditional edge based on human feedback
        self.graph.add_conditional_edges(
            "human_review",
            self.route_based_on_feedback,
            {
                'rejected': 'coder',  # If human rejects, go back to coder
                'approved': 'test_generator'  # If human approves, proceed to test generation
            }
        )

        # Final edge to end the workflow
        self.graph.add_edge("test_generator", END)

    def compile_graph(self) -> None:
        """Compile the graph for execution with memory persistence.

        This must be called after building the graph and before invoking it.
        The graph is compiled with a memory saver to enable persistence across runs.

        Raises:
            ValueError: If the graph has not been built yet
        """
        if not self.graph:
            raise ValueError("Graph not built. Call build_default_graph() first.")

        # Compile the graph with memory saver for persistence
        self.compiled_graph = self.graph.compile(
            checkpointer=self.memory_saver
        )


    def invoke_graph(self, input_data: Dict[str, Any], thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute the workflow graph with the provided input data.

        Args:
            input_data: Dictionary containing the input code to process
                       (must have 'input_code' key)
            thread_id: Optional thread ID for memory persistence. If not provided,
                      a new UUID will be generated.

        Returns:
            Dictionary containing the final workflow state

        Raises:
            ValueError: If the graph has not been compiled yet
            KeyError: If the input_data doesn't contain required keys
        """
        if not self.compiled_graph:
            raise ValueError("Graph not compiled. Call compile_graph() first.")

        if 'input_code' not in input_data and thread_id is None:
            raise KeyError("Input data must contain 'input_code' key for new workflows")

        # Generate a thread ID if not provided
        if thread_id is None:
            thread_id = str(uuid.uuid4())
            print(f"Generated new thread ID: {thread_id}")
        else:
            print(f"Using existing thread ID: {thread_id}")

        try:
            # Invoke the graph with the thread ID for memory persistence
            config = {"configurable": {"thread_id": thread_id}}

            # For Streamlit, we need to handle the workflow differently
            # If we're starting a new workflow (just input_code, no human_feedback)
            if 'input_code' in input_data and 'human_feedback' not in input_data:
                # We'll run just the coder node to get to human_review
                # First, create a proper WorkflowState
                if isinstance(input_data, dict) and not isinstance(input_data, WorkflowState):
                    # Convert dict to WorkflowState if needed
                    state = WorkflowState(**input_data)
                else:
                    state = input_data

                # Run the coder node
                coder_result = self.coder(state)

                # Update the state with the coder result
                updated_state = {**state.model_dump(), **coder_result}

                # Run the human_review node
                human_review_result = self.human_review(WorkflowState(**updated_state))

                # Return the final state for this stage
                final_state = {**updated_state, **human_review_result}
                return final_state

            # If we're continuing from human_review with feedback
            elif 'human_feedback' in input_data:
                # If human approved, run test_generator
                if input_data['human_feedback'].get('approved', False):
                    # Create a proper state object
                    if isinstance(input_data, dict) and not isinstance(input_data, WorkflowState):
                        state = WorkflowState(**input_data)
                    else:
                        state = input_data

                    # Run the test_generator node
                    test_result = self.test_generator(state)

                    # Return the final state
                    final_state = {**state.model_dump(), **test_result}
                    return final_state
                else:
                    # If human rejected, run coder again
                    if isinstance(input_data, dict) and not isinstance(input_data, WorkflowState):
                        state = WorkflowState(**input_data)
                    else:
                        state = input_data

                    # Run the coder node
                    coder_result = self.coder(state)

                    # Update the state with the coder result
                    updated_state = {**state.model_dump(), **coder_result}
                    updated_state.pop('human_feedback', None)  # Remove the human feedback

                    # Run the human_review node
                    human_review_result = self.human_review(WorkflowState(**updated_state))

                    # Return the final state for this stage
                    final_state = {**updated_state, **human_review_result}
                    return final_state

            # Default case - just run the workflow normally
            else:
                result = self.compiled_graph.invoke(input_data, config)
                return result

        except Exception as e:
            print(f"Error executing workflow: {str(e)}")
            raise


    def save_graph_visualization(self, output_path: Optional[str] = None) -> str:
        """Save a visualization of the workflow graph as a Mermaid diagram.

        Args:
            output_path: Path where the diagram should be saved
                        (defaults to 'flow.mmd' in current directory)

        Returns:
            Path to the saved diagram file

        Raises:
            ValueError: If the graph has not been built yet
        """
        if not self.graph:
            raise ValueError("Graph not built. Call build_default_graph() first.")

        if not output_path:
            output_path = os.path.join(os.getcwd(), "flow.mmd")

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # For LangGraph 0.3.x, we need to compile the graph first to get visualization
        if not self.compiled_graph:
            self.compile_graph()

        # Get the Mermaid diagram content
        mermaid_content = self.compiled_graph.get_graph().draw_mermaid()

        # Replace the default start and end node names
        mermaid_content = mermaid_content.replace("__start__([<p>__start__</p>]):::first", "Start([<p>Start</p>]):::first")
        mermaid_content = mermaid_content.replace("__end__([<p>__end__</p>]):::last", "End([<p>End</p>]):::last")
        mermaid_content = mermaid_content.replace("__start__ -->", "Start -->")
        mermaid_content = mermaid_content.replace("--> __end__", "--> End")
        mermaid_content = mermaid_content.replace(".-> __end__", ".-> End")

        # Remove any direct path from human_review to End
        mermaid_content = mermaid_content.replace("human_review -.-> End;", "")

        # Add styling for the human_review node
        if "classDef human" not in mermaid_content:
            mermaid_content += "\nclassDef human fill:#f9d5e5,stroke:#333,stroke-width:2px;"

        # Apply the human class to the human_review node
        mermaid_content = mermaid_content.replace("human_review(human_review)", "human_review(Human Review):::human")

        # Write the content to the file
        with open(output_path, 'w') as f:
            f.write(mermaid_content)
        return output_path
