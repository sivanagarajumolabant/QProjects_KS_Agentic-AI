import os
import uuid
from typing import Dict, Any
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from state import WorkflowState
from nodes import Conversion_Flow_Nodes
from langchain_core.runnables.graph import MermaidDrawMethod



class GraphBuilder:
    def __init__(self, llm):
        self.llm = llm
        self.builder = StateGraph(WorkflowState)
        self.memory = MemorySaver()

    def build_graph(self):
        """
            Configure the graph by adding nodes, edges
        """
        # Create a new builder to avoid any cached nodes
        self.builder = StateGraph(WorkflowState)
        self.conversion_nodes = Conversion_Flow_Nodes(llm=self.llm)

        # Nodes
        self.builder.add_node("llm_node", self.conversion_nodes.llm_invoke)

        # Edges
        self.builder.add_edge(START, "llm_node")
        self.builder.add_edge("llm_node", END)

        return self.builder

    def setup_graph(self):
        builder = self.build_graph()
        self.graph = builder.compile(
            interrupt_before=[], checkpointer=self.memory
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
    
    def save_graph_image(self,graph):
        # Generate the PNG image
        img_data = graph.get_graph().draw_mermaid_png(
            draw_method=MermaidDrawMethod.API
            )

        # Save the image to a file
        graph_path = "workflow_graph.png"
        with open(graph_path, "wb") as f:
            f.write(img_data)   