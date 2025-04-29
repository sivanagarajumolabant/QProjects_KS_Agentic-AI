from pydantic import BaseModel, Field
from typing import Optional


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


# Define the output schema
class CodeOutput(BaseModel):
    output_code: str = Field(description="The documented code")