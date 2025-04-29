from state import WorkflowState, CodeOutput
from typing import Dict, Any
from pydantic import BaseModel, Field


class Conversion_Flow_Nodes:
    def __init__(self, llm):
        self.llm = llm

    def llm_invoke(self, state: WorkflowState) -> Dict[str, Any]:
        """Invoke the LLM to process the input code.

        This node is responsible for invoking the LLM to process the input code.
        It updates the state with the output code.

        Args:
            state: Current workflow state containing input code

        Returns:
            Dictionary containing the output code
        """
        try:
            # Get the input code from the state
            input_code = state.input_code

            # Create a prompt string for the LLM
            prompt = f"You are an expert Python developer specializing in code documentation. Add clear, concise docstrings to the provided code following PEP 257 standards.\n\nPlease add proper docstrings to this Python code and return the complete documented code:\n\n{input_code}"

            structured_llm = self.llm.client.with_structured_output(CodeOutput)
            result = structured_llm.invoke(prompt)

            # Return the updated state
            return {"output_code": result.output_code}
        except Exception as e:
            print(f"Error in llm_invoke node: {str(e)}")
            return {"output_code": f"Error processing code: {str(e)}"}
