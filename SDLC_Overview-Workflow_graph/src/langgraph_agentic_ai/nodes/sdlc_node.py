from src.langgraph_agentic_ai.state.state import State
from typing_extensions import Literal
from pydantic import BaseModel, Field

# Define structured feedback model

class ProductOwnerFeedback(BaseModel):
    review: Literal["correct", "not correct"] = Field(description="Decide if the user story is correct as per requirement or not.")
    feedback: str = Field(description="If the user story is not as per requirement, provide feedback.")
    
class DesignDocFeedback(BaseModel):
    review: Literal["correct", "not correct"] = Field(description="Decide if the design document is correct as per requirement or not.")
    feedback: str = Field(description="If the design document is not as per requirement, provide feedback.")  

class CodeFeedback(BaseModel):
    review: Literal["correct", "not correct"] = Field(description="Decide if the code is correct as per requirement or not.")
    feedback: str = Field(description="If the code is not as per requirement, provide feedback.")
    
class SecurityFeedback(BaseModel):
    review: Literal["secure", "not secure"] = Field(description="Decide if the code is correct as per security vulnerabilities.")
    feedback: str = Field(description="If the code is not secure, provide feedback.")
    
class TestCaseFeedback(BaseModel):
    review: Literal["correct", "not correct"] = Field(description="Decide if the test cases are correct as per requirement or not.")
    feedback: str = Field(description="If the test cases are not correct, provide feedback.")

class QAFeedback(BaseModel):
    review: Literal["approved", "not approved"] = Field(description="Decide if the code is approved after QA testing.")
    feedback: str = Field(description="If the code is not approved after qa testing, provide feedback.")
    

