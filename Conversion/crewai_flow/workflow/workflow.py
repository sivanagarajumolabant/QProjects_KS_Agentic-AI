from typing import Optional
from pydantic import Field
from crewai import Crew, Process
from crewai.flow.flow import Flow, listen, start, router
from crews.code_processing_crew import (
    CodeProcessingCrew,
    CodeProcessingResult,
    AddDocumentationInput,
    ReviewDocumentationInput,
    ImproveDocumentationInput,
    GenerateTestsInput
)


class WorkflowState(CodeProcessingResult):
    """Workflow state for code processing pipeline.

    This model tracks the state of code as it moves through the workflow,
    from input to final processed output with documentation and tests.

    It extends the CodeProcessingResult model to ensure consistency between
    the workflow state and the crew results.
    """

    # Override fields with default values
    input_code: str = Field(
        default="",
        description="Original input code to be processed"
    )
    documented_code: Optional[str] = Field(
        default=None,
        description="Code after documentation has been added"
    )
    review_result: Optional[str] = Field(
        default=None,
        description="Review result indicating if documentation is sufficient"
    )
    test_code: Optional[str] = Field(
        default=None,
        description="Final code with tests added"
    )


class CodeProcessingFlow(Flow[WorkflowState]):
    """Flow for processing code through documentation, review, and test generation.

    This class implements a CrewAI Flow that processes code through a series of steps:
    1. Add documentation to the code
    2. Review the documentation
    3. If the documentation is insufficient, go back to step 1
    4. Generate test cases for the code
    """

    def __init__(self, llm_config):
        """Initialize the CodeProcessingFlow with an LLM configuration.

        Args:
            llm_config: The LLM configuration to use for processing
        """
        super().__init__()
        self.llm_config = llm_config

        # Create the code processing crew
        self.code_processing_crew = CodeProcessingCrew(llm=self.llm_config)

    @start()
    def process_input_code(self):
        """Start the code processing flow with the input code.

        Returns:
            The input code to be processed
        """
        print("\n========== STARTING CODE PROCESSING FLOW ==========\n")
        print(f"Processing input code:\n{self.state.input_code}\n")
        return self.state.input_code

    @listen(process_input_code)
    def add_documentation(self, code):
        """Add documentation to the input code using the crew.

        Args:
            code: The code to document

        Returns:
            The documented code
        """
        print("\n========== ADDING DOCUMENTATION TO CODE ==========\n")

        # Create a crew with just the add_documentation task
        crew = Crew(
            agents=[self.code_processing_crew.code_documentation_specialist()],
            tasks=[self.code_processing_crew.add_documentation_task()],
            process=Process.sequential,
            verbose=True
        )

        # Execute the crew with a structured input using Pydantic model
        task_input = AddDocumentationInput(input_code=code)
        result = crew.kickoff(inputs=task_input.model_dump())

        # Get the documented code
        documented_code = result.raw

        # Update the state
        self.state.documented_code = documented_code

        return documented_code

    @listen(add_documentation)
    def review_documentation(self, documented_code):
        """Review the documentation to determine if it's sufficient.

        Args:
            documented_code: The code with added documentation

        Returns:
            The review result and the documented code as a tuple
        """
        print("\n========== REVIEWING DOCUMENTATION ==========\n")

        # Create a crew with just the review_documentation task
        crew = Crew(
            agents=[self.code_processing_crew.code_documentation_reviewer()],
            tasks=[self.code_processing_crew.review_documentation_task()],
            process=Process.sequential,
            verbose=True
        )

        # Execute the crew with a structured input using Pydantic model
        task_input = ReviewDocumentationInput(documented_code=documented_code)
        result = crew.kickoff(inputs=task_input.model_dump())

        # Get the review result
        review_text = result.raw.strip()

        # Normalize the result to ensure it's exactly 'True' or 'False'
        if "true" in review_text.lower() and not "false" in review_text.lower():
            review_result = "True"
        else:
            review_result = "False"

        # Update the state
        self.state.review_result = review_result

        print(f"\n========== REVIEW RESULT: Documentation sufficient? {review_result} ==========\n")

        # Return both the review result and the documented code
        return {"review_result": review_result, "documented_code": documented_code}

    @router(review_documentation)
    def route_based_on_review(self, review_data):
        """Route the flow based on the review result.

        Args:
            review_data: Dictionary containing the review result and documented code

        Returns:
            The route to take: 'needs_improvement' or 'documentation_sufficient'
        """
        review_result = review_data["review_result"]

        if review_result == "True":
            return "documentation_sufficient"
        else:
            return "needs_improvement"

    @listen("needs_improvement")
    def improve_documentation(self):
        """Improve the documentation based on the review.

        Returns:
            The improved documented code
        """
        print("\n========== IMPROVING DOCUMENTATION BASED ON REVIEW ==========\n")

        # Create a crew with just the improve_documentation task
        crew = Crew(
            agents=[self.code_processing_crew.code_documentation_specialist()],
            tasks=[self.code_processing_crew.improve_documentation_task()],
            process=Process.sequential,
            verbose=True
        )

        # Execute the crew with a structured input using Pydantic model
        task_input = ImproveDocumentationInput(documented_code=self.state.documented_code)
        result = crew.kickoff(inputs=task_input.model_dump())

        # Get the improved code
        improved_code = result.raw

        # Update the state
        self.state.documented_code = improved_code

        # Go back to review the documentation
        return self.review_documentation(improved_code)

    @listen("documentation_sufficient")
    def generate_tests(self):
        """Generate test cases for the documented code.

        Returns:
            The generated test code
        """
        print("\n========== GENERATING TEST CASES ==========\n")

        # Create a crew with just the generate_tests task
        crew = Crew(
            agents=[self.code_processing_crew.test_automation_specialist()],
            tasks=[self.code_processing_crew.generate_tests_task()],
            process=Process.sequential,
            verbose=True
        )

        # Execute the crew with a structured input using Pydantic model
        task_input = GenerateTestsInput(documented_code=self.state.documented_code)
        result = crew.kickoff(inputs=task_input.model_dump())

        # Get the test code
        test_code = result.raw

        # Update the state
        self.state.test_code = test_code

        print("\n========== CODE PROCESSING COMPLETE ==========\n")

        return test_code


def plot_flow():
    """Generate a visualization of the flow."""
    flow = CodeProcessingFlow(None)  # Passing None as we don't need a real LLM for visualization
    flow.plot("code_processing_flow")
    print("Flow visualization saved to code_processing_flow.html")
