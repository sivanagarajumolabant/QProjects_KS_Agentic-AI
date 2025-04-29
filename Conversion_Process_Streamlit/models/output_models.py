from pydantic import BaseModel, Field
from typing import Optional, Literal


class CoderOutput(BaseModel):
    """Output model for the coder node.
    
    This model represents the structured output from the coder node,
    which adds documentation to the input code.
    """
    coder_code: str = Field(
        description="Code with documentation added"
    )
    explanation: Optional[str] = Field(
        default=None,
        description="Explanation of the changes made to the code"
    )


class ReviewerOutput(BaseModel):
    """Output model for the reviewer node.
    
    This model represents the structured output from the reviewer node,
    which checks if the documentation is sufficient.
    """
    review_code: Literal["True", "False"] = Field(
        description="Whether the documentation is sufficient ('True' or 'False')"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Reason for the review decision"
    )


class TestGeneratorOutput(BaseModel):
    """Output model for the test generator node.
    
    This model represents the structured output from the test generator node,
    which generates test cases for the documented code.
    """
    final_code: str = Field(
        description="Generated test code"
    )
    test_coverage: Optional[str] = Field(
        default=None,
        description="Description of the test coverage"
    )
