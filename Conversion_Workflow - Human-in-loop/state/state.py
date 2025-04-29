from pydantic import BaseModel, Field
from typing import Optional, Literal


class WorkflowState(BaseModel):
    """Workflow state for code processing pipeline.

    This model tracks the state of code as it moves through the workflow
    """
    input_code: str = Field(
        description="Original input code to be processed"
    )
    output_code: Optional[str] = Field(
        default=None,
        description="Code after documentation has been added"
    )
    human_review_status: Optional[Literal["approved", "feedback"]] = Field(
        default=None,
        description="Status of human review: 'approved' or 'feedback'"
    )
    human_feedback: Optional[str] = Field(
        default=None,
        description="Feedback provided by human reviewer when status is 'feedback'"
    )
    final_code: Optional[str] = Field(
        default=None,
        description="Final code after all processing steps"
    )


# Define the output schema
class CodeOutput(BaseModel):
    output_code: str = Field(description="The documented code")


# Define the human review input schema
class HumanReviewInput(BaseModel):
    status: Literal["approved", "feedback"] = Field(
        description="Status of the review: 'approved' or 'feedback'"
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Feedback provided when status is 'feedback'"
    )