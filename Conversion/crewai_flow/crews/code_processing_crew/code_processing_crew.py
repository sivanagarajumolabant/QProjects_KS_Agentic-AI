"""Code Processing Crew implementation using CrewAI."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crews.code_processing_crew.config.agents_config import AGENTS_CONFIG
from crews.code_processing_crew.config.tasks_config import TASKS_CONFIG


class AddDocumentationInput(BaseModel):
    """Input for the add_documentation task."""
    input_code: str = Field(
        description="Original input code to be processed"
    )


class ReviewDocumentationInput(BaseModel):
    """Input for the review_documentation task."""
    documented_code: str = Field(
        description="Code with documentation to be reviewed"
    )


class ImproveDocumentationInput(BaseModel):
    """Input for the improve_documentation task."""
    documented_code: str = Field(
        description="Code with documentation to be improved"
    )


class GenerateTestsInput(BaseModel):
    """Input for the generate_tests task."""
    documented_code: str = Field(
        description="Code with documentation for which to generate tests"
    )


class CodeProcessingResult(BaseModel):
    """Result of code processing workflow.

    This model represents the result of the code processing workflow,
    including the input code, documented code, review result, and test code.
    """
    input_code: str = Field(
        description="Original input code to be processed"
    )
    documented_code: str = Field(
        description="Code after documentation has been added"
    )
    review_result: str = Field(
        description="Review result indicating if documentation is sufficient ('True' or 'False')"
    )
    test_code: Optional[str] = Field(
        default=None,
        description="Generated test code for the documented code"
    )


@CrewBase
class CodeProcessingCrew:
    """Code processing crew for adding documentation and generating tests.

    This crew consists of three specialized agents:
    1. Code Documentation Specialist - Adds documentation to code
    2. Code Documentation Reviewer - Reviews documentation quality
    3. Test Automation Specialist - Generates test cases

    The crew follows a process where code is first documented, then reviewed,
    and if the documentation is insufficient, it's improved before generating tests.
    """

    def __init__(self, llm=None):
        """Initialize the code processing crew.

        Args:
            llm: The LLM to use for all agents (optional)
        """
        self.llm = llm
        self.agents_config = AGENTS_CONFIG
        self.tasks_config = TASKS_CONFIG

    @agent
    def code_documentation_specialist(self) -> Agent:
        """Create the code documentation specialist agent.

        Returns:
            Agent: The code documentation specialist agent
        """
        agent_config = self.agents_config['code_documentation_specialist']
        if self.llm:
            agent_config['llm'] = self.llm

        return Agent(
            config=agent_config,
            verbose=True
        )

    @agent
    def code_documentation_reviewer(self) -> Agent:
        """Create the code documentation reviewer agent.

        Returns:
            Agent: The code documentation reviewer agent
        """
        agent_config = self.agents_config['code_documentation_reviewer']
        if self.llm:
            agent_config['llm'] = self.llm

        return Agent(
            config=agent_config,
            verbose=True
        )

    @agent
    def test_automation_specialist(self) -> Agent:
        """Create the test automation specialist agent.

        Returns:
            Agent: The test automation specialist agent
        """
        agent_config = self.agents_config['test_automation_specialist']
        if self.llm:
            agent_config['llm'] = self.llm

        return Agent(
            config=agent_config,
            verbose=True
        )

    @task
    def add_documentation_task(self) -> Task:
        """Create the task for adding documentation to code.

        Returns:
            Task: The add documentation task
        """
        return Task(
            config=self.tasks_config['add_documentation_task']
        )

    @task
    def review_documentation_task(self) -> Task:
        """Create the task for reviewing documentation quality.

        Returns:
            Task: The review documentation task
        """
        return Task(
            config=self.tasks_config['review_documentation_task'],
            context=[self.add_documentation_task()]
        )

    @task
    def improve_documentation_task(self) -> Task:
        """Create the task for improving documentation based on review.

        Returns:
            Task: The improve documentation task
        """
        return Task(
            config=self.tasks_config['improve_documentation_task'],
            context=[self.review_documentation_task()]
        )

    @task
    def generate_tests_task(self) -> Task:
        """Create the task for generating test cases.

        Returns:
            Task: The generate tests task
        """
        return Task(
            config=self.tasks_config['generate_tests_task'],
            context=[self.review_documentation_task()]
        )

    @crew
    def crew(self) -> Crew:
        """Create the code processing crew.

        Returns:
            Crew: The code processing crew
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

    def process_code(self, input_code: str) -> Dict[str, Any]:
        """Process code through the complete crew workflow.

        This method orchestrates the code processing workflow:
        1. Add documentation to the code
        2. Review the documentation
        3. If the documentation is insufficient, improve it
        4. Generate test cases for the documented code

        Args:
            input_code: The input code to process

        Returns:
            Dict[str, Any]: A dictionary containing the processed code at each stage
        """
        print("\n========== STARTING CODE PROCESSING CREW ==========\n")
        print(f"Processing input code:\n{input_code}\n")

        # Step 1: Add documentation
        print("\n========== STEP 1: Adding documentation to code ==========\n")
        add_doc_crew = Crew(
            agents=[self.code_documentation_specialist()],
            tasks=[self.add_documentation_task()],
            process=Process.sequential,
            verbose=True
        )
        add_doc_input = AddDocumentationInput(input_code=input_code)
        add_doc_result = add_doc_crew.kickoff(
            inputs=add_doc_input.model_dump()
        )
        documented_code = add_doc_result.raw

        # Step 2: Review documentation
        print("\n========== STEP 2: Reviewing documentation ==========\n")
        review_crew = Crew(
            agents=[self.code_documentation_reviewer()],
            tasks=[self.review_documentation_task()],
            process=Process.sequential,
            verbose=True
        )
        review_input = ReviewDocumentationInput(documented_code=documented_code)
        review_result = review_crew.kickoff(
            inputs=review_input.model_dump()
        )

        # Normalize the review result
        review_text = review_result.raw.strip()
        is_documentation_sufficient = "true" in review_text.lower() and not "false" in review_text.lower()

        print(f"\n========== REVIEW RESULT: Documentation sufficient? {is_documentation_sufficient} ==========\n")

        # Step 3: Improve documentation if needed
        if not is_documentation_sufficient:
            print("\n========== STEP 3: Improving documentation based on review ==========\n")
            improve_crew = Crew(
                agents=[self.code_documentation_specialist()],
                tasks=[self.improve_documentation_task()],
                process=Process.sequential,
                verbose=True
            )
            improve_input = ImproveDocumentationInput(documented_code=documented_code)
            improve_result = improve_crew.kickoff(
                inputs=improve_input.model_dump()
            )
            documented_code = improve_result.raw

            # Review again
            print("\n========== REVIEWING IMPROVED DOCUMENTATION ==========\n")
            review_crew = Crew(
                agents=[self.code_documentation_reviewer()],
                tasks=[self.review_documentation_task()],
                process=Process.sequential,
                verbose=True
            )
            review_input = ReviewDocumentationInput(documented_code=documented_code)
            review_result = review_crew.kickoff(
                inputs=review_input.model_dump()
            )

            # Normalize the review result
            review_text = review_result.raw.strip()
            is_documentation_sufficient = "true" in review_text.lower() and not "false" in review_text.lower()

            print(f"\n========== REVIEW RESULT: Documentation sufficient? {is_documentation_sufficient} ==========\n")

        # Step 4: Generate tests
        print("\n========== STEP 4: Generating test cases ==========\n")
        test_crew = Crew(
            agents=[self.test_automation_specialist()],
            tasks=[self.generate_tests_task()],
            process=Process.sequential,
            verbose=True
        )
        test_input = GenerateTestsInput(documented_code=documented_code)
        test_result = test_crew.kickoff(
            inputs=test_input.model_dump()
        )
        test_code = test_result.raw

        print("\n========== CODE PROCESSING COMPLETE ==========\n")

        # Return the results as a Pydantic model
        return CodeProcessingResult(
            input_code=input_code,
            documented_code=documented_code,
            review_result="True" if is_documentation_sufficient else "False",
            test_code=test_code
        )