class SDLCNode:
    """
    SDLC logic implementation.
    """
    def __init__(self,model):
        self.llm = model
        # Product owner review node
        self.product_owner_reviewer = self.llm.with_structured_output(ProductOwnerFeedback)

        # Design doc review node
        self.design_doc_review = self.llm.with_structured_output(DesignDocFeedback)

        # Code review node
        self.code_review = self.llm.with_structured_output(CodeFeedback)

        # Security review node
        self.security_review = self.llm.with_structured_output(SecurityFeedback)

        # Test case review node
        self.test_case_review = self.llm.with_structured_output(TestCaseFeedback)

        # QA review node
        self.qa_review = self.llm.with_structured_output(QAFeedback)

    
    def user_requirement(self, state: State):
        return {"requirement": state["requirement"]}
    

    def auto_generate_user_stories(self, state:State):
        if state.get("product_owner_feedback"):
            msg = self.llm.invoke(f"Write a formal user story based on the given requirement: {state['requirement']} but take into account the feedback: {state['product_owner_feedback']} in not more than 200 words")
        else:
            msg = self.llm.invoke(f"Write a formal user story based on the given requirement: {state['requirement']} in not more than 200 words")
        return {"user_story": msg.content}


    def product_owner_review(self, state: State):
        """"""
        feedback = self.product_owner_reviewer.invoke(f"Review the generated user story {state['user_story']} for the requirement {state['requirement']}")
        return {"product_review": feedback.review, "product_feedback": feedback.feedback}

    def revise_user_story(self, state: State):
        """"""
        if state["product_review"] == "not correct":
            msg = self.llm.invoke(f"Revise the user story {state['user_story']} based on the feedback: {state['product_feedback']}")
        return {"user_story": msg.content}

    def generate_design_doc(self, state: State):
        """"""
        if state.get("design_doc_feedback"):
            msg = self.llm.invoke(f"Generate a design document, functional and technical, based on the user story: {state['user_story']}  but take into account the feedback: {state['design_doc_feedback']} in not more than 200 words")
            return {"design_doc": msg.content}
        msg = self.llm.invoke(f"Generate a design document, functional and technical, based on the user story: {state['user_story']} in not more than 200 words")
        return {"design_doc": msg.content}

    # Routing logic
    def product_route(self, state: State):
        """Determines whether to send the code back to the coder or forward it to the manager."""
        return "revise_user_story" if state["product_review"] == "not correct" else "generate_design_doc"


    def design_doc_reviewer(self, state: State):
        """"""
        feedback = self.design_doc_review.invoke(f"Review the design document {state['design_doc']} for the user story {state['user_story']}")
        return {"design_doc_review": feedback.review, "design_doc_feedback": feedback.feedback}


    def generate_code(self, state: State):
        """Generates code based on the requirement, handling different types of requests."""

        if state.get("code"):
            # If code is already provided, refactor it and add a docstring
            refactored_code = self.llm.invoke(
            f"Refactor the following code to follow PEP8 standards, improve readability, and optimize performance: {state['code']}"
        )
            docstring = self.llm.invoke(
            f"Generate a well-structured docstring for the refactored code in markdown format, ensuring clarity and completeness: {refactored_code.content}"
        )
            return {"refactored_code": refactored_code.content, "docstring": docstring.content}

        # Handling different types of requirements
        requirement = state["requirement"].lower()

        if "python" in requirement:
            msg = self.llm.invoke(
                f"Write a well-structured and modular Python script based on the requirement: {state['requirement']} "
                f"and the design document: {state['design_doc']}. Follow best coding practices, keep the code extensible, and ensure it is easy to integrate."
                #f"If full deployment-ready code is not feasible, provide a detailed blueprint or template that can be extended."
            )
        elif "website" in requirement or "web app" in requirement:
            msg = self.llm.invoke(
                f"Generate a HTML, CSS (or Flask/Django if backend is needed) template for the website/web app "
                f"based on the requirement: {state['requirement']} and the design document: {state['design_doc']}. "
                f"If full deployment-ready code is not feasible, provide a structured blueprint or starting point."
            )
        else:
            msg = self.llm.invoke(
                f"Write the necessary code or technical solution based on the requirement: {state['requirement']} "
                f"and the design document: {state['design_doc']}. Ensure clarity and correctness."
                f"If full implementation isn't feasible, provide a structured blueprint or starting point."
            )

        # Generate a docstring for the outputted code
        docstring = self.llm.invoke(
            f"Generate a markdown-formatted docstring explaining the provided code or blueprint: {msg.content}"
        )   

        return {"code": msg.content, "docstring": docstring.content}


    def design_doc_route(self, state: State):
        """Determines whether to send the code back to the coder or forward it to the manager."""
        return "generate_design_doc" if state["design_doc_review"] == "not correct" else "generate_code"


    def code_reviewer(self, state: State):
        """Reviews the generated code based on the requirement and design document."""

        # Identify the type of requirement
        requirement = state["requirement"].lower()

        if "python" in requirement:
            prompt = (f"Review the Python code: {state['code']} "
                    f"for correctness, maintainability, and adherence to PEP8 based on the requirement {state['requirement']} "
                    f"and the design document {state['design_doc']}.")
        elif "website" in requirement or "web app" in requirement:
            prompt = (f"Review the web development code (HTML, CSS, JavaScript, backend if applicable): {state['code']} "
                    f"based on the requirement {state['requirement']} "
                    f"and the design document {state['design_doc']}.")
        else:
            prompt = (f"Review the code {state['code']} "
                    f"for correctness based on the requirement {state['requirement']} and design document {state['design_doc']}.")

        feedback = self.code_review.invoke(prompt)
        return {"code_review": feedback.review, "code_feedback": feedback.feedback}


    def fix_code_after_code_review(self, state: State):
        """Fixes the code based on review feedback. If a complete fix isn't possible, provides a structured template or blueprint."""

        if state.get("code_feedback"):
            msg = self.llm.invoke(
                f"Fix the code {state['code']} based on the feedback: {state['code_feedback']}."
                f"If a full fix isn't possible, provide a structured blueprint that can be further developed."
            )
            return {"code": msg.content}


    def security_reviewer(self, state: State):
        """"""
        feedback = self.security_review.invoke(f"Review the code {state['code']} for security vulnerabilities")
        return {"security_review": feedback.review, "security_feedback": feedback.feedback}


    def generate_test_cases(self, state: State):
        """Generates test cases based on the type of code and feedback received."""

        requirement = state["requirement"].lower()

        if "python" in requirement:
            prompt = (f"Write unit tests for the Python code {state['code']}, ensuring comprehensive coverage. "
                    f"Use pytest or unittest framework based on best practices.")
        elif "website" in requirement or "web app" in requirement:
            prompt = (f"Write front-end and back-end test cases for the website/web app code {state['code']}. "
                    f"Use Jest for front-end and pytest for back-end if applicable.")
        else:
            prompt = f"Write test cases for the code {state['code']}."

        if state.get("test_cases_feedback"):
            prompt += f" Take into account the feedback: {state['test_cases_feedback']}."

        msg = self.llm.invoke(prompt)
        return {"test_cases": msg.content}


    def code_route(self, state: State):
        """Determines whether to send the code back to the coder or forward it to the manager."""    
        return "fix_code_after_code_review" if state["code_review"] == "not correct" else "security_reviewer"


    def fix_code_after_security_review(self, state: State):
        """"""
        if state.get("security_feedback"):
            msg = self.llm.invoke(f"Fix the code {state['code']} based on the feedback: {state['security_feedback']}")
            return {"code": msg.content}


    def security_route(self, state: State):
        """Determines whether to send the code back to the coder or forward it to the manager."""
        return "generate_test_cases" if state["security_review"] == "secure"  else "fix_code_after_security_review"


    def test_cases_reviewer(self, state: State):
        """"""
        feedback = self.test_case_review.invoke(f"Review the test cases {state['test_cases']} for the code {state['code']}")
        return {"test_cases_review": feedback.review, "test_cases_feedback": feedback.feedback}

    def fix_test_cases_after_review(self, state: State):
        """"""
        if state.get("test_cases_feedback"):
            msg = self.llm.invoke(f"Fix the test cases {state['test_cases']} based on the feedback: {state['test_cases_feedback']}")
            return {"test_cases": msg.content}


    def qa_testing(self, state: State):
        """Performs QA testing based on the type of application being tested."""

        requirement = state["requirement"].lower()

        if "python" in requirement:
            prompt = (f"Perform functional and integration testing on the Python code {state['code']} "
                    f"using the test cases {state['test_cases']}. Identify issues related to logic, performance, and scalability.")
        elif "website" in requirement or "web app" in requirement:
            prompt = (f"Test the website/web app {state['code']} using the test cases {state['test_cases']}. "
                    f"Check for UI responsiveness, accessibility, security vulnerabilities, and performance issues.")
        else:
            prompt = f"Test the code {state['code']} using the test cases {state['test_cases']}."

        feedback = self.qa_review.invoke(prompt)
        return {"qa_review": feedback.review, "qa_feedback": feedback.feedback}


    def qa_test_route(self, state: State):
        """Determines whether to send the code back to the coder or forward it to the manager."""
        return "fix_code_after_qa_testing" if state["qa_review"] == "not approved" else "end"


    def fix_code_after_qa_testing(self, state: State):
        """"""
        if state.get("qa_feedback"):
            msg = self.llm.invoke(f"Fix the code {state['code']} based on the feedback: {state['qa_feedback']}")
            return {"code": msg.content}


    def test_cases_route(self, state: State):
        """Determines whether to send the code back to the coder or forward it to the manager."""
        return "fix_test_cases_after_review" if state["test_cases_review"] == "not correct" else "qa_testing"