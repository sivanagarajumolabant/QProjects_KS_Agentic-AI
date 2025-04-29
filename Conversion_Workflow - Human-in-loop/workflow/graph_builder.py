import os
import uuid
import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from state import WorkflowState
from nodes import Conversion_Flow_Nodes
from langchain_core.runnables.graph import MermaidDrawMethod


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphBuilder:
    def __init__(self, llm):
        self.llm = llm
        self.builder = StateGraph(WorkflowState)
        self.memory = MemorySaver()
        self.graph = None
        self.states = {}  # Dictionary to store states by thread ID

    def build_graph(self):
        """
            Configure the graph by adding nodes, edges
        """
        # Create a new builder to avoid any cached nodes
        self.builder = StateGraph(WorkflowState)
        self.conversion_nodes = Conversion_Flow_Nodes(llm=self.llm)

        # Nodes
        self.builder.add_node("llm_node", self.conversion_nodes.llm_invoke)
        self.builder.add_node("review", self.conversion_nodes.review)
        self.builder.add_node("process_feedback", self.conversion_nodes.process_feedback)

        # Define the conditional edge from review
        def route_based_on_review(state: WorkflowState) -> Literal["approved", "feedback"]:
            """Route the workflow based on human review status."""
            if state.human_review_status == "approved":
                return "approved"
            else:
                return "feedback"

        # Edges
        self.builder.add_edge(START, "llm_node")
        self.builder.add_edge("llm_node", "review")

        # Add conditional routing from review node
        self.builder.add_conditional_edges(
            "review",
            route_based_on_review,
            {
                "approved": END,
                "feedback": "process_feedback"
            }
        )

        # Add edge from process_feedback back to llm_node for another review cycle
        self.builder.add_edge("process_feedback", "llm_node")

        return self.builder

    def setup_graph(self):
        """
        Set up and compile the graph with interrupt_before for human review.
        """
        builder = self.build_graph()
        self.graph = builder.compile(
            interrupt_before=["review"], checkpointer=self.memory
        )
        return self.graph

    def invoke_graph(self, input_data: Dict[str, Any], thread_id: str = None) -> Dict[str, Any]:
        """
        Invoke the graph with the given input data.

        Args:
            input_data: Dictionary containing the input data for the workflow
            thread_id: Optional thread ID for the workflow execution

        Returns:
            Dictionary containing the workflow result
        """
        thread_id = thread_id or f"thread_{uuid.uuid4()}"
        thread = {"configurable": {"thread_id": thread_id}}
        return self.graph.invoke(input_data, config=thread)

    def get_thread(self, thread_id: str) -> Dict[str, Dict[str, str]]:
        """
        Get the thread configuration for a given thread ID.

        Args:
            thread_id: The thread ID

        Returns:
            Thread configuration dictionary
        """
        return {"configurable": {"thread_id": thread_id}}

    def start_workflow(self, input_code: str) -> Dict[str, Any]:
        """
        Start the workflow with the given input code.

        Args:
            input_code: The input code to process

        Returns:
            Dictionary with task_id and initial state
        """
        if not self.graph:
            self.setup_graph()

        # Generate a unique task id
        task_id = f"conversion-workflow-{uuid.uuid4().hex[:8]}"

        thread = self.get_thread(task_id)

        # Start the workflow
        input_data = {"input_code": input_code}
        state = self.graph.invoke(input_data, config=thread)
        print({"task_id": task_id, "state": state})
        # Store the state
        self.states[task_id] = state

        # Return the task ID and state
        return {"task_id": task_id, "state": state}

    def update_and_resume_workflow(self, task_id: str, human_review_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the workflow state with human review input and resume execution.

        Args:
            task_id: The task ID of the workflow
            human_review_input: Dictionary containing human review status and feedback

        Returns:
            Dictionary with updated state
        """
        if not self.graph:
            raise ValueError("Graph not initialized. Call setup_graph() first.")

        thread = self.get_thread(task_id)

        # Get the current state from our dictionary
        if task_id not in self.states:
            raise ValueError(f"No state found for task ID: {task_id}")

        current_state = self.states[task_id]

        # Create a new state with the human review input
        new_state = dict(current_state)
        new_state["human_review_status"] = human_review_input["status"]
        new_state["human_feedback"] = human_review_input.get("feedback", None)

        # Update our stored state
        self.states[task_id] = new_state

        # Resume the graph from the review node
        self.graph.update_state(thread, new_state, as_node="review")

        # Continue execution
        result = self.graph.invoke(None, config=thread)

        # Update our stored state with the result
        self.states[task_id] = result

        return {"task_id": task_id, "state": result}

    def save_graph_image(self, graph=None):
        """
        Generate and save a visualization of the graph.

        Args:
            graph: Optional graph to visualize. If None, uses self.graph.
        """
        graph = graph or self.graph
        if not graph:
            graph = self.setup_graph()

        # Generate the PNG image
        img_data = graph.get_graph().draw_mermaid_png(
            draw_method=MermaidDrawMethod.API
            )

        # Save the image to a file
        graph_path = "workflow_graph.png"
        with open(graph_path, "wb") as f:
            f.write(img_data)

        logger.info(f"Graph visualization saved to {graph_path}")
        return graph_path