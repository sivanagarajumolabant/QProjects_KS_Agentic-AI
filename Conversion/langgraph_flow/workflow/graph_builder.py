import os
from typing import Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, END, START
from config import ConfigManager
from pydantic import BaseModel, Field


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
    review_code: Optional[str] = Field(
        default=None,
        description="Review result indicating if documentation is sufficient"
    )
    final_code: Optional[str] = Field(
        default=None,
        description="Final code with tests added"
    )


class GraphBuilder:
    """Builds and manages the workflow graph for code processing.

    This class handles the creation, compilation, and execution of the LangGraph
    workflow that processes code through documentation addition, review, and test generation.
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

    def coder(self, state: WorkflowState) -> Dict[str, str]:
        """Add documentation to the input code.

        Args:
            state: Current workflow state containing input code

        Returns:
            Dictionary with updated coder_code field
        """
        print('========== CODER NODE: Adding documentation to code ==========')
        try:
            # Create a prompt dictionary for the LLM
            prompt = {
                "role": "user",
                "content": f"You are an expert Python developer specializing in code documentation. Add clear, concise docstrings to the provided code following PEP 257 standards.\n\nPlease add proper docstrings to this Python code and return the complete documented code:\n\n{state.input_code}"
            }
            data = self.llm.client.invoke([prompt])
            return {"coder_code": data.content}
        except Exception as e:
            print(f"Error in coder node: {str(e)}")
            return {"coder_code": f"Error processing code: {str(e)}"}

    def reviewer(self, state: WorkflowState) -> Dict[str, str]:
        """Review the code to check if documentation is sufficient.

        Args:
            state: Current workflow state containing documented code

        Returns:
            Dictionary with review result ('True' or 'False')
        """
        print('========== REVIEWER NODE: Checking documentation quality ==========')
        try:
            # Create a prompt dictionary for the LLM
            prompt = {
                "role": "user",
                "content": f"You are a code quality reviewer specializing in documentation standards. Check if the provided code has proper docstrings for all functions and classes. Respond with ONLY 'True' if documentation is sufficient or 'False' if not.\n\nCheck if this code has proper docstrings for all functions and classes:\n\n{state.coder_code}"
            }
            data = self.llm.client.invoke([prompt])
            # Normalize response to ensure it's exactly 'True' or 'False'
            response = data.content.strip()
            if 'true' in response.lower() and not 'false' in response.lower():
                return {"review_code": "True"}
            else:
                return {"review_code": "False"}
        except Exception as e:
            print(f"Error in reviewer node: {str(e)}")
            return {"review_code": "False"}

    def check_required(self, state: WorkflowState) -> Literal['True', 'False']:
        """Determine next step based on review result.

        Args:
            state: Current workflow state containing review result

        Returns:
            'True' if documentation is sufficient, 'False' if not
        """
        print(f'========== CHECK NODE: Documentation sufficient? {state.review_code} ==========')
        if state.review_code == 'True':
            return 'True'
        else:
            return 'False'

    def test_generator(self, state: WorkflowState) -> Dict[str, str]:
        """Generate test cases for the documented code.

        Args:
            state: Current workflow state containing documented code

        Returns:
            Dictionary with generated test code
        """
        print('========== TEST GENERATOR NODE: Creating test cases ==========')
        try:
            # Create a prompt dictionary for the LLM
            prompt = {
                "role": "user",
                "content": f"You are a test automation expert specializing in pytest. Create comprehensive test cases for the provided code that verify functionality.\n\nCreate pytest test cases for this code:\n\n{state.coder_code}"
            }
            data = self.llm.client.invoke([prompt])
            return {"final_code": data.content}
        except Exception as e:
            print(f"Error in test generator node: {str(e)}")
            return {"final_code": f"Error generating tests: {str(e)}"}



    def build_default_graph(self) -> None:
        """Build the default workflow graph for code processing.

        Creates a graph with the following flow:
        1. START -> coder (add documentation)
        2. coder -> reviewer (check documentation)
        3. reviewer -> [conditional]:
           - If documentation insufficient (False) -> back to coder
           - If documentation sufficient (True) -> test_generator
        4. test_generator -> END
        """
        self.graph = StateGraph(WorkflowState)

        # Add nodes to the graph
        self.graph.add_node("coder", self.coder)
        self.graph.add_node("reviewer", self.reviewer)
        self.graph.add_node("test_generator", self.test_generator)

        # Define the edges
        self.graph.add_edge(START, "coder")
        self.graph.add_edge("coder", "reviewer")

        # Conditional edge based on review result
        self.graph.add_conditional_edges(
            "reviewer",
            self.check_required,
            {
                'False': 'coder',  # If docs insufficient, go back to coder
                'True': 'test_generator'  # If docs sufficient, proceed to test generation
            }
        )

        # Final edge to end the workflow
        self.graph.add_edge("test_generator", END)

    def compile_graph(self) -> None:
        """Compile the graph for execution.

        This must be called after building the graph and before invoking it.

        Raises:
            ValueError: If the graph has not been built yet
        """
        if not self.graph:
            raise ValueError("Graph not built. Call build_default_graph() first.")

        self.compiled_graph = self.graph.compile()

    def invoke_graph(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow graph with the provided input data.

        Args:
            input_data: Dictionary containing the input code to process
                       (must have 'input_code' key)

        Returns:
            Dictionary containing the final workflow state

        Raises:
            ValueError: If the graph has not been compiled yet
            KeyError: If the input_data doesn't contain required keys
        """
        if not self.compiled_graph:
            raise ValueError("Graph not compiled. Call compile_graph() first.")

        if 'input_code' not in input_data:
            raise KeyError("Input data must contain 'input_code' key")

        try:
            result = self.compiled_graph.invoke(input_data)
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

        # Write the content to the file
        with open(output_path, 'w') as f:
            f.write(mermaid_content)
        return output_path
