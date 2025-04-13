from typing_extensions import TypedDict
    
# Define the state
class State(TypedDict):
    requirement: str
    user_story: str
    product_review: str
    product_feedback: str
    design_doc: str
    design_doc_review: str
    design_doc_feedback: str
    code: str
    code_review: str
    code_feedback: str
    security_review: str
    security_feedback: str
    test_cases: str
    test_cases_review: str
    test_cases_feedback: str
    qa_review: str
    qa_feedback: str
    decision: str
    refactored_code: str
    docstring: str