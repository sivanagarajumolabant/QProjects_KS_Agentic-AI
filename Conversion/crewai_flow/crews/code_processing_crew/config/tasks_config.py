"""Task configurations for code processing crew."""

# Task configurations as Python dictionaries instead of YAML

ADD_DOCUMENTATION_TASK = {
    "description": """Add proper docstrings to the provided Python code following PEP 257 standards.
    Include function/method purpose, parameters, return values, and any exceptions raised.
    Make sure the documentation is clear, concise, and helpful for other developers.
    Return the complete documented code.

    CODE:
    {input_code}""",
    "expected_output": "The complete code with proper documentation added.",
    "agent": "code_documentation_specialist",
    "output_schema": """{"type": "string", "description": "The complete code with proper documentation added."}"""
}

REVIEW_DOCUMENTATION_TASK = {
    "description": """Review the provided code and determine if it has proper documentation.
    Check if all functions, methods, and classes have appropriate docstrings.
    Verify that parameters, return values, and exceptions are documented.
    Return ONLY 'True' if the documentation is sufficient, or 'False' if it needs improvement.

    CODE:
    {documented_code}""",
    "expected_output": "A boolean value indicating whether the documentation is sufficient.",
    "agent": "code_documentation_reviewer",
    "output_schema": """{"type": "string", "enum": ["True", "False"], "description": "A boolean value indicating whether the documentation is sufficient."}"""
}

IMPROVE_DOCUMENTATION_TASK = {
    "description": """The documentation in this code needs improvement.
    Please enhance the docstrings to make them more complete and helpful.
    Make sure all functions, methods, and classes have appropriate docstrings.
    Ensure that parameters, return values, and exceptions are documented.
    Return the complete improved code.

    CODE:
    {documented_code}""",
    "expected_output": "The complete code with improved documentation.",
    "agent": "code_documentation_specialist",
    "output_schema": """{"type": "string", "description": "The complete code with improved documentation."}"""
}

GENERATE_TESTS_TASK = {
    "description": """Create comprehensive pytest test cases for the provided code.
    Include tests for normal operation, edge cases, and error conditions.
    Make sure the tests verify all functionality in the code.
    Return the complete test code.

    CODE:
    {documented_code}""",
    "expected_output": "Complete test code for the provided implementation.",
    "agent": "test_automation_specialist",
    "output_schema": """{"type": "string", "description": "Complete test code for the provided implementation."}"""
}

# Dictionary mapping task names to their configurations
TASKS_CONFIG = {
    "add_documentation_task": ADD_DOCUMENTATION_TASK,
    "review_documentation_task": REVIEW_DOCUMENTATION_TASK,
    "improve_documentation_task": IMPROVE_DOCUMENTATION_TASK,
    "generate_tests_task": GENERATE_TESTS_TASK
}
