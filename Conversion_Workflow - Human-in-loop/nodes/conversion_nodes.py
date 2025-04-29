from state import WorkflowState, CodeOutput
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
            logger.error(f"Error in llm_invoke node: {str(e)}")
            return {"output_code": f"Error processing code: {str(e)}"}

    def review(self, state: WorkflowState) -> Dict[str, Any]:
        """Human review of the code documentation.

        This node is an interrupt point where the workflow waits for human input.
        It prepares the code for human review and will be interrupted before execution.

        Args:
            state: Current workflow state containing documented code

        Returns:
            Dictionary with updated state based on human review
        """
        logger.info('========== HUMAN REVIEW NODE: Processing human review ==========')

        # This function will be interrupted before execution by the LangGraph framework
        # When it resumes, it will have access to the human review input

        # The human review input should be provided when resuming the workflow
        # It should include status (approved/feedback) and feedback text if status is 'feedback'

        # Return the state with human review information
        # This will be used to determine the next step in the workflow
        return {
            "human_review_status": state.human_review_status,
            "human_feedback": state.human_feedback,
            "final_code": state.output_code if state.human_review_status == "approved" else None
        }

    def process_feedback(self, state: WorkflowState) -> Dict[str, Any]:
        """Process human feedback to improve the code.

        This node is called when human review status is 'feedback'.
        It uses the human feedback to improve the code documentation.

        Args:
            state: Current workflow state containing human feedback

        Returns:
            Dictionary with updated output code
        """
        try:
            # Get the current code and feedback
            current_code = state.output_code
            feedback = state.human_feedback

            # Create a more specific prompt for the LLM to improve the code based on feedback
            prompt = f"""You are an expert Python developer specializing in code documentation.
            You need to improve the documentation in the provided code based on human feedback.

            CURRENT CODE:
            {current_code}

            HUMAN FEEDBACK:
            {feedback}

            INSTRUCTIONS:
            1. Carefully analyze the human feedback
            2. Make specific improvements to the docstrings based on the feedback
            3. If the feedback asks for more detailed documentation, expand the docstrings with more information
            4. If the feedback mentions specific issues, address them directly
            5. Return the complete improved code with all the original functionality intact
            6. Only change the documentation, not the actual code logic

            Please update the code documentation according to the feedback and return the complete improved code.
            """

            structured_llm = self.llm.client.with_structured_output(CodeOutput)
            result = structured_llm.invoke(prompt)

            # Return the updated code
            return {"output_code": result.output_code}
        except Exception as e:
            logger.error(f"Error in process_feedback node: {str(e)}")
            return {"output_code": state.output_code}