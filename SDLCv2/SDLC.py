# --- START OF REVISED SDLC.py ---

# ==============================================================================
# SDLC.py
# Core logic for the AI-driven Software Development Life Cycle workflow.
# Uses Langchain with structured output for generating project artifacts.
# ==============================================================================

# --- Standard Library Imports ---
import datetime
import os
import sys
import shutil
import logging
import ast
import time
import random # Used for potential unique key generation if needed elsewhere
from typing import List, Union, Dict, Annotated, Any, Tuple, Optional
from functools import wraps
import json # For potentially parsing manually if needed, and formatting examples
from pathlib import Path

# --- Third-party Imports ---
from dotenv import load_dotenv
# Pydantic v2 is assumed here based on modern Langchain usage
from pydantic import BaseModel, Field, ValidationError as PydanticValidationError, field_validator # Use field_validator in Pydantic v2
from pydantic_core import ValidationError as CoreValidationError # For specific error checking if needed
from typing_extensions import TypedDict
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import nest_asyncio

# LangChain and related imports
from langchain.schema import AIMessage, HumanMessage
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

# External service clients
from tavily import TavilyClient
from plantuml import PlantUML

from markdown_it import MarkdownIt # ADDED
from weasyprint import HTML        # ADDED

# ==============================================================================
# --- Basic logging setup ---
# ==============================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==============================================================================
# --- Load Environment Variables & Apply Patches ---
# ==============================================================================
load_dotenv()
logger.info(".env file loaded if present.")

nest_asyncio.apply()
logger.info("nest_asyncio patch applied.")

# ==============================================================================
# --- Pydantic Models for Structured Data ---
# Define data structures for consistent input/output with LLMs and state management.
# These models are crucial for Langchain's `with_structured_output`.
# ==============================================================================

# --- UML Diagram Related Models ---
class DiagramSelection(BaseModel):
    """Structure for storing selected UML/DFD diagram types and justifications."""
    diagram_types: List[str] = Field(..., min_length=5, max_length=5, description="List of exactly 5 selected UML/DFD diagram types (strings)")
    justifications: List[str] = Field(..., min_length=5, max_length=5, description="List of exactly 5 brief justifications, corresponding to each selected diagram type")

    # Pydantic v2 validator syntax
    @field_validator('diagram_types', 'justifications')
    @classmethod
    def check_list_length(cls, v: List[str]) -> List[str]:
        if len(v) != 5:
            raise ValueError("List must contain exactly 5 items.")
        return v

class PlantUMLCode(BaseModel):
    """Structure for storing generated PlantUML code for a specific diagram."""
    diagram_type: str = Field(..., description="Type of UML/DFD diagram (e.g., Class Diagram, Sequence Diagram)")
    code: str = Field(..., description="PlantUML code string for the diagram (must start with @startuml and end with @enduml)")

    # Pydantic v2 validator syntax - Field validation needs context if accessing other fields
    # @field_validator('code')
    # @classmethod
    # def validate_plantuml_markers(cls, v: str, info: FieldValidationInfo) -> str:
    # Using a model validator provides access to all fields easily
    @classmethod
    def root_validator(cls, values):
        diagram_type = values.get('diagram_type', 'Unknown Diagram')
        code = values.get('code')
        if code:
            code_stripped = code.strip()
            if not code_stripped.startswith("@startuml"):
                raise ValueError(f"PlantUML code for {diagram_type} must start with @startuml.")
            if not code_stripped.endswith("@enduml"):
                raise ValueError(f"PlantUML code for {diagram_type} must end with @enduml.")
        else:
            raise ValueError("PlantUML code cannot be empty.")
        return values

# --- Code Generation Related Models ---
class CodeFile(BaseModel):
    """
    Structure representing a single file within the generated codebase.
    The filename includes the relative path from the project root.
    """
    filename: str = Field(..., description="Name of the file, including relative path from project root (e.g., 'src/main.py', 'README.md'). Must use forward slashes '/' as path separators.")
    content: str = Field(..., description="Full text content of the file. Should not be empty for actual code files.")

    @field_validator('filename')
    @classmethod
    def validate_filename_format(cls, v: str) -> str:
        if not v:
            raise ValueError("Filename cannot be empty.")
        if '\\' in v:
            raise ValueError("Filename must use forward slashes '/' for path separators, not backslashes '\\'.")
        if v.startswith('/'):
             raise ValueError("Filename should be a relative path, not starting with '/'.")
        # Add more checks if needed, e.g., for disallowed characters
        return v

class GeneratedCode(BaseModel):
    """
    Structure representing the complete generated codebase including files and instructions.
    Used for initial code generation and refinement steps. THIS IS THE TARGET SCHEMA FOR LLM.
    """
    files: List[CodeFile] = Field(..., description="List of all code files (CodeFile objects) in the project. Should include all necessary files (source, config, README, dependencies like requirements.txt). Must not be empty unless intentionally trivial.")
    instructions: str = Field(..., min_length=10, description="Clear, beginner-friendly setup and run instructions as a single string (at least 10 characters). Must cover environment setup, dependency installation, and execution steps. Must not be empty.")

    @field_validator('files')
    @classmethod
    def check_files_not_empty(cls, v: List[CodeFile]) -> List[CodeFile]:
        if not v:
             logger.warning("GeneratedCode 'files' list is empty. This might be intended for trivial projects, but is usually an issue.")
            # Consider raising ValueError("The 'files' list cannot be empty...") if it's always required
        return v

# --- Testing Related Models ---
class TestCase(BaseModel):
    """Structure representing a single test case with description, input, and expected output."""
    description: str = Field(..., min_length=5, description="Clear description of the test case scenario (at least 5 characters)")
    input_data: Dict[str, Any] = Field(..., description="Dictionary representing *concrete* fake input data required for the test. Must be non-empty.")
    expected_output: Dict[str, Any] = Field(..., description="Dictionary representing the *concrete* expected fake output or system state after the test. Must be non-empty.")

    # --- NEW VALIDATOR ---
    # Add validator to attempt parsing stringified JSON before standard validation
    @field_validator('input_data', 'expected_output', mode='before')
    @classmethod
    def parse_stringified_json(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                # Attempt to parse the string as JSON
                parsed_dict = json.loads(v)
                if not isinstance(parsed_dict, dict):
                     # If parsing results in something other than a dict (e.g., list, number)
                     raise ValueError(f"Parsed JSON string is not a dictionary, got {type(parsed_dict)}")
                logger.debug(f"Successfully parsed stringified JSON for dict field: {v[:50]}...")
                return parsed_dict
            except json.JSONDecodeError as e:
                # If the string is not valid JSON, raise an error
                raise ValueError(f"Input string is not valid JSON: {e}. Original value: '{v[:100]}...'") from e
            except ValueError as ve: # Catch the specific error raised above
                 raise ve
        # If it's not a string (presumably already a dict or other type), pass it through
        return v
    # --- END NEW VALIDATOR ---


    @field_validator('input_data', 'expected_output')
    @classmethod
    def check_dict_not_empty(cls, v: Dict) -> Dict:
        # This validator now runs *after* parse_stringified_json (if it was a string)
        # Ensure it's actually a dict first (though parse_stringified_json should guarantee this if it returns)
        if not isinstance(v, dict):
             # This case should ideally be caught by the 'before' validator or Pydantic's core type check
             raise ValueError(f"Input is not a dictionary after pre-processing (got {type(v)}).")
        if not v:
            raise ValueError("Input/Expected data dictionaries cannot be empty.")
        return v

class TestCases(BaseModel):
    """Structure holding a list of test cases."""
    test_cases: List[TestCase] = Field(..., min_length=1, description="List of test cases (TestCase objects). Must contain at least one test case.")

# --- Combined Output Model (for specific refinement steps) ---
class RefinedTestAndCodeOutput(BaseModel):
    """Structure for the combined output of refined tests and code."""
    refined_test_cases: TestCases = Field(..., description="The refined list of test cases, adhering to the TestCases schema.")
    refined_code: GeneratedCode = Field(..., description="The refined code, including BOTH 'files' and 'instructions', adhering to the GeneratedCode schema.")

class QualityCodeAndInstructionsOutput(BaseModel):
    """Structure for the combined output of refined QA analysis and potentially polished code."""
    refined_analysis: str = Field(..., min_length=50, description="The refined Quality Analysis report text (Markdown format, at least 50 chars).")
    refined_code: GeneratedCode = Field(..., description="The potentially refined code (minor tweaks only), including 'files' and 'instructions', adhering to the GeneratedCode schema.")

# ==============================================================================
# --- Main Workflow State Definition ---
# TypedDict defining the structure of the shared state dictionary passed between functions.
# Comments added to group related state variables.
# ==============================================================================

class MainState(TypedDict, total=False):
    """
    Defines the structure for the main workflow state dictionary.
    `total=False` allows keys to be potentially missing, requiring checks before access.
    """
    # --- Core Instances & Configuration ---
    llm_instance: Optional[BaseLanguageModel]      # Initialized LLM client instance (mandatory for most steps)
    tavily_instance: Optional[TavilyClient]       # Initialized Tavily client instance (optional, for web search)
    project_folder: str         # Base directory name for saving project artifacts (mandatory)
    project: str                # Name or high-level description of the project (mandatory)
    category: str               # Project category (e.g., Web Development)
    subcategory: str            # Project subcategory (e.g., API, Tool)
    coding_language: str        # Primary programming language (e.g., Python, JavaScript) (mandatory)

    # --- Communication History ---
    # Accumulates HumanMessage and AIMessage objects throughout the workflow for context
    messages: Annotated[List[Union[HumanMessage, AIMessage]], lambda x, y: (x or []) + (y or [])]

    # --- Requirements Gathering Cycle State (Cycle 1) ---
    user_input_questions: List[str] # Questions generated by the LLM for the user
    user_input_answers: List[str]   # Answers provided by the user
    user_input_iteration: int     # Current Q&A iteration count
    user_input_min_iterations: int # Minimum required Q&A iterations
    user_input_done: bool           # Flag indicating if Q&A phase is complete
    user_query_with_qa: str         # Combined initial query and Q&A history (saved artifact)
    refined_prompt: str             # Synthesized prompt after Q&A (key input for next cycles)

    # --- User Story Cycle State (Cycle 2) ---
    user_story_current: str             # The current version of user stories being worked on
    user_story_feedback: str            # AI-generated feedback on the current stories
    user_story_human_feedback: str      # Human feedback provided on the stories/AI feedback
    user_story_done: bool               # Flag indicating user stories are finalized

    # --- Product Review Cycle State (Cycle 3) ---
    product_review_current: str         # Current version of the Product Owner review
    product_review_feedback: str        # AI feedback on the PO review
    product_review_human_feedback: str  # Human feedback on the PO review/AI feedback
    product_review_done: bool           # Flag indicating PO review is finalized

    # --- Design Document Cycle State (Cycle 4) ---
    design_doc_current: str             # Current version of the design document
    design_doc_feedback: str            # AI feedback on the design document
    design_doc_human_feedback: str      # Human feedback on the design doc/AI feedback
    design_doc_done: bool               # Flag indicating design document is finalized

    # --- UML Diagram Cycle State (Cycle 5) ---
    uml_selected_diagrams: List[str]            # List of selected diagram types (strings)
    uml_current_codes: List[PlantUMLCode]       # List of current PlantUMLCode objects
    uml_feedback: Dict[str, str]                # AI feedback keyed by diagram type
    uml_human_feedback: Dict[str, str]          # Human feedback (can include 'all' key)
    uml_done: bool                              # Flag indicating UML diagrams are finalized

    # --- Code Generation Cycle State (Cycle 6 - Initial Code & Refinement Loop) ---
    # Holds the latest GeneratedCode object (files + instructions) during the cycle
    code_current: Optional[GeneratedCode]       # Current code object being iterated on
    code_human_input: str               # User input/feedback during initial code testing/running
    code_web_search_results: str        # Results from Tavily web search based on user input
    code_feedback: str                  # AI feedback on the code (considering user input, search)
    code_human_feedback: str            # Human comments on the AI code feedback
    code_done: bool                     # Flag indicating initial code generation/refinement is done (triggers Review)

    # --- Review & Security Cycle State (Cycle 7 - Analysis & Refinement Loop) ---
    code_review_current_feedback: str   # Feedback from the AI code reviewer
    security_current_feedback: str      # Feedback from the AI security checker
    review_security_human_feedback: str # Human feedback on the review/security reports
    review_security_done: bool          # Flag indicating review/security cycle is finalized (triggers Testing)

    # --- Testing Cycle State (Cycle 8 - Test Gen, Execution Sim & Refinement Loop) ---
    test_cases_current: List[TestCase]  # Current list of TestCase objects
    test_cases_feedback: str            # AI feedback on the test cases
    test_cases_human_feedback: str      # Human feedback/results from running tests (crucial for refinement)
    test_cases_passed: bool             # Flag indicating if core tests passed successfully (triggers QA)

    # --- Quality Analysis Cycle State (Cycle 9 - Report & Polish Loop) ---
    quality_current_analysis: str       # Current version of the QA report
    quality_feedback: str               # AI feedback on the QA report
    quality_human_feedback: str         # Human feedback on the QA report/AI feedback
    quality_done: bool                  # Flag indicating QA cycle is finalized (triggers Deployment)

    # --- Deployment Cycle State (Cycle 10 - Plan & Refinement Loop) ---
    deployment_current_process: str     # Current version of the deployment plan/process
    deployment_feedback: str            # AI feedback on the deployment plan
    deployment_human_feedback: str      # Human feedback on the deployment plan/AI feedback
    deployment_done: bool               # Flag indicating deployment plan is finalized

    # =============================================
    # --- Final Artifact Storage (Populated by save_* functions) ---
    # These store the final, approved versions after each cycle is marked 'done'.
    # =============================================
    final_user_story: str               # Final user stories text
    final_product_review: str           # Final product review text
    final_design_document: str          # Final design document text
    final_uml_codes: List[PlantUMLCode] # Final list of PlantUMLCode objects
    final_code_files: List[CodeFile]    # Final code files (after *all* refinements: initial, review/sec, test, qa)
    final_code_review: str              # Final saved code review feedback text
    final_security_issues: str          # Final saved security analysis text
    final_test_code_files: List[CodeFile] # Code version that passed testing (snapshot)
    final_quality_analysis: str         # Final quality analysis report text
    final_deployment_process: str       # Final deployment plan text

    # =============================================
    # --- File Paths for Saved Artifacts (Populated by save_* functions) ---
    # These store the absolute paths to the saved files/folders for easy retrieval/download.
    # =============================================
    final_user_story_path: Optional[str]            # Path to final_user_stories.md
    final_product_review_path: Optional[str]        # Path to final_product_review.md
    final_design_document_path: Optional[str]       # Path to final_design_document.md
    final_uml_diagram_folder: Optional[str]         # Path to 5_uml_diagrams folder
    final_uml_png_paths: List[str]                  # List of paths to generated PNGs within the UML folder
    final_review_security_folder: Optional[str]     # Path to 6_review_security folder
    review_code_snapshot_folder: Optional[str]      # Path to code snapshot *after* review/sec fixes within 6_...
    final_testing_folder: Optional[str]             # Path to 7_testing folder
    testing_passed_code_folder: Optional[str]       # Path to code snapshot that *passed* testing within 7_...
    final_quality_analysis_path: Optional[str]      # Path to final_quality_analysis_report.md
    final_code_folder: Optional[str]                # Path to the *absolute final* code snapshot (after QA polish) within 8_...
    final_deployment_path: Optional[str]            # Path to final_deployment_plan.md
    refined_prompt_path: Optional[str] # ADDED for MD path

    # --- ADDED: PDF File Paths ---
    refined_prompt_pdf_path: Optional[str]
    final_user_story_pdf_path: Optional[str]
    final_product_review_pdf_path: Optional[str]
    final_design_document_pdf_path: Optional[str]
    final_quality_analysis_pdf_path: Optional[str] # Renamed QA path slightly
    final_deployment_pdf_path: Optional[str]     # Renamed Deploy path slightly

    # --- ADDED: Intermediate Code Snapshot Paths ---
    snapshot_path_codegen_initial: Optional[str]
    snapshot_path_codegen_refined: Optional[str] # Path to the LATEST refined snapshot in this cycle
    snapshot_path_review_refined: Optional[str]  # Path after refine_code_with_reviews
    snapshot_path_testing_refined: Optional[str] # Path to LATEST refinement after test fail
    snapshot_path_qa_polished: Optional[str]     # Path after refine_quality_and_code

    
# ==============================================================================
# --- Constants ---
# Shared constants used across the workflow.
# ==============================================================================

# Max length for text artifacts when used as context in prompts (to manage token limits)
MAX_CONTEXT_LEN: int = 15000
# Max length for code snippets when used as context in prompts
MAX_CODE_CONTEXT_LEN: int = 25000
# Minimum iterations for initial user Q&A
MIN_USER_INPUT_ITERATIONS: int = 1 # Adjusted, can be configured

# ==============================================================================
# --- Helper Functions ---
# Utility functions used across the workflow.
# ==============================================================================

# --- PlantUML Syntax Reference & Validation ---
PLANTUML_SYNTAX_RULES: Dict[str, Dict[str, Any]] = {
    # (Syntax rules dictionary remains unchanged - included for completeness)
    "Activity Diagram": {"template": "@startuml\nstart\nif (condition) then (yes)\n  :action1;\nelse (no)\n  :action2;\nendif\nwhile (condition)\n  :action3;\nendwhile\nstop\n@enduml", "required_keywords": ["start", ":", "stop"], "notes": "Conditionals: if/else/endif. Loops: while/endwhile. Actions: :action;."},
    "Sequence Diagram": {"template": "@startuml\nparticipant A\nparticipant B\nA -> B : message\nalt condition\n  B --> A : success\nelse\n  B --> A : failure\nend\n@enduml", "required_keywords": ["participant", "->", "-->"], "notes": "-> solid line, --> dashed line. alt/else/end for alternatives."},
    "Use Case Diagram": {"template": "@startuml\nactor User\nusecase (UC1)\nUser --> (UC1)\n@enduml", "required_keywords": ["actor", "-->", "("], "notes": "Define actors and use cases, connect with -->."},
    "Class Diagram": {"template": "@startuml\nclass MyClass {\n  +field: Type\n  +method()\n}\nMyClass --> OtherClass\n@enduml", "required_keywords": ["class", "{", "}", "-->"], "notes": "Define classes, attributes, methods. --> association, <|-- inheritance."},
    "State Machine Diagram": {"template": "@startuml\n[*] --> State1\nState1 --> State2 : event [condition] / action\nState2 --> [*]\n@enduml", "required_keywords": ["[*]", "-->", ":"], "notes": "[*] start/end. --> transitions with event/condition/action."},
    "Object Diagram": {"template": "@startuml\nobject obj1: Class1\nobj1 : attr = val\nobj1 --> obj2\n@enduml", "required_keywords": ["object", ":", "-->"], "notes": "Define objects (instances), set attributes, link."},
    "Component Diagram": {"template": "@startuml\ncomponent Comp1\ninterface Iface\nComp1 ..> Iface\nComp1 --> Comp2\n@enduml", "required_keywords": ["component", "-->"], "notes": "Define components, interfaces. --> dependency, ..> usage."},
    "Deployment Diagram": {"template": "@startuml\nnode Server {\n  artifact app.jar\n}\n@enduml", "required_keywords": ["node", "artifact"], "notes": "Nodes for hardware/software envs, artifacts for deployed items."},
    "Package Diagram": {"template": "@startuml\npackage \"My Package\" {\n  class ClassA\n}\n@enduml", "required_keywords": ["package", "{"], "notes": "Group elements."},
    "Composite Structure Diagram": {"template": "@startuml\nclass Composite {\n  +part1 : Part1\n}\nComposite *-- Part1\n@enduml", "required_keywords": ["class", "{", "}", "*--"], "notes": "Show internal structure, *-- composition."},
    "Timing Diagram": {"template": "@startuml\nrobust \"User\" as U\nconcise \"System\" as S\n@0\nU is Idle\nS is Ready\n@100\nU -> S : Request()\nS is Processing\n@300\nS --> U : Response()\nU is Active\nS is Ready\n@enduml", "required_keywords": ["@", "is"], "notes": "Show state changes over time."},
    "Interaction Overview Diagram": {"template": "@startuml\nstart\nif (condition?) then (yes)\n  ref over Actor : Interaction1\nelse (no)\n  :Action A;\nendif\nstop\n@enduml", "required_keywords": ["start", ":", "ref", "stop"], "notes": "Combine activity diagrams with interaction refs."},
    "Communication Diagram": {"template": "@startuml\nobject O1\nobject O2\nO1 -> O2 : message()\n@enduml", "required_keywords": ["object", "->", ":"], "notes": "Focus on object interactions."},
    "Profile Diagram": {"template": "@startuml\nprofile MyProfile {\n  stereotype MyStereotype\n}\n@enduml", "required_keywords": ["profile", "stereotype"], "notes": "Define custom stereotypes and tagged values."},
    "Context Diagram (Level 0 DFD)": {"template": "@startuml\nrectangle System as S\nentity External as E\nE --> S : Data Input\nS --> E : Data Output\n@enduml", "required_keywords": ["rectangle", "entity", "-->", ":"], "notes": "System boundary, external entities, major data flows."},
    "Level 1 DFD": {"template": "@startuml\nentity E\nrectangle P1\nrectangle P2\ndatabase DS\nE --> P1 : Input\nP1 --> P2 : Data\nP1 --> DS : Store\nP2 --> E : Output\n@enduml", "required_keywords": ["rectangle", "entity", "database", "-->", ":"], "notes": "Major processes, data stores, flows between them."},
    "General DFD": {"template": "@startuml\nentity E\nrectangle P\ndatabase DS\nE --> P : Input\nP --> DS : Store\nDS --> P : Retrieve\nP --> E : Output\n@enduml", "required_keywords": ["entity", "rectangle", "database", "-->", ":"], "notes": "Generic structure for DFDs."},
}

# Basic validation is now handled within the PlantUMLCode Pydantic model
# def validate_plantuml_code(diagram_type: str, code: str) -> bool: ... (removed)
# --- ADDED: PDF Conversion Helper ---
def convert_md_to_pdf(md_content: str, output_pdf_path: str) -> bool:
    """
    Converts Markdown content to a PDF file using markdown-it-py and WeasyPrint.

    Args:
        md_content: The Markdown text content.
        output_pdf_path: The full path where the PDF should be saved.

    Returns:
        True if conversion was successful, False otherwise.
    """
    try:
        logger.info(f"Attempting to convert Markdown to PDF: {output_pdf_path}")
        # 1. Convert Markdown to HTML
        md_parser = MarkdownIt()
        html_content = md_parser.render(md_content)

        # Basic CSS for better PDF formatting (optional, can be expanded)
        # Ensures code blocks wrap and provides some spacing.
        css_style = """
            @page { margin: 1in; }
            body { font-family: sans-serif; line-height: 1.4; }
            h1, h2, h3, h4, h5, h6 { margin-top: 1.2em; margin-bottom: 0.6em; line-height: 1.2; }
            h1 { font-size: 1.8em; }
            h2 { font-size: 1.5em; }
            h3 { font-size: 1.3em; }
            p { margin-bottom: 0.8em; }
            pre {
                white-space: pre-wrap; /* Allow wrapping */
                word-wrap: break-word; /* Break long words */
                background-color: #f0f0f0;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto; /* Add scrollbar if needed, though wrap should handle most */
            }
            code { font-family: monospace; }
            ul, ol { padding-left: 1.5em; margin-bottom: 0.8em; }
            li { margin-bottom: 0.2em; }
            blockquote { border-left: 3px solid #ccc; padding-left: 1em; margin-left: 0; font-style: italic; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 1em; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        """
        full_html = f"<html><head><style>{css_style}</style></head><body>{html_content}</body></html>"

        # 2. Convert HTML to PDF
        HTML(string=full_html).write_pdf(output_pdf_path)
        logger.info(f"Successfully generated PDF: {os.path.basename(output_pdf_path)}")
        return True
    except ImportError:
        logger.error("WeasyPrint or markdown-it-py not installed. Cannot generate PDF.")
        return False
    except Exception as e:
        logger.error(f"Failed to generate PDF '{os.path.basename(output_pdf_path)}': {e}", exc_info=True)
        # Clean up potentially incomplete PDF file
        if os.path.exists(output_pdf_path):
            try: os.remove(output_pdf_path)
            except Exception as rm_e: logger.warning(f"Could not remove partial PDF {output_pdf_path}: {rm_e}")
        return False
# --- END ADDED HELPER ---

# --- Code Context Generation ---
def get_code_context_string(code_files: List[CodeFile], max_len: int = MAX_CODE_CONTEXT_LEN, func_name: str = "unknown") -> str:
    """
    Creates a truncated string representation of code files for LLM context.
    Prioritizes key files and truncates intelligently.

    Args:
        code_files: A list of CodeFile objects (with filenames including paths).
        max_len: The maximum total length of the returned string.
        func_name: The name of the calling function (for logging).

    Returns:
        A single string containing concatenated (and potentially truncated) file contents.
    """
    if not code_files:
        return "No code files provided."

    code_str_parts = []
    total_len = 0
    # Keywords to identify potentially important configuration or entrypoint files
    key_file_hints = ["requirements", "dockerfile", "main.", "app.", ".env", "config", "setup.", "pom.xml", "build.gradle", "package.json", "readme", "makefile", "docker-compose", "settings", "urls", "wsgi", "asgi"]

    # Separate key files from others
    key_files = []
    other_files = []
    for f in code_files:
        # Use Path for robust basename extraction
        try:
            # Ensure filename is a string before processing
            if not isinstance(f.filename, str):
                logger.warning(f"Skipping file with non-string filename: {f.filename} in func {func_name}")
                continue
            filename_lower = Path(f.filename).name.lower()
            is_key = any(hint in filename_lower for hint in key_file_hints)
        except Exception as e: # Handle potential invalid filenames gracefully
            logger.warning(f"Could not process filename '{f.filename}' for key file check: {e}")
            is_key = False

        if is_key:
            key_files.append(f)
        else:
            other_files.append(f)

    processed_files_count = 0
    # Process key files first, then others
    files_to_process = sorted(key_files, key=lambda x: x.filename) + sorted(other_files, key=lambda x: x.filename)

    for file in files_to_process:
        # Check again in case non-string filenames slipped through
        if not isinstance(file.filename, str):
             logger.warning(f"Skipping file processing due to non-string filename: {file.filename}")
             continue

        header = f"\n--- File: {file.filename} ---\n"
        # Calculate remaining length available for this file's content
        # Account for header length and potential truncation markers
        remaining_len_for_content = max_len - total_len - len(header) - 50 # Extra buffer

        if remaining_len_for_content <= 10: # Not enough space even for a small snippet
            files_remaining = len(files_to_process) - processed_files_count
            if files_remaining > 0:
                 # Avoid adding this message multiple times
                 if not code_str_parts or not code_str_parts[-1].startswith("\n*... (Code context truncated"):
                      code_str_parts.append(f"\n*... (Code context truncated, {files_remaining} more file{'s' if files_remaining != 1 else ''} not shown)*")
            logger.debug(f"Code context fully truncated in {func_name} after {processed_files_count} files.")
            break

        file_content = file.content if file.content is not None else "" # Handle potential None content
        # Ensure content is string before getting length or slicing
        if not isinstance(file_content, str):
             logger.warning(f"File '{file.filename}' content is not a string ({type(file_content)}), treating as empty.")
             file_content = ""

        content_len = len(file_content)
        is_truncated = content_len > remaining_len_for_content

        # Take only the allowed portion of the content
        snippet = file_content[:remaining_len_for_content]

        file_repr = header + snippet
        if is_truncated:
            file_repr += '\n*... (File content truncated)*'

        code_str_parts.append(file_repr)
        total_len += len(file_repr)
        processed_files_count += 1

        # Check if we've hit the overall max length after adding this file
        if total_len >= max_len:
             files_remaining_after_current = len(files_to_process) - processed_files_count
             if files_remaining_after_current > 0:
                  # Avoid adding this message multiple times
                  if not code_str_parts or not code_str_parts[-1].startswith("\n*... (Code context max length reached"):
                       code_str_parts.append(f"\n*... (Code context max length reached, {files_remaining_after_current} more file{'s' if files_remaining_after_current != 1 else ''} not shown)*")
             logger.debug(f"Code context max length reached in {func_name} while processing file {file.filename}")
             break # Stop processing more files

    return "\n".join(code_str_parts)

# --- Safe File Saving Utility ---
def save_code_files(code_files: List[CodeFile], instructions: str, target_dir: str, instructions_filename: str = "instructions.md") -> bool:
    """
    Safely saves a list of CodeFile objects and instructions to a target directory.
    Creates subdirectories as needed based on filenames.

    Args:
        code_files: List of CodeFile objects to save.
        instructions: The instruction string to save.
        target_dir: The absolute path to the directory where files should be saved.
        instructions_filename: The name for the instructions file.

    Returns:
        True if all files and instructions were saved successfully, False otherwise.
    """
    if not os.path.isabs(target_dir):
        logger.error(f"Target directory for saving code must be absolute: {target_dir}")
        return False

    os.makedirs(target_dir, exist_ok=True) # Ensure target exists
    logger.info(f"Saving {len(code_files)} code file(s) and instructions to: {target_dir}")

    all_successful = True
    saved_count = 0

    # Save code files
    for code_file in code_files:
        # Validate types before proceeding
        if not isinstance(code_file, CodeFile):
            logger.warning(f"Skipping non-CodeFile object found in list: {type(code_file)}")
            all_successful = False
            continue
        if not isinstance(code_file.filename, str) or not isinstance(code_file.content, str):
            logger.warning(f"Skipping CodeFile with non-string filename/content: {code_file.filename} ({type(code_file.filename)}), {type(code_file.content)}")
            all_successful = False
            continue

        filename = code_file.filename
        content = code_file.content # Already validated as string

        # Basic path sanitization and validation
        relative_path = filename.lstrip('/\\').strip()
        if not relative_path:
            logger.warning(f"Skipping file with empty relative path.")
            all_successful = False
            continue
        # Prevent path traversal attempts
        if ".." in Path(relative_path).parts:
            logger.warning(f"Skipping potentially unsafe file path with '..': {filename}")
            all_successful = False
            continue

        # Use Path object for robust joining and normalization
        try:
             filepath_obj = Path(target_dir) / relative_path
             filepath = filepath_obj.resolve() # Get absolute path to check against target_dir root
        except Exception as path_err:
             logger.warning(f"Error resolving path for '{filename}' in '{target_dir}': {path_err}")
             all_successful = False
             continue

        # Final check: ensure the resolved path is still within the intended target directory
        target_dir_abs = Path(target_dir).resolve()
        if not str(filepath).startswith(str(target_dir_abs)):
            logger.warning(f"Attempted path traversal detected! Skipping file save: {filename} -> {filepath}")
            all_successful = False
            continue

        try:
            # Create subdirectories if they don't exist based on the file path
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.debug(f"Saved code file: {filepath.relative_to(target_dir_abs)}")
            saved_count += 1
        except OSError as path_err:
            logger.error(f"OS Error saving code file '{filepath}': {path_err}")
            all_successful = False
        except Exception as write_err:
            logger.error(f"Error writing code file '{filepath}': {write_err}")
            all_successful = False

    logger.info(f"Saved {saved_count} out of {len(code_files)} code files.")

    # Save instructions file
    try:
        # Validate instructions type
        if not isinstance(instructions, str):
            logger.error(f"Instructions must be a string, but got {type(instructions)}. Saving placeholder.")
            instructions = "[Error: Instructions were not a string]"
            all_successful = False

        instr_path = Path(target_dir) / instructions_filename
        with open(instr_path, "w", encoding="utf-8") as f:
            f.write(instructions)
        logger.debug(f"Saved instructions file: {instructions_filename}")
    except Exception as instr_err:
        logger.error(f"Error writing instructions file '{instr_path}': {instr_err}")
        all_successful = False

    return all_successful

# --- ADDED: Code Snapshot Saving Helper ---
def _save_code_snapshot(state: MainState, cycle_name: str, step_description: str) -> Optional[str]:
    """
    Saves the current code state (files + instructions) to a timestamped snapshot folder.

    Args:
        state: The current workflow state dictionary.
        cycle_name: Name of the current cycle (e.g., "code_generation").
        step_description: Description of the step (e.g., "initial", "refined", "post_review").

    Returns:
        The absolute path to the created snapshot folder, or None on failure.
    """
    func_name = f"_save_code_snapshot ({cycle_name}/{step_description})"
    logger.info(f"Executing {func_name}...")

    code_to_save: Optional[GeneratedCode] = state.get("code_current")
    project_folder = state.get("project_folder")

    if not project_folder:
        logger.error(f"Project folder path is missing in state for {func_name}.")
        return None
    if not code_to_save or not isinstance(code_to_save, GeneratedCode) or not code_to_save.files:
        logger.warning(f"No valid code/files found in 'code_current' state to save for {func_name}.")
        return None # Nothing to save

    # --- Create Snapshot Directory ---
    snapshot_folder: Optional[str] = None
    try:
        abs_project_folder = os.path.abspath(project_folder)
        # Use cycle number for better sorting if desired (extract from STAGE_TO_CYCLE or CYCLE_ORDER)
        # Simplified cycle naming for folder path:
        cycle_folder_name = cycle_name.lower().replace(" ", "_").replace("&", "and")
        snapshots_base_dir = os.path.join(abs_project_folder, f"{cycle_folder_name}_snapshots")
        os.makedirs(snapshots_base_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_step_desc = "".join(c for c in step_description if c.isalnum() or c == '_').lower()
        snapshot_folder_name = f"snapshot_{safe_step_desc}_{timestamp}"
        snapshot_folder = os.path.join(snapshots_base_dir, snapshot_folder_name)
        os.makedirs(snapshot_folder, exist_ok=True) # Create the specific snapshot folder

        logger.info(f"Saving snapshot to: {snapshot_folder}")

        # --- Save Code Files ---
        files_to_save = code_to_save.files
        instructions = code_to_save.instructions
        saved_count = 0
        for code_file in files_to_save:
            filename = code_file.filename
            content = code_file.content
            relative_path = filename.lstrip('/\\').strip()
            if ".." in relative_path or os.path.isabs(relative_path):
                logger.warning(f"Skipping potentially unsafe file path: {filename}"); continue
            filepath = os.path.normpath(os.path.join(snapshot_folder, relative_path))
            if not os.path.abspath(filepath).startswith(os.path.abspath(snapshot_folder)):
                logger.warning(f"Attempted path traversal! Skipping file: {filename} -> {filepath}"); continue
            try:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f: f.write(content)
                saved_count += 1
            except OSError as path_err: logger.error(f"OS Error saving snapshot file '{filepath}': {path_err}")
            except Exception as write_err: logger.error(f"Error writing snapshot file '{filepath}': {write_err}")
        logger.debug(f"Saved {saved_count} files to snapshot.")

        # --- Save Instructions ---
        try:
            instr_filename = "instructions.md"
            instr_path = os.path.join(snapshot_folder, instr_filename)
            with open(instr_path, "w", encoding="utf-8") as f: f.write(instructions)
            logger.debug(f"Saved instructions to snapshot: {instr_filename}")
        except Exception as instr_err:
            logger.error(f"Error writing instructions to snapshot: {instr_err}")

        return snapshot_folder # Return the path to the created snapshot folder

    except (ValueError, OSError, TypeError) as e:
        logger.error(f"Error during {func_name}: {e}", exc_info=True)
        return None # Return None on failure
# --- END ADDED HELPER ---


# ==============================================================================
# --- Initialization Function ---
# Sets up LLM and Tavily clients based on user configuration.
# (No changes needed in this function based on the request)
# ==============================================================================

def initialize_llm_clients(provider: str, model_name: str, llm_api_key: str, tavily_api_key: Optional[str]) -> Tuple[Optional[BaseLanguageModel], Optional[TavilyClient], Optional[str]]:
    """
    Initializes LangChain LLM and Tavily clients based on provided configuration.
    Performs a basic test call to the LLM provider.

    Args:
        provider: The name of the LLM provider (e.g., "OpenAI", "Groq", "Google", "Anthropic", "XAI"). Case-insensitive.
        model_name: The specific model name for the provider.
        llm_api_key: The API key for the selected LLM provider.
        tavily_api_key: The API key for Tavily (optional).

    Returns:
        A tuple containing:
        - The initialized LLM client instance (or None on error).
        - The initialized Tavily client instance (or None if no key or error).
        - An error message string (or None if successful).
    """
    llm_instance: Optional[BaseLanguageModel] = None
    tavily_instance: Optional[TavilyClient] = None
    error_message: Optional[str] = None
    provider_lower = provider.lower().strip()

    logger.info(f"Attempting to initialize LLM: Provider='{provider}', Model='{model_name}'")

    # --- LLM Initialization ---
    try:
        if not llm_api_key:
            raise ValueError(f"{provider} API Key is required but was not provided.")

        # Select LLM client based on provider name
        # Common parameters like temperature can be set here
        common_params = {"temperature": 0.5} # Keep a moderate temperature for creativity + structure

        if provider_lower == "openai":
            llm_instance = ChatOpenAI(model=model_name, api_key=llm_api_key, **common_params)
        elif provider_lower == "groq":
            llm_instance = ChatGroq(model=model_name, api_key=llm_api_key, **common_params)
        elif provider_lower == "google":
            llm_instance = ChatGoogleGenerativeAI(model=model_name, google_api_key=llm_api_key, **common_params)
        elif provider_lower == "anthropic":
            # Note: Anthropic models might require more specific prompt engineering for structured output
            llm_instance = ChatAnthropic(model=model_name, anthropic_api_key=llm_api_key, **common_params)
        elif provider_lower == "xai":
            # xAI uses an OpenAI-compatible API endpoint
            llm_instance = ChatOpenAI(model=model_name, api_key=llm_api_key, base_url="https://api.x.ai/v1", **common_params)
        else:
            raise ValueError(f"Unsupported LLM provider specified: '{provider}'. Supported: OpenAI, Groq, Google, Anthropic, XAI.")

        # --- Basic test call to check connectivity/authentication ---
        logger.info(f"Performing a basic test call to {provider} LLM...")
        test_response = llm_instance.invoke("Respond with 'OK'.")
        if not test_response or not hasattr(test_response, 'content') or 'ok' not in test_response.content.lower():
             logger.warning(f"Basic test call to {provider} returned unexpected content: '{getattr(test_response, 'content', 'N/A')}'")
             # Consider this a warning, not necessarily a fatal error
        logger.info(f"LLM client for {provider} ({model_name}) initialized and test call response received.")

    except ValueError as ve:
        error_message = str(ve)
        logger.error(f"LLM Initialization Value Error: {error_message}")
    except ImportError as ie:
        package_name = f"langchain-{provider_lower}"
        if provider_lower == "google": package_name = "langchain-google-genai"
        elif provider_lower == "xai": package_name = "langchain-openai"
        error_message = f"Missing required library for {provider}. Please install `pip install {package_name}`. Error: {ie}"
        logger.error(error_message)
    except ConnectionError as ce: # Catch specific connection errors from test call if raised
         error_message = f"LLM Test Call Error: {ce}"
         logger.error(error_message)
    except Exception as e:
        error_message = f"Unexpected error initializing or testing LLM for {provider}: {e}"
        logger.error(error_message, exc_info=True)

    # Reset instance if any error occurred during LLM init/test
    if error_message:
        llm_instance = None

    # --- Tavily Initialization ---
    if tavily_api_key:
        try:
            logger.info("Initializing Tavily client...")
            tavily_instance = TavilyClient(api_key=tavily_api_key)
            # Add test call if desired
            logger.info("Tavily client initialized successfully.")
        except Exception as e:
            tavily_err_msg = f"Failed to initialize Tavily client: {e}"
            logger.error(tavily_err_msg, exc_info=True)
            # Append Tavily error to any existing LLM error message
            error_message = f"{error_message}; {tavily_err_msg}" if error_message else tavily_err_msg
            tavily_instance = None # Ensure instance is None on error
    else:
        logger.warning("Tavily API Key not provided. Web search functionality will be disabled.")
        tavily_instance = None

    return llm_instance, tavily_instance, error_message

# ==============================================================================
# --- Retry Decorator ---
# Wrapper to automatically retry functions on transient errors or specific validation errors.
# ==============================================================================

def with_retry(func):
    """
    Decorator to add retry logic to LLM calls or other potentially flaky functions.
    Uses exponential backoff. Retries on common network errors and specific
    Pydantic/ValueError exceptions that might indicate recoverable LLM output issues.
    """
    RETRY_ATTEMPTS = 15
    RETRY_MIN_WAIT_SECONDS = 4
    RETRY_MAX_WAIT_SECONDS = 10

    # Define exceptions to retry on more precisely
    # Network errors + Validation errors that might be due to LLM non-conformance
    retryable_exceptions = (
        ConnectionError,
        TimeoutError,
        PydanticValidationError, # Pydantic V2 base error
        CoreValidationError,     # Pydantic core error
        ValueError               # Catch general value errors which might indicate parsing/format issues
    )

    @wraps(func)
    @retry(
        stop=stop_after_attempt(RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT_SECONDS, max=RETRY_MAX_WAIT_SECONDS),
        retry=retry_if_exception_type(retryable_exceptions),
        before_sleep=lambda rs: logger.warning(
            f"Retrying {func.__name__} (attempt {rs.attempt_number}/{RETRY_ATTEMPTS}) "
            f"after {rs.next_action.sleep:.2f}s delay due to: {type(rs.outcome.exception()).__name__}: {str(rs.outcome.exception())[:200]}" # Log exception concisely
        )
    )
    def wrapper(*args, **kwargs):
        try:
            # Execute the wrapped function
            return func(*args, **kwargs)
        except Exception as e:
            # This block is reached only if all retry attempts fail
            logger.error(f"Function {func.__name__} failed after {RETRY_ATTEMPTS} attempts: {e}", exc_info=True)
            # Re-raise the exception to be handled by the calling application layer (e.g., app.py)
            raise
    return wrapper

# ==============================================================================
# --- Workflow Functions (Grouped by SDLC Cycle) ---
# Each function typically:
# 1. Takes the MainState dictionary.
# 2. Performs an action (often involving LLM calls, sometimes with structured output).
# 3. Updates the MainState dictionary with results or intermediate artifacts.
# 4. Returns the modified MainState dictionary.
# ==============================================================================

# ------------------------------------------------------------------------------
# --- 1. Requirements Gathering Cycle ---
# (Functions: generate_questions, refine_prompt - no changes needed based on request)
# ------------------------------------------------------------------------------
@with_retry
def generate_questions(state: MainState) -> MainState:
    """
    Generates clarification questions based on initial project info or previous Q&A.
    Uses regular LLM invocation, not structured output.
    """
    func_name = "generate_questions"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError(f"LLM instance not found in state for {func_name}.")
    if 'messages' not in state: state['messages'] = []

    # --- Context Gathering ---
    project = state.get('project', 'Unnamed Project')
    category = state.get('category', 'N/A')
    subcategory = state.get('subcategory', 'N/A')
    coding_language = state.get('coding_language', 'N/A')
    project_context = f"Project Name: {project}\nCategory: {category}/{subcategory}\nLanguage: {coding_language}"
    iteration = state.get("user_input_iteration", 0)
    logger.debug(f"Generating questions for iteration {iteration}.")

    # --- Prompt Construction ---
    prompt_text: str
    if iteration == 0:
        # Initial questions prompt
        prompt_text = f"""
**Persona:** Requirements Analyst

**Goal:** Generate initial clarification questions about a new software project.

**Project Context:**
{project_context}

**Task:** Ask exactly 5 concise, open-ended questions to understand the core needs, goals, users, and constraints of this project. Focus on the most crucial unknowns to get started.

**Desired Qualities:** Concise, Relevant, Open-ended, Prioritized (most important first).

**Output Format:** Respond with ONLY the 5 questions, each on a new line. Do not include numbering, introductions, explanations, or greetings.
"""
    else:
        # Follow-up questions prompt based on history
        user_questions = state.get("user_input_questions", [])
        user_answers = state.get("user_input_answers", [])
        # Get Q&A pairs from the *most recent* interaction for context
        # Assuming 5 questions per round typically
        num_questions_prev_round = 5 # Adjust if variable
        start_index = max(0, len(user_answers) - num_questions_prev_round)
        prev_qa_pairs = list(zip(user_questions[start_index:], user_answers[start_index:]))

        if not prev_qa_pairs:
             qa_history = "No previous Q&A relevant to this iteration."
             logger.warning(f"Could not reliably extract Q&A from previous iteration ({iteration-1}) for context.")
        else:
             qa_history = "\n".join([f"Q: {q}\nA: {a}" for q, a in prev_qa_pairs])


        prompt_text = f"""
**Persona:** Requirements Analyst

**Goal:** Generate follow-up clarification questions based on the answers just provided.

**Project Context:**
{project_context}

**Previous Q&A (Most Recent Round):**
```
{qa_history if qa_history else "No specific Q&A context for this round."}
```

**Task:** Ask up to 5 *new*, concise clarification questions based specifically on the information and potential ambiguities in the 'Previous Q&A'. Focus on areas needing more detail or confirmation. If everything seems clear, ask about edge cases or non-functional requirements. Avoid repeating previous questions.

**Desired Qualities:** Concise, Relevant, Builds on previous answers, Avoids repetition, Probing.

**Output Format:** Respond with ONLY the new questions (up to 5), each on a new line. Do not include numbering, introductions, or greetings. If no further questions seem necessary, respond with the single phrase: NO_MORE_QUESTIONS
"""

    # --- LLM Invocation ---
    logger.debug(f"Sending prompt to LLM for question generation (Iteration {iteration})...")
    response = llm.invoke(prompt_text)
    generated_content = response.content.strip()

    # --- State Update ---
    questions = []
    no_more_questions_flag = "NO_MORE_QUESTIONS"
    if generated_content and generated_content != no_more_questions_flag:
        questions = [q.strip() for q in generated_content.split("\n") if q.strip() and len(q.strip()) > 5]

    if questions:
        state["user_input_questions"] = state.get("user_input_questions", []) + questions
        logger.info(f"Generated {len(questions)} questions for iteration {iteration}.")
        state["messages"].append(AIMessage(content="Please answer the following questions:\n" + "\n".join([f"- {q}" for q in questions]))) # Use markdown list
    elif generated_content == no_more_questions_flag:
        logger.info(f"LLM indicated no further questions are needed (Iteration {iteration}).")
        state["messages"].append(AIMessage(content="The AI has no further clarification questions at this time."))
        state["user_input_done"] = True
    else:
        logger.warning(f"No new questions generated for iteration {iteration}, and no completion flag received. Assuming Q&A can continue if min iterations not met.")
        state["messages"].append(AIMessage(content="No further questions were generated in this round."))

    return state

@with_retry
def refine_prompt(state: MainState) -> MainState:
    """
    Synthesizes the initial project info and Q&A history into a refined prompt.
    Uses regular LLM invocation. Saves intermediate artifacts.
    """
    func_name = "refine_prompt"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError(f"LLM instance not found in state for {func_name}.")
    if 'messages' not in state: state['messages'] = []

    # --- Context Gathering ---
    project_name = state.get('project', 'Unnamed Project')
    project_details = f"Project: {project_name} ({state.get('category', 'N/A')}/{state.get('subcategory', 'N/A')}) in {state.get('coding_language', 'N/A')}."
    user_questions = state.get("user_input_questions", [])
    user_answers = state.get("user_input_answers", [])

    # Combine Q&A history safely
    qa_history: str
    if not user_questions or not user_answers:
        initial_desc = state.get("project", "No initial project description provided.")
        qa_history = f"Initial Project Description (No Q&A Occurred):\n{initial_desc}"
        logger.warning(f"No Q&A history found for {func_name}. Using initial description only.")
    else:
        min_len = min(len(user_questions), len(user_answers))
        if len(user_questions) != len(user_answers):
            logger.warning(f"Q&A length mismatch in {func_name}: Questions={len(user_questions)}, Answers={len(user_answers)}. Using {min_len} pairs.")
        qa_pairs = zip(user_questions[:min_len], user_answers[:min_len])
        qa_history = "\n\n".join([f"Q: {q.strip()}\nA: {a.strip()}" for q, a in qa_pairs])

    # Store the combined Q&A history for potential saving
    state["user_query_with_qa"] = qa_history

    # --- Prompt Construction ---
    prompt_text = f"""
**Persona:** Expert Requirements Analyst & Technical Writer

**Goal:** Transform the provided project details and Q&A history into a single, well-structured 'Refined Project Prompt' for subsequent SDLC stages.

**Input Context:**
*   **Base Project Details:** {project_details}
*   **Full Q&A Discussion / Initial Description:**
    ```
    {qa_history}
    ```

**Task:**
Synthesize *all* essential requirements, decisions, constraints, user roles, goals, and clarifications from the entire input context into one coherent and unambiguous prompt. Discard conversational filler, repetitions, and greetings. Focus solely on the consolidated requirements. If contradictions exist, prioritize later answers in the Q&A. Structure the output logically (e.g., Goal, Key Features, Target Users, Constraints, Non-Functional Requirements).

**Desired Qualities for the Refined Prompt:** Clear & Unambiguous; Complete; Concise; Actionable; Faithful (reflect inputs, don't invent).

**Output Format:**
Respond with *only* the final 'Refined Project Prompt' text itself. Do not include any introductory phrases, explanations, markdown formatting (like ### or ```), or any other text. Just the plain text of the synthesized prompt.
"""
    # --- LLM Invocation ---
    logger.debug(f"Sending prompt to LLM for prompt refinement (History Length: {len(qa_history)})...")
    response = llm.invoke(prompt_text)
    refined_prompt_text = response.content.strip()
    if not refined_prompt_text:
        logger.error("LLM failed to generate refined prompt text. Result is empty.")
        raise ValueError("LLM returned empty content for the refined prompt.")

    state["refined_prompt"] = refined_prompt_text
    state["messages"].append(AIMessage(content=f"Refined Project Prompt:\n{refined_prompt_text}"))
    logger.info("Refined project prompt generated based on Q&A.")

    # --- Save Artifacts (MD and PDF) ---
    md_path: Optional[str] = None
    pdf_path: Optional[str] = None
    try:
        project_folder_name = state.get("project_folder", "default_sdlc_project")
        abs_project_folder = os.path.abspath(project_folder_name)
        intro_dir = os.path.join(abs_project_folder, "1_requirements")
        os.makedirs(intro_dir, exist_ok=True)

        # Save Q&A History (no change)
        if state.get("user_query_with_qa"):
             qa_file_path = os.path.join(intro_dir, "qa_history.txt")
             with open(qa_file_path, "w", encoding="utf-8") as f: f.write(state["user_query_with_qa"])
             logger.debug(f"Saved Q&A history to {qa_file_path}")

        # Save Refined Prompt MD
        md_path = os.path.join(intro_dir, "refined_prompt.md")
        with open(md_path, "w", encoding="utf-8") as f: f.write(refined_prompt_text)
        logger.info(f"Saved refined prompt markdown: {os.path.basename(md_path)}")

        # --- ADDED: Generate and Save PDF ---
        pdf_path = os.path.join(intro_dir, "refined_prompt.pdf")
        if convert_md_to_pdf(refined_prompt_text, pdf_path):
            logger.info(f"Saved refined prompt PDF: {os.path.basename(pdf_path)}")
        else:
            logger.warning(f"Failed to generate PDF for refined prompt.")
            pdf_path = None # Ensure path is None if PDF generation fails
        # --- END ADDED ---

    except (ValueError, OSError, TypeError) as e:
        logger.error(f"Failed to save requirements artifacts: {e}", exc_info=True)
        md_path = None
        pdf_path = None

    state["refined_prompt_path"] = md_path
    state["refined_prompt_pdf_path"] = pdf_path # Store PDF path

    return state

# ------------------------------------------------------------------------------
# --- 2. User Story Cycle ---
# (Functions: generate_initial_user_stories, generate_user_story_feedback, refine_user_stories, save_final_user_story - no changes needed)
# ------------------------------------------------------------------------------
@with_retry
def generate_initial_user_stories(state: MainState) -> MainState:
    """Generates initial user stories based on the refined prompt."""
    func_name = "generate_initial_user_stories"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    refined_prompt = state.get('refined_prompt')
    if not refined_prompt: raise ValueError("Cannot generate user stories without a refined prompt.")

    prompt_text = f"""
**Persona:** Agile Business Analyst
**Goal:** Generate a comprehensive list of initial user stories based on the refined requirements.
**Input Context:**
*   **Refined Project Prompt:** ```{refined_prompt}```
**Task:** Analyze the prompt, identify user roles and requirements, and formulate stories using the format "As a [user], I want [task], so that [goal]." Aim for INVEST principles. Cover core functionality.
**Desired Qualities:** Standard Format, Completeness, Clarity, Atomicity, INVEST considered.
**Output Format:** Respond with *only* the list of user stories, each on a new line starting with "As a...". No introductions or extra text.
"""
    logger.debug(f"Sending prompt to LLM for initial user stories (Prompt Length: {len(refined_prompt)})...")
    response = llm.invoke(prompt_text)
    initial_user_stories = response.content.strip()

    if not initial_user_stories: raise ValueError("LLM returned empty content for initial user stories.")

    state["user_story_current"] = initial_user_stories
    state["messages"].append(AIMessage(content=f"**Initial User Stories Generated:**\n\n{initial_user_stories}"))
    logger.info("Generated Initial User Stories.")
    return state

@with_retry
def generate_user_story_feedback(state: MainState) -> MainState:
    """Generates AI feedback on the current user stories."""
    func_name = "generate_user_story_feedback"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    current_stories = state.get('user_story_current')
    refined_prompt = state.get('refined_prompt', "[Refined Prompt Missing]")

    if not current_stories:
        logger.warning(f"No current user stories found for {func_name}. Skipping feedback.")
        state["user_story_feedback"] = "[Feedback Skipped: No user stories available]"
        state["messages"].append(AIMessage(content="User Story Feedback: Skipped - No stories found."))
        return state

    prompt_text = f"""
**Persona:** Experienced Agile Coach / QA Lead
**Goal:** Review user stories for quality, completeness, INVEST criteria, and alignment with the project prompt.
**Input Context:**
*   **Refined Project Prompt:** ```{refined_prompt}```
*   **User Stories Under Review:** ```{current_stories}```
**Task:** Review the stories. Evaluate against INVEST and prompt alignment. Provide specific, actionable feedback on clarity, size, value, testability, gaps, format adherence, overlaps, and weak value props.
**Desired Qualities:** Constructive, Specific, Actionable, Aligned with INVEST & Prompt.
**Output Format:** Respond with *only* the feedback text. No introductions or story summaries. Use clear points. Start directly with feedback.
"""
    logger.debug(f"Sending prompt to LLM for user story feedback (Stories Length: {len(current_stories)})...")
    response = llm.invoke(prompt_text)
    feedback = response.content.strip()

    if not feedback: feedback = "[AI Feedback Generation Resulted in Empty Content]"

    state["user_story_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"**AI Feedback on User Stories:**\n\n{feedback}"))
    logger.info("Generated feedback on user stories.")
    return state

@with_retry
def refine_user_stories(state: MainState) -> MainState:
    """Refines user stories based on AI and human feedback."""
    func_name = "refine_user_stories"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    current_stories = state.get('user_story_current')
    ai_feedback = state.get('user_story_feedback', '[No AI Feedback Provided]')
    human_feedback = state.get('user_story_human_feedback', '[No Human Feedback Provided]')
    refined_prompt = state.get('refined_prompt', "[Refined Prompt Missing]")

    if not current_stories: raise ValueError("Current user stories are missing in state.")

    prompt_text = f"""
**Persona:** Agile Business Analyst (Revising Stories)
**Goal:** Revise user stories based on AI and human feedback, ensuring alignment with prompt and INVEST.
**Input Context:**
*   **Refined Project Prompt:** ```{refined_prompt}```
*   **Current User Stories (To Be Revised):** ```{current_stories}```
*   **AI Feedback on Stories:** ```{ai_feedback}```
*   **Human Feedback on Stories:** ```{human_feedback}```
**Task:** Review stories and feedback. Incorporate feedback: reword for clarity/format, split large stories, add missing, remove redundant, strengthen value. Ensure alignment with prompt & INVEST. Address actionable points.
**Desired Qualities:** Improved Clarity, Better Adherence to INVEST, Completeness, Standard Format, Incorporation of Feedback.
**Output Format:** Respond with *only* the complete, refined list of user stories. Each story on a new line starting with "As a...". No introductions or extra text. Note it should able to properly separate each "As a ..." with new line when we preview this .md in md preview and also when convert that preview in PDF.
"""
    logger.debug(f"Sending prompt to LLM for user story refinement...")
    response = llm.invoke(prompt_text)
    refined_user_stories = response.content.strip()

    if not refined_user_stories: raise ValueError("LLM returned empty content when refining user stories.")
    if not refined_user_stories.lower().startswith("as a"): logger.warning(f"Refined user stories output in {func_name} doesn't start as expected.")

    state["user_story_current"] = refined_user_stories
    state["messages"].append(AIMessage(content=f"**Refined User Stories (incorporating feedback):**\n\n{refined_user_stories}"))
    logger.info("Refined User Stories based on feedback.")
    return state

def save_final_user_story(state: MainState) -> MainState:
    """Saves the final version of user stories to MD and PDF files."""
    logger.info("Executing save_final_user_story...")
    final_stories = state.get("user_story_current", "[No user stories were finalized]")
    state["final_user_story"] = final_stories
    md_path: Optional[str] = None
    pdf_path: Optional[str] = None
    try:
        project_folder = state.get("project_folder")
        if not project_folder: raise ValueError("Project folder path is missing in state.")
        abs_project_folder = os.path.abspath(project_folder)
        us_dir = os.path.join(abs_project_folder, "2_user_story")
        os.makedirs(us_dir, exist_ok=True)

        # Save MD
        md_path = os.path.join(us_dir, "final_user_stories.md")
        md_content_with_header = f"# Final User Stories\n\n{final_stories}" # Add header for PDF clarity
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content_with_header)
        logger.info(f"Saved final user stories markdown: {os.path.basename(md_path)}")

        # --- ADDED: Generate and Save PDF ---
        pdf_path = os.path.join(us_dir, "final_user_stories.pdf")
        if convert_md_to_pdf(md_content_with_header, pdf_path):
             logger.info(f"Saved final user stories PDF: {os.path.basename(pdf_path)}")
        else:
             logger.warning("Failed to generate PDF for final user stories.")
             pdf_path = None
        # --- END ADDED ---

    except (ValueError, OSError, TypeError) as e:
        logger.error(f"Failed to save final user story artifacts: {e}", exc_info=True)
        md_path = None
        pdf_path = None

    state["final_user_story_path"] = md_path
    state["final_user_story_pdf_path"] = pdf_path # Store PDF path
    return state

# ------------------------------------------------------------------------------
# --- 3. Product Review Cycle ---
# (Functions: generate_initial_product_review, generate_product_review_feedback, refine_product_review, save_final_product_review - no changes needed)
# ------------------------------------------------------------------------------
@with_retry
def generate_initial_product_review(state: MainState) -> MainState:
    """Generates an initial product review from a Product Owner perspective."""
    func_name = "generate_initial_product_review"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    refined_prompt = state.get('refined_prompt')
    final_user_story = state.get('final_user_story')
    project_name = state.get('project', 'Unnamed Project')

    if not refined_prompt: raise ValueError(f"Refined prompt is missing for {func_name}.")
    if not final_user_story: raise ValueError(f"Final user stories are missing for {func_name}.")

    prompt_text = f"""
**Persona:** Product Owner (PO) for '{project_name}'
**Goal:** Conduct an initial review of the prompt and stories for business alignment, completeness, risks, and vision coherence.
**Input Context:**
*   **Refined Project Prompt:** ```{refined_prompt}```
*   **Final User Stories:** ```{final_user_story}```
**Task:** As PO, review inputs. Provide a review covering: Alignment & Value, Completeness (MVP Focus), Priorities & Dependencies (initial thoughts), Business Concerns/Risks, Overall Vision Coherence.
**Desired Qualities:** Business-focused, Strategic, Insightful, Concise, Actionable.
**Output Format:** Respond with *only* the PO's review text. Use clear paragraphs/bullets. No introductions or summaries. Start directly with review content.
"""
    logger.debug(f"Sending prompt to LLM for initial product review...")
    response = llm.invoke(prompt_text)
    initial_review = response.content.strip()

    if not initial_review: raise ValueError("LLM returned empty content for initial product review.")

    state["product_review_current"] = initial_review
    state["messages"].append(AIMessage(content=f"**Initial Product Owner Review Generated:**\n\n{initial_review}"))
    logger.info("Generated initial product owner review.")
    return state

@with_retry
def generate_product_review_feedback(state: MainState) -> MainState:
    """Generates AI feedback on the quality and clarity of the Product Owner's review."""
    func_name = "generate_product_review_feedback"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    po_review = state.get('product_review_current')
    if not po_review:
        logger.warning(f"No PO review found for {func_name}. Skipping feedback.")
        state["product_review_feedback"] = "[Feedback Skipped: No PO review available]"
        state["messages"].append(AIMessage(content="Product Review Feedback: Skipped - No review found."))
        return state

    final_user_story_sum = state.get('final_user_story', '[Missing Stories Context]')[:MAX_CONTEXT_LEN // 2]
    refined_prompt_sum = state.get('refined_prompt', '[Missing Prompt Context]')[:MAX_CONTEXT_LEN // 2]

    prompt_text = f"""
**Persona:** Lead Business Analyst / Project Manager
**Goal:** Review a PO's assessment for clarity, logic, completeness, and actionability from a project management view.
**Input Context (Background Only):**
*   *Refined Project Prompt Summary:* ```{refined_prompt_sum}...```
*   *Final User Stories Summary:* ```{final_user_story_sum}...```
**Product Owner Review Under Assessment (Primary Input):** ```{po_review}```
**Task:** Analyze the PO Review. Evaluate: Clarity & Structure, Logic & Justification, Completeness (key PO points), Actionability, Tone. Suggest improvements *to the review document itself*. Focus on review quality, not PO opinions.
**Desired Qualities:** Objective, Constructive, Focused on Review Quality, Suggests Report Improvements, PM Perspective.
**Output Format:** Respond with *only* the feedback on the PO's review. Use clear points. No introductions or summaries. Start directly with feedback.
"""
    logger.debug(f"Sending prompt to LLM for PO review feedback (Review Length: {len(po_review)})...")
    response = llm.invoke(prompt_text)
    feedback = response.content.strip()

    if not feedback: feedback = "[AI Feedback Generation Resulted in Empty Content]"

    state["product_review_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"**AI Feedback on Product Review:**\n\n{feedback}"))
    logger.info("Generated feedback on product review.")
    return state

@with_retry
def refine_product_review(state: MainState) -> MainState:
    """Refines the Product Owner's review based on AI and human feedback."""
    func_name = "refine_product_review"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    current_review = state.get('product_review_current')
    ai_feedback = state.get('product_review_feedback', '[No AI Feedback Provided]')
    human_feedback = state.get('product_review_human_feedback', '[No Human Feedback Provided]')
    project_name = state.get('project', 'Unnamed Project')

    if not current_review: raise ValueError("Current product review is missing in state.")

    prompt_text = f"""
**Persona:** Product Owner (PO) for '{project_name}' (Revising Document)
**Goal:** Refine the PO review based on AI and human feedback for clarity, impact, and actionability.
**Input Context:**
*   **Current PO Review (To Be Revised):** ```{current_review}```
*   **AI Feedback on Review:** ```{ai_feedback}```
*   **Human Feedback on Review:** ```{human_feedback}```
**Task:** Act as PO revising the 'Current PO Review'. Consider all feedback. Incorporate suggestions to improve clarity, structure, logic, completeness, actionability while maintaining your business assessment. Address feedback points you agree add value.
**Desired Qualities:** Improved Clarity, Stronger Justification, More Comprehensive, Actionable, Consistent PO Voice.
**Output Format:** Respond with *only* the refined PO review text. No introductions, explanations, or feedback summaries. Start directly with the refined review.
"""
    logger.debug(f"Sending prompt to LLM for product review refinement...")
    response = llm.invoke(prompt_text)
    refined_review = response.content.strip()

    if not refined_review: raise ValueError("LLM returned empty content when refining product review.")

    state["product_review_current"] = refined_review
    state["messages"].append(AIMessage(content=f"**Refined Product Owner Review:**\n\n{refined_review}"))
    logger.info("Refined product owner review.")
    return state

def save_final_product_review(state: MainState) -> MainState:
    """Saves the final product review to MD and PDF files."""
    logger.info("Executing save_final_product_review...")
    final_review = state.get("product_review_current", "[No product review was finalized]")
    state["final_product_review"] = final_review
    md_path: Optional[str] = None
    pdf_path: Optional[str] = None
    try:
        project_folder = state.get("project_folder")
        if not project_folder: raise ValueError("Project folder path is missing in state.")
        abs_project_folder = os.path.abspath(project_folder)
        pr_dir = os.path.join(abs_project_folder, "3_product_review")
        os.makedirs(pr_dir, exist_ok=True)

        # Save MD
        md_path = os.path.join(pr_dir, "final_product_review.md")
        md_content_with_header = f"# Final Product Owner Review\n\n{final_review}"
        with open(md_path, "w", encoding="utf-8") as f:
             f.write(md_content_with_header)
        logger.info(f"Saved final product review markdown: {os.path.basename(md_path)}")

        # --- ADDED: Generate and Save PDF ---
        pdf_path = os.path.join(pr_dir, "final_product_review.pdf")
        if convert_md_to_pdf(md_content_with_header, pdf_path):
            logger.info(f"Saved final product review PDF: {os.path.basename(pdf_path)}")
        else:
            logger.warning("Failed to generate PDF for final product review.")
            pdf_path = None
        # --- END ADDED ---

    except (ValueError, OSError, TypeError) as e:
        logger.error(f"Failed to save final product review artifacts: {e}", exc_info=True)
        md_path = None
        pdf_path = None
    state["final_product_review_path"] = md_path
    state["final_product_review_pdf_path"] = pdf_path # Store PDF path
    return state

# ------------------------------------------------------------------------------
# --- 4. Design Document Cycle ---
# (Functions: generate_initial_design_doc, generate_design_doc_feedback, refine_design_doc, save_final_design_doc - no changes needed)
# ------------------------------------------------------------------------------
@with_retry
def generate_initial_design_doc(state: MainState) -> MainState:
    """Generates the initial high-level technical design document using Markdown."""
    func_name = "generate_initial_design_doc"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    refined_prompt = state.get('refined_prompt')
    final_user_story = state.get('final_user_story')
    final_product_review = state.get('final_product_review', '[Product Owner Review Missing]')
    project_name = state.get('project', 'Unnamed Project')
    coding_language = state.get('coding_language', 'Not Specified')

    if not refined_prompt: raise ValueError(f"Refined prompt is missing for {func_name}.")
    if not final_user_story: raise ValueError(f"Final user stories are missing for {func_name}.")
    if final_product_review == '[Product Owner Review Missing]': logger.warning(f"Final PO Review is missing for {func_name}.")

    prompt_text = f"""
**Persona:** System Architect / Lead Developer for '{project_name}'
**Goal:** Create an initial high-level technical design document (Markdown) based on requirements, stories, and PO feedback.
**Input Context:**
*   **Refined Project Prompt:** ```{refined_prompt}```
*   **Final User Stories:** ```{final_user_story}```
*   **Final Product Owner Review (Context):** ```{final_product_review}```
**Task:** Generate a design doc for {coding_language} covering: `## 1. Introduction & Goals`, `## 2. Architecture Overview`, `## 3. Key Components/Modules`, `## 4. Data Model/Storage`, `## 5. API Design (Conceptual)`, `## 6. Technology Stack (Proposed)`, `## 7. Deployment Strategy (Initial)`, `## 8. Scalability and Performance`, `## 9. Security Considerations`, `## 10. Open Questions/Risks`. Justify key choices.
**Desired Qualities:** Technically Sound, Comprehensive, Clear, Concise, Aligned with Requirements, Justified Choices, Uses Specified Markdown Structure.
**Output Format:** Respond with *only* the design document markdown text, using `##` headers for sections 1-10. No introductions or summaries. Start directly with `## 1. Introduction & Goals`.
"""
    logger.debug(f"Sending prompt to LLM for initial design document...")
    response = llm.invoke(prompt_text)
    initial_doc = response.content.strip()

    required_headers = [f"## {i+1}." for i in range(10)]
    if not initial_doc or len(initial_doc) < 200 or not all(header in initial_doc for header in required_headers):
        raise ValueError(f"LLM returned empty, minimal, or incorrectly structured content for the initial design document in {func_name}.")

    state["design_doc_current"] = initial_doc
    state["messages"].append(AIMessage(content=f"**Initial Design Document Generated:**\n\n{initial_doc[:1000]}...\n*(Full document stored in state)*"))
    logger.info("Generated Initial Design Document.")
    return state

@with_retry
def generate_design_doc_feedback(state: MainState) -> MainState:
    """Generates AI feedback on the technical design document."""
    func_name = "generate_design_doc_feedback"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    current_design_doc = state.get('design_doc_current')
    if not current_design_doc:
        logger.warning(f"No design document found for {func_name}. Skipping feedback.")
        state["design_doc_feedback"] = "[Feedback Skipped: No design document available]"
        state["messages"].append(AIMessage(content="Design Doc Feedback: Skipped - No document found."))
        return state

    refined_prompt_sum = state.get('refined_prompt', '[Missing Prompt Context]')[:MAX_CONTEXT_LEN // 2]
    final_user_story_sum = state.get('final_user_story', '[Missing Stories Context]')[:MAX_CONTEXT_LEN // 2]

    prompt_text = f"""
**Persona:** Senior Software Engineer / Technical Reviewer
**Goal:** Review a design doc for feasibility, completeness, clarity, consistency, tech choices, risks, and requirement alignment.
**Input Context (Background Only):**
*   *Refined Project Prompt Summary:* ```{refined_prompt_sum}...```
*   *Final User Stories Summary:* ```{final_user_story_sum}...```
**Design Document Under Review (Primary Input):** ```markdown\n{current_design_doc}\n```
**Task:** Evaluate the design doc. Provide feedback on: Feasibility, Completeness & Clarity, Consistency, Technology Choices, Risks/Challenges, Alignment with requirements.
**Desired Qualities:** Technical Depth, Constructive Criticism, Specific Examples, Actionable Suggestions, Balanced Perspective.
**Output Format:** Respond with *only* the feedback text. Structure clearly (e.g., by section). No introductions or summaries. Start directly with feedback.
"""
    logger.debug(f"Sending prompt to LLM for design doc feedback (Doc Length: {len(current_design_doc)})...")
    response = llm.invoke(prompt_text)
    feedback = response.content.strip()

    if not feedback: feedback = "[AI Feedback Generation Resulted in Empty Content]"

    state["design_doc_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"**AI Feedback on Design Document:**\n\n{feedback}"))
    logger.info("Generated Design Document Feedback.")
    return state

@with_retry
def refine_design_doc(state: MainState) -> MainState:
    """Refines the design document based on AI and human feedback."""
    func_name = "refine_design_doc"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    current_doc = state.get('design_doc_current')
    ai_feedback = state.get('design_doc_feedback', '[No AI Feedback Provided]')
    human_feedback = state.get('design_doc_human_feedback', '[No Human Feedback Provided]')
    project_name = state.get('project', 'Unnamed Project')

    if not current_doc: raise ValueError("Current design document is missing in state.")

    prompt_text = f"""
**Persona:** System Architect / Lead Developer for '{project_name}' (Revising Document)
**Goal:** Revise the design doc based on AI/human feedback for improved robustness, clarity, and technical soundness.
**Input Context:**
*   **Current Design Document (To Be Revised):** ```markdown\n{current_doc}\n```
*   **AI Feedback on Design:** ```{ai_feedback}```
*   **Human Feedback on Design:** ```{human_feedback}```
**Task:** Act as architect revising the design. Incorporate feedback to improve feasibility, completeness, clarity, consistency, risk mitigation. Address feedback points where valuable. Maintain the standard 10-section markdown structure (`## 1. ...`). Update relevant sections. Output the *complete* refined document.
**Desired Qualities:** Improved Clarity, Technical Soundness, Completeness, Risk Mitigation, Incorporation of Feedback, Consistent Structure.
**Output Format:** Respond with *only* the complete, refined design doc (markdown, `##` headers 1-10). No introductions or summaries. Start directly with `## 1. Introduction & Goals`.
"""
    logger.debug(f"Sending prompt to LLM for design doc refinement...")
    response = llm.invoke(prompt_text)
    refined_doc = response.content.strip()

    required_headers = [f"## {i+1}." for i in range(10)]
    if not refined_doc or len(refined_doc) < 200 or not all(header in refined_doc for header in required_headers):
        raise ValueError(f"LLM returned empty, minimal, or incorrectly structured content when refining the design document in {func_name}.")

    state["design_doc_current"] = refined_doc
    state["messages"].append(AIMessage(content=f"**Refined Design Document (incorporating feedback):**\n\n{refined_doc[:1000]}...\n*(Full document stored in state)*"))
    logger.info("Refined Design Document based on feedback.")
    return state

def save_final_design_doc(state: MainState) -> MainState:
    """Saves the final design document to MD and PDF files."""
    logger.info("Executing save_final_design_doc...")
    final_doc = state.get("design_doc_current", "[No design document was finalized]")
    state["final_design_document"] = final_doc
    md_path: Optional[str] = None
    pdf_path: Optional[str] = None
    try:
        project_folder = state.get("project_folder")
        if not project_folder: raise ValueError("Project folder path is missing in state.")
        abs_project_folder = os.path.abspath(project_folder)
        dd_dir = os.path.join(abs_project_folder, "4_design_doc")
        os.makedirs(dd_dir, exist_ok=True)

        # Save MD (Assume final_doc already has good markdown structure)
        md_path = os.path.join(dd_dir, "final_design_document.md")
        with open(md_path, "w", encoding="utf-8") as f:
             f.write(final_doc) # Might already have a header from generation prompt
        logger.info(f"Saved final design doc markdown: {os.path.basename(md_path)}")

        # --- ADDED: Generate and Save PDF ---
        pdf_path = os.path.join(dd_dir, "final_design_document.pdf")
        # Add a top-level header if the generator might not include one
        md_content_for_pdf = final_doc
        if not final_doc.strip().startswith("#"):
            md_content_for_pdf = f"# Final Design Document\n\n{final_doc}"

        if convert_md_to_pdf(md_content_for_pdf, pdf_path):
            logger.info(f"Saved final design doc PDF: {os.path.basename(pdf_path)}")
        else:
            logger.warning("Failed to generate PDF for final design document.")
            pdf_path = None
        # --- END ADDED ---

    except (ValueError, OSError, TypeError) as e:
        logger.error(f"Failed save design doc artifacts: {e}", exc_info=True)
        md_path = None
        pdf_path = None
    state["final_design_document_path"] = md_path
    state["final_design_document_pdf_path"] = pdf_path # Store PDF path
    return state

# ------------------------------------------------------------------------------
# --- 5. UML Diagram Cycle ---
# (Functions: select_uml_diagrams, generate_initial_uml_codes, generate_uml_feedback, refine_uml_codes, save_final_uml_diagrams - no changes needed)
# ------------------------------------------------------------------------------
@with_retry
def select_uml_diagrams(state: MainState) -> MainState:
    """Selects relevant UML/DFD diagram types based on the design doc using structured output."""
    func_name = "select_uml_diagrams"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    final_design_document = state.get('final_design_document')
    if not final_design_document or final_design_document == "[No design document was finalized]":
         raise ValueError(f"Final design document is missing or invalid for {func_name}.")

    project_name = state.get('project', 'Unnamed Project')
    all_diagram_types = list(PLANTUML_SYNTAX_RULES.keys())

    prompt_text = f"""
**Persona:** System Designer / Software Modeler
**Goal:** Select the 5 most relevant UML/DFD diagrams for the design.
**Input Context:**
*   **Final Design Document:** ```markdown\n{final_design_document}\n```
*   **Available Diagram Types:** {', '.join(all_diagram_types)}
**Task:** Analyze the design. Select exactly 5 types from 'Available Diagram Types' that provide the most value. Provide a brief 1-sentence justification for each.
**Desired Qualities:** Relevance, Clear Justifications, Exactly 5, Correct Diagram Names.
**Output Format:** Respond ONLY with a valid JSON object matching 'DiagramSelection' schema. No ```json block.
**DiagramSelection Schema:**
```json
{{
  "diagram_types": ["Type1", "Type2", "Type3", "Type4", "Type5"],
  "justifications": ["Justification 1...", "Justification 2...", ...]
}}
```
Ensure exactly 5 unique types from Available list and 5 non-empty justifications.
"""
    logger.debug(f"Sending prompt to LLM for UML diagram selection (Design Doc Length: {len(final_design_document)})...")
    structured_llm = llm.with_structured_output(DiagramSelection)
    selected_diagrams = []
    justifications_text = "Error during selection."

    try:
        response: DiagramSelection = structured_llm.invoke(prompt_text)
        if not response or not response.diagram_types or not response.justifications: raise ValueError("LLM response parsed but missing fields.")
        if len(response.diagram_types) != 5 or len(response.justifications) != 5: raise ValueError(f"LLM response not exactly 5 diagrams/justifications.")
        unknown_types = [dt for dt in response.diagram_types if dt not in PLANTUML_SYNTAX_RULES]
        if unknown_types: logger.warning(f"LLM selected unknown diagram types: {unknown_types}")

        selected_diagrams = response.diagram_types
        justifications_text = "\n".join(f"- **{dtype}:** {just}" for dtype, just in zip(selected_diagrams, response.justifications))
        logger.info(f"Selected UML Diagrams: {', '.join(selected_diagrams)}")

    except (PydanticValidationError, CoreValidationError) as e:
        logger.error(f"Pydantic validation failed for diagram selection in {func_name}: {e}", exc_info=True)
        raise ValueError(f"LLM structured output validation failed for diagram selection: {e}") from e
    except ValueError as ve:
        logger.error(f"Output validation failed for diagram selection in {func_name}: {ve}", exc_info=True)
        raise
    except Exception as e:
         logger.error(f"Unexpected error during UML diagram selection in {func_name}: {e}", exc_info=True)
         raise

    state["uml_selected_diagrams"] = selected_diagrams
    display_msg = f"**Selected UML/DFD Diagrams & Justifications:**\n{justifications_text}"
    state["messages"].append(AIMessage(content=display_msg))
    return state

@with_retry
def generate_initial_uml_codes(state: MainState) -> MainState:
    """Generates initial PlantUML code for each selected diagram type using structured output."""
    func_name = "generate_initial_uml_codes"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    final_design_document = state.get('final_design_document')
    selected_diagrams = state.get("uml_selected_diagrams", [])
    project_name = state.get('project', 'Unnamed Project')

    if not selected_diagrams:
        logger.warning(f"No diagrams selected for {func_name}, skipping UML code generation.")
        state["uml_current_codes"] = []
        state["messages"].append(AIMessage(content="Skipped UML code generation: No diagrams selected."))
        return state

    final_design_document_sum = final_design_document[:MAX_CONTEXT_LEN + 5000] if final_design_document else "[Design Doc Missing]"
    if final_design_document_sum == "[Design Doc Missing]": logger.warning(f"Design doc missing for {func_name}, UML quality poor.")

    generated_codes_list: List[PlantUMLCode] = []
    structured_llm = llm.with_structured_output(PlantUMLCode)
    logger.info(f"Generating initial PlantUML code for: {', '.join(selected_diagrams)}")

    errors_occurred = False
    for diagram_type in selected_diagrams:
        logger.debug(f"Generating code for diagram type: {diagram_type}")
        syntax_info = PLANTUML_SYNTAX_RULES.get(diagram_type, {})
        template = syntax_info.get("template", f"@startuml\n' Error: No template found\n@enduml")
        notes = syntax_info.get("notes", "N/A.")

        prompt_text = f"""
**Persona:** PlantUML Expert / System Modeler
**Goal:** Generate PlantUML code for a '{diagram_type}' based on the design document.
**Input Context:**
*   **Final Design Document (or Summary):** ```markdown\n{final_design_document_sum}...\n```
*   **Project Name:** {project_name}
*   **Diagram Type Requested:** {diagram_type}
*   **PlantUML Syntax Reference (for {diagram_type}):** Template: `{template}` Notes: `{notes}`
**Task:** Analyze design, generate PlantUML for '{diagram_type}'. Focus on pertinent info. Adhere to syntax/reference. Start with `@startuml`, end with `@enduml`. Be reasonably detailed but not overly complex. Use meaningful names.
**Desired Qualities:** Syntactically Correct PlantUML, Relevant to Design, Adheres to Diagram Purpose, Clear Naming.
**Output Format:** Respond ONLY with valid JSON matching 'PlantUMLCode' schema. No ```json block.
**PlantUMLCode Schema:** ```json\n{{ "diagram_type": "{diagram_type}", "code": "@startuml\\n...code...\\n@enduml" }}\n``` 'diagram_type' MUST be '{diagram_type}'. 'code' must be PlantUML string starting `@startuml`, ending `@enduml`.
"""
        logger.debug(f"Sending prompt to LLM for initial UML code ({diagram_type})...")
        code_to_add: Optional[PlantUMLCode] = None
        try:
            response: PlantUMLCode = structured_llm.invoke(prompt_text)
            if not response or not response.code: raise ValueError("Missing code content.")
            if response.diagram_type != diagram_type: raise ValueError(f"Diagram type mismatch: expected {diagram_type}, got {response.diagram_type}.")
            # Pydantic model handles start/end marker validation now
            code_to_add = response
            logger.info(f"Successfully generated and validated PlantUML for {diagram_type}.")
        except (PydanticValidationError, CoreValidationError, ValueError) as e:
             logger.error(f"Validation failed for {diagram_type} in {func_name}: {e}. Reverting to template.", exc_info=False) # Less verbose traceback for validation errors
             code_to_add = PlantUMLCode(diagram_type=diagram_type, code=template + f"\n' Error: Failed validation - {e}'")
             errors_occurred = True
        except Exception as e:
             logger.error(f"Unexpected error generating UML code for {diagram_type} in {func_name}: {e}. Reverting to template.", exc_info=True)
             code_to_add = PlantUMLCode(diagram_type=diagram_type, code=template + f"\n' Error: Unexpected failure - {e}'")
             errors_occurred = True

        if code_to_add: generated_codes_list.append(code_to_add)
        else: # Should not happen with error handling above
             logger.error(f"Logic error: No code object for {diagram_type}, adding error template.")
             generated_codes_list.append(PlantUMLCode(diagram_type=diagram_type, code=template + "\n' Error: Unknown generation failure'"))
             errors_occurred = True

    state["uml_current_codes"] = generated_codes_list
    summary = "\n\n".join([f"**{c.diagram_type}**:\n```plantuml\n{c.code[:300].strip()}...\n```" for c in generated_codes_list])
    state["messages"].append(AIMessage(content=f"**Generated Initial UML Codes ({len(generated_codes_list)}):**\n{summary}"))
    logger.info(f"Finished generating initial code for {len(generated_codes_list)} UML diagrams.")
    if errors_occurred: logger.warning(f"One or more UML diagrams reverted to templates due to errors in {func_name}.")
    return state

@with_retry
def generate_uml_feedback(state: MainState) -> MainState:
    """Generates AI feedback for each current UML diagram code based on design alignment and syntax."""
    func_name = "generate_uml_feedback"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    final_design_document = state.get('final_design_document')
    current_codes = state.get('uml_current_codes', [])
    project_name = state.get('project', 'Unnamed Project')

    if not current_codes:
        logger.warning(f"No UML codes available for {func_name}. Skipping feedback.")
        state["uml_feedback"] = {}
        state["messages"].append(AIMessage(content="UML Feedback Skipped: No diagrams found."))
        return state

    final_design_document_sum = final_design_document[:MAX_CONTEXT_LEN] if final_design_document else "[Design Doc Missing]"
    if final_design_document_sum == "[Design Doc Missing]": logger.warning(f"Design doc missing for {func_name}, feedback accuracy reduced.")

    feedback_dict: Dict[str, str] = {}
    logger.info(f"Generating feedback for {len(current_codes)} UML diagrams.")

    for plantuml_code_obj in current_codes:
        diagram_type = plantuml_code_obj.diagram_type
        code_to_review = plantuml_code_obj.code
        syntax_info = PLANTUML_SYNTAX_RULES.get(diagram_type, {})
        template = syntax_info.get("template", "N/A")
        notes = syntax_info.get("notes", "N/A")

        prompt_text = f"""
**Persona:** PlantUML Expert / Technical Reviewer
**Goal:** Review PlantUML code for '{diagram_type}' for syntax, clarity, and design alignment.
**Input Context:**
*   **Final Design Document (Summary):** ```markdown\n{final_design_document_sum}...\n```
*   **Project Name:** {project_name}
*   **Diagram Type:** {diagram_type}
*   **PlantUML Code Under Review:** ```plantuml\n{code_to_review}\n```
*   **PlantUML Syntax Reference (Context):** Template: `{template}` Notes: `{notes}`
**Task:** Review the PlantUML code. Provide feedback on: Syntax Correctness & Best Practices, Clarity & Readability, Alignment with Design Summary, Completeness (for type).
**Desired Qualities:** Specific, Constructive, Technically Insightful, Actionable Suggestions.
**Output Format:** Respond with *only* feedback for {diagram_type}. Use clear points. No introductions or summaries. Start directly with feedback.
"""
        logger.debug(f"Sending prompt to LLM for UML feedback ({diagram_type})...")
        feedback_text = f"[Error generating feedback for {diagram_type}]"
        try:
            response = llm.invoke(prompt_text)
            current_feedback = response.content.strip()
            if not current_feedback:
                logger.warning(f"LLM generated empty feedback for UML diagram {diagram_type} in {func_name}.")
                feedback_text = "[AI feedback generation resulted in empty content]"
            else:
                 feedback_text = current_feedback
                 logger.info(f"Generated feedback for {diagram_type}.")
        except Exception as e:
            logger.error(f"Failed to generate feedback for {diagram_type} in {func_name}: {e}", exc_info=True)

        feedback_dict[diagram_type] = feedback_text

    state["uml_feedback"] = feedback_dict
    summary = "\n\n".join([f"**Feedback for {dt}:**\n{fb[:400].strip()}..." for dt, fb in feedback_dict.items()])
    state["messages"].append(AIMessage(content=f"**UML Feedback Provided ({len(feedback_dict)} diagrams):**\n{summary}"))
    logger.info(f"Finished generating feedback for {len(feedback_dict)} current UML diagrams.")
    return state

@with_retry
def refine_uml_codes(state: MainState) -> MainState:
    """Refines UML codes based on AI and human feedback using structured output."""
    func_name = "refine_uml_codes"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    final_design_document = state.get('final_design_document')
    current_codes_objs = state.get('uml_current_codes', [])
    ai_feedback_dict = state.get('uml_feedback', {})
    human_feedback_dict = state.get('uml_human_feedback', {})
    project_name = state.get('project', 'Unnamed Project')

    if not current_codes_objs:
        logger.warning(f"No UML codes found to refine for {func_name}.")
        state["messages"].append(AIMessage(content="Skipped UML refinement: No diagrams found."))
        return state

    final_design_document_sum = final_design_document[:MAX_CONTEXT_LEN + 5000] if final_design_document else "[Design Doc Missing]"
    if final_design_document_sum == "[Design Doc Missing]": logger.warning(f"Design doc missing for {func_name}, refinement quality poor.")

    refined_codes_list: List[PlantUMLCode] = []
    structured_llm = llm.with_structured_output(PlantUMLCode)
    logger.info(f"Refining {len(current_codes_objs)} UML diagrams based on feedback.")

    errors_occurred = False
    for i, plantuml_code_obj in enumerate(current_codes_objs):
        diagram_type = plantuml_code_obj.diagram_type
        current_code = plantuml_code_obj.code
        syntax_info = PLANTUML_SYNTAX_RULES.get(diagram_type, {})
        template = syntax_info.get("template", "N/A")
        notes = syntax_info.get("notes", "N/A")

        ai_feedback = ai_feedback_dict.get(diagram_type, "[No AI Feedback Provided]")
        human_feedback_specific = human_feedback_dict.get(diagram_type, "")
        human_feedback_general = human_feedback_dict.get('all', "")
        combined_human_feedback = f"Specific Human Feedback: {human_feedback_specific}\nGeneral Human Feedback: {human_feedback_general}".strip()
        if combined_human_feedback == "Specific Human Feedback: \nGeneral Human Feedback:": combined_human_feedback = "[No Human Feedback Provided]"

        prompt_text = f"""
**Persona:** PlantUML Expert / System Modeler (Revising Diagram)
**Goal:** Refine PlantUML code for '{diagram_type}' incorporating AI/human feedback, ensuring correctness and design alignment.
**Input Context:**
*   **Final Design Document (Summary):** ```markdown\n{final_design_document_sum}...\n```
*   **Project Name:** {project_name}
*   **Diagram Type:** {diagram_type}
*   **Current PlantUML Code (To Be Revised):** ```plantuml\n{current_code}\n```
*   **AI Feedback on this Code:** ```{ai_feedback}```
*   **Human Feedback (Specific and/or General):** ```{combined_human_feedback}```
*   **PlantUML Syntax Reference (Context):** Template: `{template}` Notes: `{notes}`
**Task:** Revise the 'Current PlantUML Code'. Incorporate actionable feedback from AI/Human inputs. Fix syntax, improve clarity, correct design misalignments, add/refine elements. Ensure code starts `@startuml`, ends `@enduml`.
**Desired Qualities:** Syntactically Correct, Improved Clarity & Accuracy, Better Design Alignment, Incorporation of Feedback.
**Output Format:** Respond ONLY with valid JSON matching 'PlantUMLCode' schema. No ```json block.
**PlantUMLCode Schema:** ```json\n{{ "diagram_type": "{diagram_type}", "code": "@startuml\\n...refined code...\\n@enduml" }}\n``` 'diagram_type' MUST be '{diagram_type}'. 'code' must be refined PlantUML string.
"""
        logger.debug(f"Sending prompt to LLM for refine UML code ({diagram_type})...")
        code_to_add: PlantUMLCode = plantuml_code_obj

        try:
            response: PlantUMLCode = structured_llm.invoke(prompt_text)
            if not response or not response.code: raise ValueError("Missing refined code content.")
            if response.diagram_type != diagram_type: raise ValueError(f"Diagram type mismatch: expected {diagram_type}, got {response.diagram_type}.")
            # Pydantic validates markers
            code_to_add = response
            logger.info(f"Successfully refined and validated PlantUML for {diagram_type}.")
        except (PydanticValidationError, CoreValidationError, ValueError) as e:
             logger.error(f"Validation failed for refined {diagram_type} in {func_name}: {e}. Reverting.", exc_info=False)
             errors_occurred = True
        except Exception as e:
             logger.error(f"Unexpected error refining UML code for {diagram_type} in {func_name}: {e}. Reverting.", exc_info=True)
             errors_occurred = True

        refined_codes_list.append(code_to_add)

    state["uml_current_codes"] = refined_codes_list
    summary = "\n\n".join([f"**{c.diagram_type} (Refined):**\n```plantuml\n{c.code[:300].strip()}...\n```" for c in refined_codes_list])
    state["messages"].append(AIMessage(content=f"**Refined UML Codes ({len(refined_codes_list)}):**\n{summary}"))
    logger.info(f"Finished refining {len(refined_codes_list)} UML diagrams.")
    if errors_occurred: logger.warning(f"One or more UML diagrams reverted due to refinement errors in {func_name}.")
    return state

def save_final_uml_diagrams(state: MainState) -> MainState:
    """Saves final PlantUML (.puml) files and attempts to generate PNG images."""
    func_name = "save_final_uml_diagrams"
    logger.info(f"Executing {func_name}...")
    final_codes = state.get("uml_current_codes", [])
    state["final_uml_codes"] = final_codes

    png_paths: List[str] = []
    uml_dir: Optional[str] = None
    server: Optional[PlantUML] = None
    can_generate_png = False

    try:
        project_folder = state.get("project_folder")
        if not project_folder: raise ValueError("Project folder path is missing in state.")

        uml_dir_path = Path(project_folder).resolve() / "5_uml_diagrams"
        uml_dir_path.mkdir(parents=True, exist_ok=True)
        uml_dir = str(uml_dir_path)
        state["final_uml_diagram_folder"] = uml_dir
        logger.info(f"Preparing to save {len(final_codes)} final UML diagrams to {uml_dir}...")

        plantuml_server_url = os.getenv("PLANTUML_SERVER_URL", "http://www.plantuml.com/plantuml/png/")
        logger.debug(f"Using PlantUML server URL: {plantuml_server_url}")
        try:
            server = PlantUML(url=plantuml_server_url, basic_auth={}, form_auth={}, http_opts={'timeout': 15}, request_opts={})
            test_code = "@startuml\nBob->Alice:test\n@enduml"
            png_data = server.processes(test_code)
            if not png_data or len(png_data) < 100: raise ConnectionError("Test diagram empty/small.")
            logger.info("PlantUML server connection successful.")
            can_generate_png = True
        except Exception as p_e:
            logger.warning(f"PlantUML server issue ({plantuml_server_url}). PNG generation skipped. Error: {p_e}", exc_info=False)
            can_generate_png = False

        if not final_codes:
            logger.warning(f"No final UML codes found to save in {func_name}.")
            state["final_uml_png_paths"] = []
            return state

        for i, pc in enumerate(final_codes, 1):
            safe_type_name = "".join(c if c.isalnum() or c in ['_', '-'] else '_' for c in pc.diagram_type).lower().replace(" ", "_")
            base_name = f"diagram_{i:02d}_{safe_type_name}"
            puml_path = uml_dir_path / f"{base_name}.puml"
            png_path = uml_dir_path / f"{base_name}.png"

            try:
                puml_content_to_write = f"' Diagram Type: {pc.diagram_type}\n\n{pc.code}"
                puml_path.write_text(puml_content_to_write, encoding="utf-8")
                logger.debug(f"Saved PUML file: {puml_path.name}")
            except Exception as file_e:
                logger.error(f"Error saving PUML file {puml_path} in {func_name}: {file_e}", exc_info=True)
                continue

            if can_generate_png and server:
                logger.debug(f"Attempting PNG generation for {base_name}...")
                try:
                    puml_content = puml_path.read_text(encoding="utf-8") # Read saved content
                    png_bytes = server.processes(puml_content)
                    if not png_bytes or len(png_bytes) < 100: raise IOError(f"Generated PNG data empty/small.")
                    png_path.write_bytes(png_bytes)

                    if png_path.exists() and png_path.stat().st_size > 100:
                        logger.info(f"Successfully generated PNG: {png_path.name}")
                        png_paths.append(str(png_path))
                    else:
                        logger.error(f"PlantUML processed '{base_name}' but output PNG invalid: {png_path}.")
                        if png_path.exists():
                            try: png_path.unlink()
                            except Exception as rm_e: logger.warning(f"Could not remove invalid PNG {png_path}: {rm_e}")
                except Exception as png_e:
                    logger.error(f"PNG generation failed for {base_name} ({pc.diagram_type}) in {func_name}. Code invalid? Error: {png_e}", exc_info=False)
            elif not can_generate_png:
                logger.debug(f"Skipping PNG generation for {base_name} (PlantUML server issue).")

        state["final_uml_png_paths"] = png_paths
        logger.info(f"Finished UML saving. Saved {len(final_codes)} PUML. Generated {len(png_paths)} PNG.")

    except Exception as e:
        logger.error(f"General error in {func_name}: {e}", exc_info=True)
        state["final_uml_diagram_folder"] = None
        state["final_uml_png_paths"] = []
    return state


# ------------------------------------------------------------------------------
# --- 6. Code Generation Cycle ---
# (Functions: generate_initial_code, web_search_code, generate_code_feedback, refine_code)
# ------------------------------------------------------------------------------

@with_retry
def generate_initial_code(state: MainState) -> MainState:
    """
    Generates the initial codebase based on all preceding artifacts using structured output (GeneratedCode).

    Args:
        state: Current state, expecting design, stories, prompt, UML summaries.

    Returns:
        Updated state with 'code_current' (GeneratedCode object).
    """
    func_name = "generate_initial_code"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError(f"LLM instance not found in state for {func_name}.")
    if 'messages' not in state: state['messages'] = []

    # --- Context Gathering ---
    final_design_document = state.get('final_design_document')
    if not final_design_document or final_design_document == "[No design document was finalized]":
         raise ValueError(f"Final design document is missing or invalid for {func_name}.")

    refined_prompt_sum = state.get('refined_prompt', '[Missing Refined Prompt]')[:MAX_CONTEXT_LEN // 2]
    final_user_story_sum = state.get('final_user_story', '[Missing Final User Stories]')[:MAX_CONTEXT_LEN // 2]

    final_uml_codes = state.get('final_uml_codes', [])
    uml_summary = "\n".join([f"- {c.diagram_type}" for c in final_uml_codes]) if final_uml_codes else "No UML diagrams provided."

    project_name = state.get('project', 'Unnamed Project')
    coding_language = state.get('coding_language', 'Python')

    # --- Prompt Construction (Updated for Structured Output) ---
    prompt_text = f"""
**Persona:** Senior Software Engineer specializing in {coding_language}

**Goal:** Generate a complete, runnable initial codebase for the '{project_name}' project, adhering to the provided design and requirements.

**Cumulative Project Context:**
*   **Refined Project Prompt (Summary):** ```{refined_prompt_sum}...```
*   **Final User Stories (Summary):** ```{final_user_story_sum}...```
*   **Final Design Document (Primary Input):** ```markdown\n{final_design_document}\n```
*   **Final UML Diagrams Provided (Types):** {uml_summary}

**Task:**
Based *primarily* on the 'Final Design Document' and considering all other context, generate the complete source code for '{project_name}' in {coding_language}. Your output MUST be a JSON object matching the 'GeneratedCode' schema. Include:
1.  **All necessary code files:** Source files (.py, .js, etc.), config files, Dockerfile (if appropriate), etc., following the structure in the Design Doc. Use correct relative paths (e.g., `src/utils/helpers.py`). Include meaningful comments.
2.  **Dependency file:** (e.g., `requirements.txt`, `package.json`) based on the Design Doc's tech stack.
3.  **README.md:** Basic project explanation.
4.  **Setup and Run Instructions:** Clear, step-by-step instructions (env setup, dependency install, run command) accurate for the generated code.

**Desired Qualities:** Runnable Code, Adherence to Design, Completeness, {coding_language} Best Practices, Comments, Accurate Instructions, Correct Relative Paths.

**Output Format:**
Respond ONLY with a single, valid JSON object matching the 'GeneratedCode' schema provided below. Do NOT include ```json markdown blocks or any other text outside the JSON object.

**GeneratedCode Schema:**
```json
{{
  "files": [
    {{ "filename": "README.md", "content": "# Project Title..." }},
    {{ "filename": "requirements.txt", "content": "dependency1==1.0\\ndependency2" }},
    {{ "filename": "src/main.py", "content": "# Main entry point..." }},
    {{ "filename": "src/module/feature.py", "content": "# Feature implementation..." }}
    // ... more CodeFile objects as needed
  ],
  "instructions": "1. Setup Environment: ...\\n2. Install Dependencies: `pip install -r requirements.txt`\\n3. Run: `python src/main.py`"
}}
```
Ensure 'files' is a non-empty list of CodeFile objects (with 'filename' including relative path using '/' and non-empty 'content'). Ensure 'instructions' is a non-empty, accurate string.
"""

    # --- LLM Invocation & Validation ---
    logger.debug(f"Sending prompt to LLM for {func_name} (Design Doc Length: {len(final_design_document)})...")
    # Bind the GeneratedCode schema to the LLM
    structured_llm = llm.with_structured_output(GeneratedCode)
    try:
        response: GeneratedCode = structured_llm.invoke(prompt_text)

        # --- RELAXED VALIDATION ---
        # Pydantic already validated the structure and basic field types/constraints (like min_length=10 for instructions).
        # We will now only log warnings for potentially problematic but structurally valid outputs,
        # instead of raising ValueErrors that halt execution.

        if not response:
             # This case means parsing itself failed or returned None, which is critical.
             logger.error(f"LLM invocation returned None or parsing failed entirely in {func_name}.")
             raise ValueError("LLM response object is null or parsing failed.")

        if not response.files:
            logger.warning(f"LLM response in {func_name} has an empty 'files' list. Proceeding, but code might be missing.")
        # REMOVED: Explicit check for len(response.instructions) < 10, as Pydantic handles min_length
        # REMOVED: Explicit check for invalid file types, as CodeFile model validation handles this now

        # --- END RELAXED VALIDATION ---

        # If validation passes (or warnings logged):
        state["code_current"] = response
        file_count = len(response.files) if response.files else 0
        file_list = ", ".join([f.filename for f in response.files[:5]]) + ('...' if file_count > 5 else '') if response.files else "No files"

        # --- ADDED: Save Snapshot ---
        snapshot_path = _save_code_snapshot(state, "code_generation", "initial")
        if snapshot_path:
            state["snapshot_path_codegen_initial"] = snapshot_path # Store path in state
            logger.info(f"Initial code snapshot saved to: {snapshot_path}")
        else:
            logger.warning("Failed to save initial code snapshot.")
        # --- END ADDED ---
        
        instr_summary = response.instructions[:250] if response.instructions else "[No Instructions]"
        summary = f"Generated {file_count} file{'s' if file_count != 1 else ''} ({file_list}).\nInstructions:\n{instr_summary}..."
        state["messages"].append(AIMessage(content=f"**Initial Code Generated:**\n{summary}"))
        logger.info(f"Generated initial code structure with {file_count} file{'s' if file_count != 1 else ''}.") # Log count even if 0

    # Keep existing error handling for parsing failures
    except (PydanticValidationError, CoreValidationError) as e:
        logger.error(f"Pydantic/Structure validation failed during {func_name}: {e}", exc_info=True)
        raise ValueError(f"LLM structured output validation failed in {func_name}: {e}") from e
    except ValueError as ve: # Catch the specific error raised above if parsing failed entirely
        logger.error(f"Output validation failed during {func_name}: {ve}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during {func_name} invoke: {e}", exc_info=True)
        raise

    return state

# web_search_code remains the same - no changes needed
@with_retry
def web_search_code(state: MainState) -> MainState:
    """Performs web search based on user feedback about code issues using Tavily."""
    func_name = "web_search_code"
    logger.info(f"Executing {func_name}...")
    tavily = state.get('tavily_instance')
    if not tavily:
        logger.warning(f"Tavily client not available, skipping {func_name}.")
        state["code_web_search_results"] = "[Web Search Skipped: Tavily client not configured]"
        state["messages"].append(AIMessage(content="Web Search: Skipped (No Tavily Client)"))
        return state

    if 'messages' not in state: state['messages'] = []
    human_input = state.get('code_human_input', '').strip()

    if not human_input:
        logger.info(f"Skipping {func_name} - no specific human input/issue provided.")
        state["code_web_search_results"] = "[Web Search Skipped: No specific issue provided by user]"
        state["messages"].append(AIMessage(content="Web Search: Skipped (No Issue Provided)"))
        return state

    human_input_summary = human_input[:200]
    coding_language = state.get('coding_language', 'programming')
    search_query = f"how to fix error '{human_input_summary}' in {coding_language}"
    logger.info(f"Performing Tavily web search with query: '{search_query}'")

    results_text = f"[No relevant web search results found for query: '{search_query}']"
    summary = "No relevant web search results found."
    try:
        response = tavily.search(query=search_query, search_depth="basic", max_results=5)
        search_results = response.get("results", [])
        if search_results:
            formatted_results = []
            for i, r in enumerate(search_results, 1):
                 title = r.get('title', 'N/A')
                 url = r.get('url', 'N/A')
                 content_snippet = r.get('content', 'N/A')[:600]
                 score = r.get('score', 'N/A')
                 formatted_results.append(f"**Result {i} (Score: {score}): {title}**\nURL: {url}\nSnippet: {content_snippet}...")
            results_text = "\n\n---\n\n".join(formatted_results)
            log_summary = f"found {len(search_results)} results. Top: '{search_results[0].get('title', 'N/A')}' ({search_results[0].get('score', 'N/A')})"
            logger.info(f"Tavily search successful, {log_summary}")
            summary = f"Found {len(search_results)} results related to the issue."
        else:
            logger.info(f"Tavily search returned no results for the query in {func_name}.")

        state["code_web_search_results"] = results_text
    except Exception as e:
        error_detail = str(e)
        logger.error(f"Tavily search failed in {func_name}: {error_detail}", exc_info=True)
        results_text = f"[Error during web search in {func_name}: {error_detail}]"
        state["code_web_search_results"] = results_text
        summary = f"Error during web search: {error_detail[:100]}..."

    state["messages"].append(AIMessage(content=f"**Web Search Summary:** {summary}\n\n**Full Results:**\n{results_text}"))
    logger.info(f"Completed {func_name} step.")
    return state

# generate_code_feedback remains the same - no changes needed
@with_retry
def generate_code_feedback(state: MainState) -> MainState:
    """Generates AI feedback on current code, considering user input and search results."""
    func_name = "generate_code_feedback"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    code_current_obj = state.get("code_current")
    if not code_current_obj or not isinstance(code_current_obj, GeneratedCode) or not code_current_obj.files:
        logger.warning(f"No valid code found for {func_name}. Skipping feedback.")
        state["code_feedback"] = "[Feedback Skipped: No current code available]"
        state["messages"].append(AIMessage(content="AI Code Feedback: Skipped - No code found."))
        return state

    code_files = code_current_obj.files
    instructions = code_current_obj.instructions
    code_content_str = get_code_context_string(code_files, MAX_CODE_CONTEXT_LEN, func_name)

    human_input = state.get('code_human_input', '[No User Input Provided]')
    search_results = state.get('code_web_search_results', '[No Web Search Results Provided]')
    final_design_document_sum = state.get('final_design_document', '[Missing Design Doc]')[:MAX_CONTEXT_LEN]
    project_name = state.get('project', 'Unnamed Project')
    coding_language = state.get('coding_language', 'Code')

    prompt_text = f"""
**Persona:** Senior {coding_language} Code Reviewer & Debugger
**Goal:** Provide comprehensive feedback on the code, considering user issues, web search, and design intent.
**Input Context:**
*   **Design Doc Summary:** ```{final_design_document_sum}...```
*   **Code Under Review:** ```{code_content_str}```
*   **Setup/Run Instructions:** ```{instructions}```
*   **User Feedback / Issues:** ```{human_input}```
*   **Web Search Results:** ```{search_results}```
**Task:** Review code and instructions. Analyze user feedback and search results. Provide feedback covering: 1. Bug Analysis & Fix Suggestions (based on user feedback), 2. Implementation Gaps & Design Alignment, 3. Code Quality & Best Practices, 4. Instruction Clarity & Accuracy, 5. Search Result Applicability, 6. Overall Suggestions (prioritized, actionable).
**Desired Qualities:** Thorough, Diagnostic, Constructive, Specific Code Refs, Actionable Recommendations.
**Output Format:** Respond with *only* feedback text. Structure logically. No introductions or summaries. Start directly with feedback.
"""
    logger.debug(f"Sending prompt to LLM for code feedback (Code Context Length approx: {len(code_content_str)})...")
    response = llm.invoke(prompt_text)
    feedback_text = response.content.strip()

    if not feedback_text: feedback_text = "[AI Feedback Generation Resulted in Empty Content]"

    state["code_feedback"] = feedback_text
    state["messages"].append(AIMessage(content=f"**AI Code Feedback Provided:**\n\n{feedback_text}"))
    logger.info("Generated AI feedback on the code.")
    return state

@with_retry
def refine_code(state: MainState) -> MainState:
    """
    Refines the code based on user input, web search, AI feedback, and human comments on feedback.
    Uses structured output (GeneratedCode).

    Args:
        state: Current state, expecting 'code_current', feedback/search keys, design summary.

    Returns:
        Updated state with refined 'code_current'.
    """
    func_name = "refine_code"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError(f"LLM instance not found in state for {func_name}.")
    if 'messages' not in state: state['messages'] = []

    # --- Context Gathering ---
    code_current_obj = state.get("code_current")
    # Check if code_current exists AND has files. Allow refinement even if files are empty initially.
    if not code_current_obj or not isinstance(code_current_obj, GeneratedCode):
        raise ValueError("Missing valid current code object (GeneratedCode) for refinement.")

    current_code_files = code_current_obj.files if code_current_obj.files else []
    current_instructions = code_current_obj.instructions if code_current_obj.instructions else "[Previous Instructions Missing]"
    code_content_str = get_code_context_string(current_code_files, MAX_CODE_CONTEXT_LEN, func_name) # Handles empty list

    human_input = state.get('code_human_input', '[No User Input Provided]')
    search_results = state.get('code_web_search_results', '[No Web Search Results Provided]')
    ai_feedback = state.get('code_feedback', '[No AI Feedback Provided]')
    human_feedback_on_ai = state.get('code_human_feedback', '[No Human Comments on AI Feedback Provided]')
    final_design_document_sum = state.get('final_design_document', '[Missing Design Doc]')[:MAX_CONTEXT_LEN]
    project_name = state.get('project', 'Unnamed Project')
    coding_language = state.get('coding_language', 'Code')

    # --- Prompt Construction (Updated for Structured Output) ---
    prompt_text = f"""
**Persona:** Senior {coding_language} Developer implementing fixes and improvements.

**Goal:** Refine the '{project_name}' codebase by addressing user-reported issues, incorporating web search findings, and implementing suggestions from code review feedback. Update instructions if necessary. Output must adhere to the GeneratedCode JSON schema.

**Input Context:**
*   **Design Doc Summary:** ```{final_design_document_sum}...```
*   **Current Code (To Be Refined):** ```{code_content_str}```
*   **Current Instructions:** ```{current_instructions}```
*   **User Feedback / Issues:** ```{human_input}```
*   **Web Search Results:** ```{search_results}```
*   **AI Code Feedback:** ```{ai_feedback}```
*   **Human Comments on AI Feedback:** ```{human_feedback_on_ai}```

**Task:**
Act as the developer. Modify the 'Current Code' based on *all* feedback ('User Feedback', 'Web Search', 'AI Code Feedback', 'Human Comments'). Prioritize fixing user-reported bugs. Apply quality improvements. Use search results if helpful.
1.  **Implement Changes:** Modify code content. Add/remove files if needed. Output *all* necessary project files (including dependencies, README) with correct relative paths (using '/').
2.  **Update Instructions:** If code changes affect setup/run (new deps, commands, env vars), update instructions accordingly. Ensure accuracy.

**Desired Qualities:** Correctness (addresses feedback), Improved Quality, Completeness (all files), Updated & Accurate Instructions, Correct Relative Paths.

**Output Format:**
Respond ONLY with a single, valid JSON object matching the 'GeneratedCode' schema. Do NOT include ```json markdown blocks or any other text.

**GeneratedCode Schema:**
```json
{{
  "files": [
    {{ "filename": "README.md", "content": "# Project Title..." }},
    {{ "filename": "requirements.txt", "content": "dependency1==1.0" }},
    {{ "filename": "src/main.py", "content": "# Refined main..." }}
    // ... CodeFile objects for ALL required files ...
  ],
  "instructions": "1. Setup... 2. Install... `pip install -r requirements.txt` 3. Run..."
}}
```
Ensure 'files' is a list of valid CodeFile objects (can be empty if no files needed). Ensure 'instructions' is a non-empty, accurate string.
"""

    # --- LLM Invocation & Validation ---
    logger.debug(f"Sending prompt to LLM for {func_name} (Code Context Length approx: {len(code_content_str)})...")
    # Bind the GeneratedCode schema
    structured_llm = llm.with_structured_output(GeneratedCode)
    try:
        response: GeneratedCode = structured_llm.invoke(prompt_text)

        # --- RELAXED VALIDATION ---
        if not response:
             logger.error(f"LLM invocation returned None or parsing failed entirely in {func_name}.")
             raise ValueError("LLM response object is null or parsing failed during refinement.")

        if response.files is None: # Check if files list itself is missing
             logger.warning(f"LLM response in {func_name} is missing the 'files' list. Proceeding with empty list.")
             response.files = [] # Default to empty list
        elif not response.files:
             logger.warning(f"LLM response in {func_name} has an empty 'files' list after refinement. Proceeding, but code might be missing.")
        # REMOVED: Explicit check for len(response.instructions) < 10
        # Pydantic model validation covers basic field requirements and CodeFile structure.
        # --- END RELAXED VALIDATION ---

        # If validation passes (or warnings logged):
        state["code_current"] = response
        file_count = len(response.files) if response.files else 0
        file_list = ", ".join([f.filename for f in response.files[:5]]) + ('...' if file_count > 5 else '') if response.files else "No files"

        # --- ADDED: Save Snapshot ---
        snapshot_path = _save_code_snapshot(state, "code_generation", "refined")
        if snapshot_path:
            state["snapshot_path_codegen_refined"] = snapshot_path # Store path to LATEST refined snapshot
            logger.info(f"Refined code snapshot saved to: {snapshot_path}")
        else:
            logger.warning("Failed to save refined code snapshot.")
        # --- END ADDED ---
        
        instr_summary = response.instructions[:250] if response.instructions else "[No Instructions]"
        summary = f"Refined code - {file_count} file{'s' if file_count != 1 else ''} ({file_list}).\nInstructions:\n{instr_summary}..."
        state["messages"].append(AIMessage(content=f"**Code Refined (incorporating feedback):**\n{summary}"))
        logger.info(f"Refined code based on feedback, resulting in {file_count} file{'s' if file_count != 1 else ''}.")

    # Keep existing error handling
    except (PydanticValidationError, CoreValidationError) as e:
        logger.error(f"Pydantic/Structure validation failed during {func_name}: {e}", exc_info=True)
        raise ValueError(f"LLM structured output validation failed in {func_name}: {e}") from e
    except ValueError as ve: # Catch error if parsing failed entirely
        logger.error(f"Output validation failed during {func_name}: {ve}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during {func_name} invoke: {e}", exc_info=True)
        raise

    return state

# ------------------------------------------------------------------------------
# --- 7. Code Review & Security Cycle ---
# (Functions: code_review, security_check, refine_code_with_reviews, save_review_security_outputs)
# ------------------------------------------------------------------------------

# code_review and security_check remain the same - no changes needed
@with_retry
def code_review(state: MainState) -> MainState:
    """Performs code review on the codebase marked ready from the previous cycle."""
    func_name = "code_review"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    code_current_obj = state.get("code_current")
    if not code_current_obj or not isinstance(code_current_obj, GeneratedCode) or not code_current_obj.files:
        logger.warning(f"No valid code found for {func_name}. Skipping review.")
        state["code_review_current_feedback"] = "[Review Skipped: No valid code available]"
        state["messages"].append(AIMessage(content="Code Review: Skipped - No code found."))
        return state

    code_files_to_review = code_current_obj.files
    instructions = code_current_obj.instructions
    code_content_str = get_code_context_string(code_files_to_review, MAX_CODE_CONTEXT_LEN, func_name)

    final_design_document_sum = state.get('final_design_document', '[Missing Design Doc]')[:MAX_CONTEXT_LEN]
    project_name = state.get('project', 'Unnamed Project')
    coding_language = state.get('coding_language', 'Code')

    prompt_text = f"""
**Persona:** Meticulous Senior {coding_language} Code Reviewer
**Goal:** Conduct detailed code review for quality, maintainability, readability, efficiency, best practices. Assume functional correctness unless glaring errors.
**Input Context:**
*   **Design Doc Summary:** ```{final_design_document_sum}...```
*   **Code Under Review:** ```{code_content_str}```
*   **Instructions:** ```{instructions}```
**Task:** Perform thorough review. Evaluate: Readability & Style ({coding_language} conventions), Maintainability & Complexity (structure, comments, DRY), Efficiency (static analysis view), Error Handling, Best Practices & Idioms, Instruction Accuracy (based on code).
**Desired Qualities:** Thorough, Constructive, Specific Examples, Actionable Suggestions, Focus on Non-Functional Quality.
**Output Format:** Respond with *only* code review feedback text. Structure logically. No introductions or summaries. Start directly with feedback.
"""
    logger.debug(f"Sending prompt to LLM for code review (Code Context Length approx: {len(code_content_str)})...")
    response = llm.invoke(prompt_text)
    feedback = response.content.strip()

    if not feedback: feedback = "[AI code review generation resulted in empty content]"

    state["code_review_current_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"**Code Review Findings:**\n\n{feedback}"))
    logger.info("Performed code review.")

    # Store snapshot *before* security check/refinement
    state["final_code_files"] = code_files_to_review
    logger.debug("Stored reviewed code snapshot into 'final_code_files'.")
    return state

@with_retry
def security_check(state: MainState) -> MainState:
    """Performs security analysis on the codebase snapshot taken just after code review."""
    func_name = "security_check"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    code_files_to_check = state.get("final_code_files")
    if not code_files_to_check:
        logger.error(f"Code files missing ('final_code_files') for {func_name}. Skipping.")
        state["security_current_feedback"] = "[Security Check Skipped: Code files missing after review step]"
        state["messages"].append(AIMessage(content="Security Check: Skipped - Code files missing."))
        return state

    instructions = state.get("code_current", GeneratedCode(files=[], instructions="[Instructions Not Found]")).instructions
    code_content_str = get_code_context_string(code_files_to_check, MAX_CODE_CONTEXT_LEN, func_name)

    final_design_document_sum = state.get('final_design_document', '[Missing Design Doc]')[:MAX_CONTEXT_LEN]
    project_name = state.get('project', 'Unnamed Project')
    coding_language = state.get('coding_language', 'Code')

    prompt_text = f"""
**Persona:** Application Security Specialist ({coding_language})
**Goal:** Analyze code for potential security vulnerabilities (OWASP Top 10 etc.) and recommend remediations.
**Input Context:**
*   **Design Doc Summary:** ```{final_design_document_sum}...```
*   **Code Under Security Review:** ```{code_content_str}```
*   **Instructions:** ```{instructions}```
**Task:** Analyze code for vulnerabilities: Injection, Broken Auth, Sensitive Data Exposure, XXE, Broken Access Control, Security Misconfiguration, XSS, Insecure Deserialization, Vulnerable Components (check deps), Insufficient Logging. For each finding: Describe issue, Assess impact, Recommend remediation (specific examples).
**Desired Qualities:** Security Focused, Technically Accurate, Prioritized (High/Medium/Low if possible), Actionable Remediation, References OWASP.
**Output Format:** Respond with *only* security analysis findings/recommendations. Structure clearly. No introductions or summaries. Start directly with findings.
"""
    logger.debug(f"Sending prompt to LLM for security check (Code Context Length approx: {len(code_content_str)})...")
    response = llm.invoke(prompt_text)
    feedback = response.content.strip()

    if not feedback: feedback = "[AI security check generation resulted in empty content]"

    state["security_current_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"**Security Check Findings:**\n\n{feedback}"))
    logger.info("Performed security check.")
    return state

# Modified refine_code_with_reviews
@with_retry
def refine_code_with_reviews(state: MainState) -> MainState:
    """
    Refines code based on code review, security check, and human feedback on those reviews.
    Uses structured output (GeneratedCode).

    Args:
        state: Current state, expecting 'final_code_files' (code before this refinement),
               review/security feedback keys, and potentially 'code_current' (for original instructions).

    Returns:
        Updated state with refined 'final_code_files' and updated 'code_current'.
    """
    func_name = "refine_code_with_reviews"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError(f"LLM instance not found in state for {func_name}.")
    if 'messages' not in state: state['messages'] = []

    # --- Context Gathering ---
    code_files_to_refine = state.get("final_code_files")
    if code_files_to_refine is None: # Check specifically for None, allow empty list
        raise ValueError("Missing code files ('final_code_files') needed for refinement after review/security.")

    # Get instructions associated with the code *before* this refinement
    code_current_obj_before_refinement = state.get("code_current")
    existing_instructions = "[Instructions Placeholder - Verify Accuracy]"
    if code_current_obj_before_refinement and isinstance(code_current_obj_before_refinement, GeneratedCode):
         existing_instructions = code_current_obj_before_refinement.instructions

    code_content_str = get_code_context_string(code_files_to_refine, MAX_CODE_CONTEXT_LEN, func_name) # Handles empty list

    code_review_feedback = state.get('code_review_current_feedback', '[No Code Review Feedback Provided]')
    security_feedback = state.get('security_current_feedback', '[No Security Feedback Provided]')
    human_feedback_on_reviews = state.get('review_security_human_feedback', '[No Human Feedback on Reviews Provided]')
    final_design_document_sum = state.get('final_design_document', '[Missing Design Doc]')[:MAX_CONTEXT_LEN]
    project_name = state.get('project', 'Unnamed Project')
    coding_language = state.get('coding_language', 'Code')

    # --- Prompt Construction (Updated for Structured Output) ---
    prompt_text = f"""
**Persona:** Diligent Senior {coding_language} Developer implementing final review feedback.

**Goal:** Produce the final, production-ready codebase for '{project_name}' by incorporating feedback from code review, security analysis, and user comments. Update instructions if necessary. Output must adhere to the GeneratedCode JSON schema.

**Input Context:**
*   **Design Doc Summary:** ```{final_design_document_sum}...```
*   **Code Under Review (Pre-Refinement Version):** ```{code_content_str}```
*   **Existing Instructions:** ```{existing_instructions}```
*   **Code Review Feedback:** ```{code_review_feedback}```
*   **Security Analysis Feedback:** ```{security_feedback}```
*   **User Feedback on Reviews:** ```{human_feedback_on_reviews}```

**Task:**
Act as developer finalizing code. Analyze all feedback. Modify 'Code Under Review' to address actionable points. Prioritize: 1. Security Fixes (unless user contradicts), 2. Critical Review Points, 3. Other Feedback (quality improvements).
1.  **Implement Changes:** Modify code content. Add/remove files if needed. Output *all* necessary project files (including dependencies, README) with correct relative paths (using '/').
2.  **Update Instructions:** If changes affect setup/run (new deps, commands, env vars), update instructions. Ensure accuracy.

**Desired Qualities:** Security Hardened, High Quality, Maintainable, Correctness (incorporates feedback), Updated/Accurate Final Instructions, Complete File Set.

**Output Format:**
Respond ONLY with a single, valid JSON object matching the 'GeneratedCode' schema. Do NOT include ```json markdown blocks or any other text.

**GeneratedCode Schema:**
```json
{{
  "files": [
    {{ "filename": "README.md", "content": "# Project Title..." }},
    {{ "filename": "requirements.txt", "content": "dependency1==1.1" }}, // Ensure updated if needed
    {{ "filename": "src/main.py", "content": "# Final main..." }}
    // ... CodeFile objects for ALL required final files ...
  ],
  "instructions": "1. Setup... 2. Install... `pip install -r requirements.txt` 3. Configure env vars... 4. Run..."
}}
```
Ensure 'files' is a list of valid CodeFile objects (can be empty if appropriate). Ensure 'instructions' is a non-empty, accurate string for the FINAL code.
"""

    # --- LLM Invocation & Validation ---
    logger.debug(f"Sending prompt to LLM for {func_name} (Code Context Length approx: {len(code_content_str)})...")
    # Bind the GeneratedCode schema
    structured_llm = llm.with_structured_output(GeneratedCode)
    try:
        response: GeneratedCode = structured_llm.invoke(prompt_text)

        # --- RELAXED VALIDATION ---
        if not response:
             logger.error(f"LLM invocation returned None or parsing failed entirely in {func_name}.")
             raise ValueError("LLM response object is null or parsing failed after review refinement.")

        if response.files is None: # Check if files list itself is missing
             logger.warning(f"LLM response in {func_name} is missing the 'files' list after review refinement. Proceeding with empty list.")
             response.files = []
        elif not response.files:
             # This was the specific error source before
             logger.warning(f"LLM response in {func_name} has an empty 'files' list after review refinement. Proceeding, but code might be missing.")
        # REMOVED: Explicit check for len(response.instructions) < 10
        # Pydantic handles basic validation.
        # --- END RELAXED VALIDATION ---

        # If validation passes (or warnings logged):
        # Update BOTH final_code_files AND code_current
        state["final_code_files"] = response.files # Store even if empty list
        state["code_current"] = response # Update current state

        file_count = len(response.files) if response.files else 0
        file_list = ", ".join([f.filename for f in response.files[:5]]) + ('...' if file_count > 5 else '') if response.files else "No files"

        # --- ADDED: Save Snapshot ---
        snapshot_path = _save_code_snapshot(state, "review_security", "post_review_refined")
        if snapshot_path:
            state["snapshot_path_review_refined"] = snapshot_path # Store path
            logger.info(f"Post-review refined code snapshot saved to: {snapshot_path}")
        else:
            logger.warning("Failed to save post-review refined code snapshot.")
        # --- END ADDED ---
        
        instr_summary = response.instructions[:250] if response.instructions else "[No Instructions]"
        summary = f"Refined code ({file_count} file{'s' if file_count != 1 else ''}: {file_list}) incorporating review/security feedback."
        state["messages"].append(AIMessage(content=f"**Code Refined Post-Review/Security:**\n{summary}"))
        logger.info(f"Refined code post-review/security, resulting in {file_count} file{'s' if file_count != 1 else ''}.")

    # Keep existing error handling
    except (PydanticValidationError, CoreValidationError) as e:
        logger.error(f"Pydantic/Structure validation failed during {func_name}: {e}", exc_info=True)
        raise ValueError(f"LLM structured output validation failed in {func_name}: {e}") from e
    except ValueError as ve: # Catch error if parsing failed entirely
        logger.error(f"Output validation failed during {func_name}: {ve}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during {func_name} invoke: {e}", exc_info=True)
        raise

    return state

# save_review_security_outputs remains the same - no changes needed
def save_review_security_outputs(state: MainState) -> MainState:
    """Saves review/security feedback received."""
    # REMOVED saving of code snapshot here, as it's done in refine_code_with_reviews
    logger.info("Executing save_review_security_outputs (saving feedback only)...")
    code_review_feedback_received = state.get("code_review_current_feedback", "[No Code Review Feedback Generated]")
    security_feedback_received = state.get("security_current_feedback", "[No Security Feedback Generated]")
    state["final_code_review"] = code_review_feedback_received
    state["final_security_issues"] = security_feedback_received

    rs_dir: Optional[str] = None
    try:
        project_folder = state.get("project_folder")
        if not project_folder: raise ValueError("Project folder path is missing in state.")
        abs_project_folder = os.path.abspath(project_folder)
        rs_dir = os.path.join(abs_project_folder, "6_review_security") # Folder name kept
        os.makedirs(rs_dir, exist_ok=True)
        state["final_review_security_folder"] = rs_dir

        # Save feedback files
        review_path = os.path.join(rs_dir, "code_review_feedback_received.md")
        security_path = os.path.join(rs_dir, "security_analysis_feedback_received.md")
        with open(review_path, "w", encoding="utf-8") as f: f.write(code_review_feedback_received)
        with open(security_path, "w", encoding="utf-8") as f: f.write(security_feedback_received)
        logger.info(f"Saved review and security feedback reports to {rs_dir}")

        # Retrieve the snapshot path saved by refine_code_with_reviews for potential UI use
        state["review_code_snapshot_folder"] = state.get("snapshot_path_review_refined")

    except (ValueError, OSError, TypeError) as e:
        logger.error(f"General error in save_review_security_outputs: {e}", exc_info=True)
        state["final_review_security_folder"] = None
        state["review_code_snapshot_folder"] = None # Reset this too
    return state
    
# ------------------------------------------------------------------------------
# --- 8. Testing Cycle ---
# (Functions: generate_initial_test_cases, generate_test_cases_feedback, refine_test_cases_and_code, save_testing_outputs)
# ------------------------------------------------------------------------------

# generate_initial_test_cases and generate_test_cases_feedback remain the same
@with_retry
def generate_initial_test_cases(state: MainState) -> MainState:
    """
    Generates initial test cases based on stories, design, and code using structured output (TestCases).

    Args:
        state: Current state, expecting finalized stories, design summary, and code after review/sec.

    Returns:
        Updated state with 'test_cases_current' (List[TestCase]).
    """
    func_name = "generate_initial_test_cases"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError(f"LLM instance not found in state for {func_name}.")
    if 'messages' not in state: state['messages'] = []

    # --- Context Gathering ---
    code_files_for_tests = state.get("final_code_files") # Code after review/sec fixes
    if not code_files_for_tests:
        raise ValueError("Missing reviewed/secured code ('final_code_files') for test case generation.")

    instructions_obj = state.get("code_current")
    instructions = "[Instructions Not Found or Inconsistent State]"
    if instructions_obj and isinstance(instructions_obj, GeneratedCode):
         instructions = instructions_obj.instructions
    else:
         logger.warning(f"Could not find valid instructions in 'code_current' for {func_name}.")

    code_content_str = get_code_context_string(code_files_for_tests, MAX_CODE_CONTEXT_LEN, func_name)

    final_user_story = state.get('final_user_story')
    if not final_user_story or final_user_story == "[No user stories were finalized]":
         raise ValueError(f"Final user stories missing for {func_name}.")

    final_design_document_sum = state.get('final_design_document', '[Missing Design Doc]')[:MAX_CONTEXT_LEN]
    project_name = state.get('project', 'Unnamed Project')
    coding_language = state.get('coding_language', 'Code')

    # --- Prompt Construction (Updated for Structured Output & Stronger Constraints) ---
    prompt_text = f"""
**Persona:** QA Engineer / Tester specializing in {coding_language} applications.

**Goal:** Generate a set of initial, concrete test cases (aim for 3-7) for '{project_name}' covering happy paths, edge cases, and potential errors based primarily on user stories, but also considering the design and code provided.

**Input Context:**
*   **Final User Stories (Primary Input):** ```{final_user_story}```
*   **Design Doc Summary (Context):** ```{final_design_document_sum}...```
*   **Code to Test (Context):** ```{code_content_str}```
*   **Instructions (Context):** ```{instructions}```

**Task:**
Generate a list of test cases. Your output MUST be a JSON object matching the 'TestCases' schema. For each test case:
1.  **description:** A clear, concise description (min 5 chars) explaining the scenario being tested, referencing the relevant user story if possible.
2.  **input_data:** A **native JSON dictionary object**. It MUST be a real dictionary, **NOT a string containing JSON**. Must be non-empty. Example: `{{"key": "value"}}`
3.  **expected_output:** A **native JSON dictionary object**. It MUST be a real dictionary, **NOT a string containing JSON**. Must be non-empty. Example: `{{"result": true}}`
Aim for diverse cases covering different stories and potential failure points identified in the code/design context.

**Desired Qualities:** Good Coverage (happy, edge, error), Concrete NATIVE Dictionary Inputs/Outputs (NO STRINGIFIED JSON), Clarity, Verifiable Outcomes, Alignment with User Stories.

**Output Format:**
Respond ONLY with a single, valid JSON object matching the 'TestCases' schema provided below. Do NOT include ```json markdown blocks or any other text outside the JSON object. **CRITICAL: Ensure `input_data` and `expected_output` fields contain actual JSON dictionary objects, not strings.**

**TestCases Schema:**
```json
{{
  "test_cases": [
    {{
      "description": "Test successful user login with valid credentials.",
      "input_data": {{ "username": "testuser", "password": "Password123" }}, // ACTUAL DICTIONARY
      "expected_output": {{ "status": "success", "token": "some_jwt_token" }} // ACTUAL DICTIONARY
    }},
    {{
      "description": "Test login attempt with invalid password.",
      "input_data": {{ "username": "testuser", "password": "WrongPassword" }}, // ACTUAL DICTIONARY
      "expected_output": {{ "status": "error", "message": "Invalid credentials" }} // ACTUAL DICTIONARY
    }}
    // ... more TestCase objects (min 1 total) ...
  ]
}}
```
Ensure 'test_cases' is a list containing at least one valid TestCase object. Each TestCase must have a non-empty string 'description', and non-empty **native dictionary objects** for 'input_data' and 'expected_output'. **DO NOT output strings like '"{{...}}"' for these fields.**
"""

    # --- LLM Invocation & Validation ---
    logger.debug(f"Sending prompt to LLM for {func_name} (Code Context Length approx: {len(code_content_str)})...")
    # Bind the TestCases schema to the LLM
    structured_llm = llm.with_structured_output(TestCases)
    try:
        response: TestCases = structured_llm.invoke(prompt_text)

        # Pydantic validation done (including the 'before' validator for strings).
        # Add specific checks for non-empty dicts after potential parsing.
        if not response or not response.test_cases:
            raise ValueError(f"LLM response parsed but 'test_cases' list is missing or empty in {func_name}.")

        # Validate that input_data and expected_output are non-empty dictionaries
        for i, tc in enumerate(response.test_cases):
            # Type check is less critical now due to 'before' validator, but non-empty check remains
            if not isinstance(tc.input_data, dict):
                 # This could happen if 'before' validator received non-string, non-dict input
                 logger.error(f"Test case {i} ('{tc.description}') 'input_data' is not dict type after validation.")
                 raise ValueError(f"Test case {i} 'input_data' is not a dictionary (got {type(tc.input_data)}).")
            if not isinstance(tc.expected_output, dict):
                 logger.error(f"Test case {i} ('{tc.description}') 'expected_output' is not dict type after validation.")
                 raise ValueError(f"Test case {i} 'expected_output' is not a dictionary (got {type(tc.expected_output)}).")
            if not tc.input_data:
                 raise ValueError(f"Test case {i} ('{tc.description}') 'input_data' dictionary is empty.")
            if not tc.expected_output:
                 raise ValueError(f"Test case {i} ('{tc.description}') 'expected_output' dictionary is empty.")

        # --- State Update ---
        state["test_cases_current"] = response.test_cases # Store the list of TestCase objects
        test_count = len(response.test_cases)
        summary = "\n".join([f"- {tc.description}" for tc in response.test_cases])
        state["messages"].append(AIMessage(content=f"**Generated Initial Test Cases ({test_count}):**\n{summary}"))
        logger.info(f"Generated {test_count} initial valid test cases.")

    except (PydanticValidationError, CoreValidationError) as e:
        logger.error(f"Pydantic/Structure validation failed during {func_name}: {e}", exc_info=True)
        # Check specifically if it failed because a field expected as a dict was a string
        # (The 'before' validator should now catch this and raise ValueError instead)
        dict_type_errors = [err['loc'] for err in e.errors() if err.get('type') == 'dict_type']
        if dict_type_errors:
            # This might still happen if the 'before' validator fails in an unexpected way
            logger.error(f"Pydantic reported dict_type error despite 'before' validator for fields at {dict_type_errors}")
            raise ValueError(f"LLM output could not be parsed into dictionaries for fields at {dict_type_errors}") from e
        else:
            raise ValueError(f"LLM structured output validation failed in {func_name}: {e}") from e
    except ValueError as ve: # Catch specific validation errors raised by our checks or the 'before' validator
        logger.error(f"Output validation failed during {func_name}: {ve}", exc_info=False)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during {func_name}: {e}", exc_info=True)
        state["test_cases_current"] = [] # Ensure state is cleared on unexpected error
        raise # Re-raise for app.py to handle

    return state

@with_retry
def generate_test_cases_feedback(state: MainState) -> MainState:
    """Generates AI feedback on the current set of test cases."""
    func_name = "generate_test_cases_feedback"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    current_test_cases = state.get("test_cases_current", [])
    if not current_test_cases:
        logger.warning(f"No test cases found for {func_name}. Skipping feedback.")
        state["test_cases_feedback"] = "[Feedback Skipped: No test cases available]"
        state["messages"].append(AIMessage(content="Test Case Feedback: Skipped - No tests found."))
        return state

    try:
        tests_str = "\n\n".join([f"**Test:** {tc.description}\n  Input: `{json.dumps(tc.input_data)}`\n  Expected: `{json.dumps(tc.expected_output)}`" for tc in current_test_cases])[:MAX_CONTEXT_LEN + 5000]
    except Exception as json_e:
        logger.error(f"Error formatting test cases for {func_name} prompt: {json_e}")
        tests_str = "[Error formatting test cases]"

    final_user_story_sum = state.get('final_user_story', '[Missing Stories Context]')[:MAX_CONTEXT_LEN]
    code_files_tested = state.get("final_code_files", [])
    code_summary_str = get_code_context_string(code_files_tested, MAX_CONTEXT_LEN, func_name)
    project_name = state.get('project', 'Unnamed Project')

    prompt_text = f"""
**Persona:** Senior QA Lead / Test Architect
**Goal:** Review test cases for coverage, clarity, effectiveness, realism based on stories/code summaries.
**Input Context:**
*   **User Stories Summary:** ```{final_user_story_sum}...```
*   **Code Tested Summary:** ```{code_summary_str}...```
*   **Test Cases Under Review:** ```{tests_str}```
**Task:** Review tests. Assess: Coverage & Relevance (vs stories/code), Clarity & Specificity (desc, input/output), Effectiveness (catch bugs?), Realism, Data Validity (are data/output dicts?). Suggest improvements (new tests, clearer desc, better data).
**Desired Qualities:** Thorough, Insightful, Constructive, Focus on Quality & Coverage Gaps, Actionable Suggestions.
**Output Format:** Respond with *only* feedback text. Structure clearly. No introductions or summaries. Start directly with feedback.
"""
    logger.debug(f"Sending prompt to LLM for test case feedback (Tests Context Length approx: {len(tests_str)})...")
    response = llm.invoke(prompt_text)
    feedback = response.content.strip()

    if not feedback: feedback = "[AI feedback generation resulted in empty content]"

    state["test_cases_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"**AI Feedback on Test Cases:**\n\n{feedback}"))
    logger.info("Generated feedback on test cases.")
    return state

# Modified refine_test_cases_and_code
@with_retry
def refine_test_cases_and_code(state: MainState) -> MainState:
    """
    Refines both test cases and code based on test feedback and human-reported execution results (failures).
    Uses structured output for the combined refined tests and code.

    Args:
        state: Current state, expecting 'test_cases_current', 'final_code_files',
               feedback keys, and 'code_current' (for original instructions).

    Returns:
        Updated state with refined 'test_cases_current', 'final_code_files', and 'code_current'.
    """
    func_name = "refine_test_cases_and_code"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError(f"LLM instance not found in state for {func_name}.")
    if 'messages' not in state: state['messages'] = []

    # Context Gathering
    current_tests = state.get("test_cases_current")
    current_code_files = state.get("final_code_files") # Code that potentially failed

    if not current_tests: raise ValueError("Missing test cases for refinement.")
    if current_code_files is None: raise ValueError("Missing code files ('final_code_files') for refinement.") # Allow empty list

    code_current_obj_before_refinement = state.get("code_current")
    existing_instructions = "[Instructions Not Found]"
    if code_current_obj_before_refinement and isinstance(code_current_obj_before_refinement, GeneratedCode):
         existing_instructions = code_current_obj_before_refinement.instructions

    code_content_str = get_code_context_string(current_code_files, MAX_CODE_CONTEXT_LEN, func_name) # Handles empty list

    try:
        # Use the TestCase model's dict fields directly
        tests_str_parts = []
        for tc in current_tests:
            input_str = json.dumps(tc.input_data) if isinstance(tc.input_data, dict) else str(tc.input_data)
            output_str = json.dumps(tc.expected_output) if isinstance(tc.expected_output, dict) else str(tc.expected_output)
            tests_str_parts.append(f"**Test:** {tc.description}\n  Input: `{input_str}`\n  Expected: `{output_str}`")
        tests_str = "\n\n".join(tests_str_parts)[:MAX_CONTEXT_LEN + 5000]

    except Exception as json_e:
        logger.error(f"Error formatting test cases for {func_name} prompt: {json_e}")
        tests_str = "[Error formatting test cases]"

    ai_feedback_on_tests = state.get('test_cases_feedback', '[No AI Feedback Provided]')
    human_feedback_test_results = state.get('test_cases_human_feedback', '[No Human Feedback Provided - Assume All Need Review/Fix]')

    final_user_story_sum = state.get('final_user_story', '[Missing Stories Context]')[:MAX_CONTEXT_LEN]
    project_name = state.get('project', 'Unnamed Project')
    coding_language = state.get('coding_language', 'Code')

    # --- Prompt Construction (Updated for Combined Structured Output) ---
    prompt_text = f"""
**Persona:** Senior Developer / QA Engineer collaborating to fix test failures.

**Goal:** Refine *both* test cases and codebase for '{project_name}' to address failed tests ('Human Feedback') and incorporate AI test feedback ('AI Feedback'), ensuring refined code passes refined tests. Output must use the RefinedTestAndCodeOutput JSON schema.

**Input Context:**
*   **User Stories Summary:** ```{final_user_story_sum}...```
*   **Current Test Cases:** ```{tests_str}...```
*   **Current Code (Failed/Needs Improvement):** ```{code_content_str}```
*   **Current Instructions:** ```{existing_instructions}```
*   **AI Feedback on Test Cases:** ```{ai_feedback_on_tests}```
*   **Human Feedback / Test Results (CRUCIAL - failures/errors):** ```{human_feedback_test_results}```

**Task:**
Analyze test failures ('Human Feedback'), AI test feedback, current tests, and code.
Perform integrated actions:
1.  **Refine Test Cases:** Modify 'Current Test Cases' based on AI & human feedback. Correct descriptions, inputs, expected outputs (must be **dictionary objects**). Add/remove tests as needed. Ensure result adheres to `TestCases` schema within the output structure.
2.  **Refine Code:** Modify 'Current Code' files to fix bugs causing failures ('Human Feedback'). Apply relevant improvements from 'AI Feedback'. Ensure `refined_code.files` contains all necessary files with correct relative paths.
3.  **Update Instructions:** If code changes affect setup/run, update `refined_code.instructions`. Ensure accuracy.

**Desired Qualities:** Correct Code (passes refined tests), Robust Test Suite, Accurate Instructions, Incorporates All Feedback/Failures.

**Output Format:**
Respond ONLY with a single, valid JSON object matching 'RefinedTestAndCodeOutput' schema. No ```json block.

**RefinedTestAndCodeOutput Schema:**
```json
{{
  "refined_test_cases": {{ // TestCases object
    "test_cases": [
      {{ "description": "...", "input_data": {{...}}, "expected_output": {{...}} }}, // DICTIONARIES
      // ... more refined TestCases ...
    ]
  }},
  "refined_code": {{ // GeneratedCode object
    "files": [
      {{ "filename": "src/fixed_file.py", "content": "# Fixed code..." }},
      // ... ALL necessary CodeFiles ...
    ],
    "instructions": "Updated instructions..."
  }}
}}
```
Ensure non-empty `refined_test_cases.test_cases` list with valid TestCases (dict input/output). Ensure `refined_code.files` is a list of valid CodeFiles (can be empty). Ensure `refined_code.instructions` is a non-empty string.
"""

    # --- LLM Invocation & Validation ---
    logger.debug(f"Sending prompt to LLM for {func_name} (Code Context Length approx: {len(code_content_str)})...")
    # Bind the combined schema
    structured_llm = llm.with_structured_output(RefinedTestAndCodeOutput)
    try:
        response: RefinedTestAndCodeOutput = structured_llm.invoke(prompt_text)

        # --- Partially Relaxed Validation ---
        # Pydantic validated the overall RefinedTestAndCodeOutput structure.
        if not response: raise ValueError("LLM response object is null.")
        if not response.refined_test_cases or not response.refined_test_cases.test_cases:
             # If tests are missing, that's likely a critical failure
             raise ValueError("Missing 'refined_test_cases' or empty 'test_cases' list.")
        # Validate test case dictionary types explicitly as before
        for i, tc in enumerate(response.refined_test_cases.test_cases):
             # The 'before' validator in TestCase handles string->dict parsing
             if not isinstance(tc.input_data, dict): raise ValueError(f"Refined test {i} input_data not dict.")
             if not isinstance(tc.expected_output, dict): raise ValueError(f"Refined test {i} expected_output not dict.")
             if not tc.input_data: raise ValueError(f"Refined test {i} input_data empty dict.")
             if not tc.expected_output: raise ValueError(f"Refined test {i} expected_output empty dict.")

        # Relax validation for the refined_code part
        if not response.refined_code:
            logger.error(f"LLM response missing 'refined_code' block in {func_name}.")
            # Decide how critical this is. Maybe raise error, or maybe try to proceed with old code?
            # For now, let's raise, as refining code was part of the goal.
            raise ValueError("Missing 'refined_code' block in response.")
        if response.refined_code.files is None:
             logger.warning(f"LLM response in {func_name} is missing the 'refined_code.files' list. Assuming empty list.")
             response.refined_code.files = []
        elif not response.refined_code.files:
            logger.warning(f"LLM response in {func_name} has an empty 'refined_code.files' list. Proceeding, but code refinement may have failed.")
        # REMOVED: Explicit check for len(response.refined_code.instructions) < 10
        # --- END Partially Relaxed Validation ---


        # --- State Update ---
        state["test_cases_current"] = response.refined_test_cases.test_cases # Extract list
        state["final_code_files"] = response.refined_code.files # Update final code (even if empty)
        state["code_current"] = response.refined_code # Update current code state (even if empty)

        file_count = len(response.refined_code.files) if response.refined_code.files else 0
        test_count = len(response.refined_test_cases.test_cases)

        # --- ADDED: Save Snapshot ---
        # Description indicates refinement after testing failure
        snapshot_path = _save_code_snapshot(state, "testing", "post_failure_refined")
        if snapshot_path:
            state["snapshot_path_testing_refined"] = snapshot_path # Store path to LATEST refinement snapshot
            logger.info(f"Post-testing refined code snapshot saved to: {snapshot_path}")
        else:
            logger.warning("Failed to save post-testing refined code snapshot.")
        # --- END ADDED ---
        
        summary = f"Refined {file_count} code file{'s' if file_count != 1 else ''} & {test_count} test case{'s' if test_count != 1 else ''} based on feedback/failures."
        state["messages"].append(AIMessage(content=f"**Refined Tests and Code:**\n{summary}"))
        logger.info(f"Refined {test_count} test cases and {file_count} code files successfully.")

    # Keep existing detailed error handling for test cases dict validation
    except (PydanticValidationError, CoreValidationError) as e:
        logger.error(f"Pydantic/Structure validation failed during {func_name}: {e}", exc_info=True)
        # Check for the specific dict type error in test cases again
        dict_type_errors = [err['loc'] for err in e.errors() if err.get('type') == 'dict_type' and 'refined_test_cases' in err.get('loc',())]
        if dict_type_errors:
            raise ValueError(f"LLM likely returned stringified JSON for test dict fields ({dict_type_errors}) in {func_name}. Schema requires actual dictionaries.") from e
        else:
            # Handle other Pydantic errors if needed
             raise ValueError(f"LLM structured output validation failed in {func_name}: {e}") from e
    except ValueError as ve: # Catch specific validation errors raised above
        logger.error(f"Output validation failed during {func_name}: {ve}", exc_info=False)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during {func_name}: {e}", exc_info=True)
        raise

    return state


# save_testing_outputs remains the same
def save_testing_outputs(state: MainState) -> MainState:
    """Saves the final (potentially refined) tests and the code version that passed them."""
    func_name = "save_testing_outputs"
    logger.info(f"Executing {func_name}...")

    passed_code_files = state.get("final_code_files", [])
    state["final_test_code_files"] = passed_code_files # Store snapshot

    final_tests = state.get("test_cases_current", [])
    test_dir: Optional[str] = None
    code_snap_dir: Optional[str] = None
    tc_path: Optional[str] = None

    try:
        project_folder = state.get("project_folder")
        if not project_folder: raise ValueError("Project folder path is missing in state.")

        test_dir_path = Path(project_folder).resolve() / "7_testing"
        test_dir_path.mkdir(parents=True, exist_ok=True)
        test_dir = str(test_dir_path)
        state["final_testing_folder"] = test_dir

        tc_path_obj = test_dir_path / "final_test_cases.md"
        tc_content_parts = []
        if final_tests:
             tc_content_parts.append(f"# Final Test Cases ({len(final_tests)} Assumed Passed)\n\n")
             for i, tc in enumerate(final_tests, 1):
                 try: input_str, output_str = json.dumps(tc.input_data, indent=2), json.dumps(tc.expected_output, indent=2)
                 except Exception: input_str, output_str = str(tc.input_data), str(tc.expected_output)
                 tc_content_parts.append(f"## Test Case {i}: {tc.description}\n**Input Data:**\n```json\n{input_str}\n```\n**Expected Output:**\n```json\n{output_str}\n```\n---")
        else: tc_content_parts.append("# Final Test Cases\n\n[No test cases were finalized or passed]\n")
        tc_path_obj.write_text("\n".join(tc_content_parts), encoding="utf-8")
        tc_path = str(tc_path_obj)
        logger.info(f"Saved final test cases file: {tc_path_obj.name}")

        code_snap_dir_path = test_dir_path / "code_snapshot_passed_testing"
        code_snap_dir = str(code_snap_dir_path)
        state["testing_passed_code_folder"] = code_snap_dir

        instructions_obj = state.get("code_current")
        passed_instructions = "[Instructions Not Found]"
        if instructions_obj and isinstance(instructions_obj, GeneratedCode): passed_instructions = instructions_obj.instructions
        else: logger.warning(f"Instructions for passed code snapshot not found correctly.")

        if passed_code_files:
            save_successful = save_code_files(passed_code_files, passed_instructions, code_snap_dir, "instructions_passed.md")
            if save_successful: logger.info(f"Saved passed code snapshot to {code_snap_dir}")
            else: logger.error(f"Errors saving passed code snapshot to {code_snap_dir}")
        else:
            logger.warning(f"No passed code files found to save in {func_name}.")
            code_snap_dir_path.mkdir(exist_ok=True)

    except Exception as e:
        logger.error(f"Failed saving testing outputs in {func_name}: {e}", exc_info=True)
        state["final_testing_folder"] = None
        state["testing_passed_code_folder"] = None
    return state


# ------------------------------------------------------------------------------
# --- 9. Quality Analysis Cycle ---
# (Functions: generate_initial_quality_analysis, generate_quality_feedback, refine_quality_and_code, save_final_quality_analysis)
# ------------------------------------------------------------------------------

# generate_initial_quality_analysis and generate_quality_feedback remain the same
@with_retry
def generate_initial_quality_analysis(state: MainState) -> MainState:
    """Generates an overall quality analysis report on the final, tested code."""
    func_name = "generate_initial_quality_analysis"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError(f"LLM instance not found in state for {func_name}.")
    if 'messages' not in state: state['messages'] = []

    code_files_passed = state.get("final_test_code_files")
    if not code_files_passed:
        logger.warning(f"No passed code files found for {func_name}. Skipping analysis.")
        state["quality_current_analysis"] = "[QA Skipped: No tested code available]"
        state["messages"].append(AIMessage(content="Quality Analysis: Skipped - No tested code found."))
        return state

    instructions_obj = state.get("code_current")
    instructions = "[Instructions Not Found]"
    if instructions_obj and isinstance(instructions_obj, GeneratedCode): instructions = instructions_obj.instructions
    code_content_str = get_code_context_string(code_files_passed, MAX_CODE_CONTEXT_LEN, func_name)

    final_design_document_sum = state.get('final_design_document', '[Missing Design Doc]')[:MAX_CONTEXT_LEN]
    final_code_review_sum = state.get('final_code_review', '[Missing Code Review]')[:MAX_CONTEXT_LEN]
    final_security_issues_sum = state.get('final_security_issues', '[Missing Security Report]')[:MAX_CONTEXT_LEN]
    final_tests = state.get("test_cases_current", [])
    tests_summary = f"{len(final_tests)} test cases passed. Examples: " + ", ".join([f"'{tc.description}'" for tc in final_tests[:3]]) + ('...' if len(final_tests) > 3 else '')

    project_name = state.get('project', 'Unnamed Project')
    coding_language = state.get('coding_language', 'Code')

    prompt_text = f"""
**Persona:** Experienced QA Lead / Software Analyst
**Goal:** Generate a comprehensive QA report for '{project_name}', evaluating the final, tested code against quality attributes, considering its history.
**Input Context:**
*   **Design Doc Summary:** ```{final_design_document_sum}...```
*   **Code Review Summary:** ```{final_code_review_sum}...```
*   **Security Report Summary:** ```{final_security_issues_sum}...```
*   **Final Test Cases Summary (Passed):** {tests_summary}
*   **Code Under QA (Passed Tests):** ```{code_content_str}```
*   **Instructions:** ```{instructions}```
**Task:** Analyze code and context. Generate QA report assessing: `## Maintainability`, `## Reliability`, `## Performance Efficiency (Static)`, `## Security Posture`, `## Test Coverage (Inferred)`, `## Documentation Quality`, `## Overall Quality Assessment`, `## Confidence Score (1-10)`. Provide brief assessment (High/Med/Low/NA) and justification for each.
**Desired Qualities:** Balanced Assessment, Justified Ratings, Comprehensive, Clear Rationale, Considers History, Uses Specified Markdown Structure.
**Output Format:** Respond with *only* the QA report text (markdown, `##` headers). No introductions or summaries. Start directly with `## Maintainability`.
"""
    logger.debug(f"Sending prompt to LLM for initial quality analysis (Code Context Length approx: {len(code_content_str)})...")
    response = llm.invoke(prompt_text)
    qa_report = response.content.strip()

    required_headers = ["## Maintainability", "## Reliability", "## Performance", "## Security", "## Test Coverage", "## Documentation", "## Overall", "## Confidence"] # Check keywords
    if not qa_report or len(qa_report) < 200 or not all(header in qa_report for header in required_headers):
        raise ValueError(f"LLM returned empty, minimal, or incorrectly structured content for the initial QA report in {func_name}.")

    state["quality_current_analysis"] = qa_report
    state["messages"].append(AIMessage(content=f"**Initial Quality Analysis Report Generated:**\n\n{qa_report}"))
    logger.info("Generated Initial Quality Analysis Report.")
    return state

@with_retry
def generate_quality_feedback(state: MainState) -> MainState:
    """Generates AI feedback on the Quality Analysis report itself for clarity and consistency."""
    func_name = "generate_quality_feedback"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    current_qa_report = state.get('quality_current_analysis')
    if not current_qa_report or current_qa_report.startswith("[QA Skipped"):
        logger.warning(f"No valid QA report found for {func_name}. Skipping feedback.")
        state["quality_feedback"] = "[Feedback Skipped: No QA report available]"
        state["messages"].append(AIMessage(content="Feedback on QA Report: Skipped - No report found."))
        return state

    project_name = state.get('project', 'Unnamed Project')
    code_files_analyzed = state.get("final_test_code_files", [])
    code_summary_str = get_code_context_string(code_files_analyzed, MAX_CONTEXT_LEN, func_name)

    prompt_text = f"""
**Persona:** Project Manager / Senior Stakeholder reviewing QA assessment.
**Goal:** Review QA report for '{project_name}' for fairness, comprehensiveness, clarity, logical consistency relative to context.
**Input Context (Background Only):**
*   *Code Analyzed Summary:* ```{code_summary_str}...```
**QA Report Under Review (Primary Input):** ```markdown\n{current_qa_report}\n```
**Task:** Review the QA Report *itself*. Evaluate: Fairness & Objectivity, Comprehensiveness & Structure (`## Attribute`), Clarity & Justification, Logical Consistency (assessments vs score), Actionability (implicit). Suggest improvements *to the report*.
**Desired Qualities:** Objective Assessment of Report, Focus on Report Quality, Constructive Suggestions.
**Output Format:** Respond with *only* feedback text on the QA report. Use clear points. No introductions or summaries. Start directly with feedback.
"""
    logger.debug(f"Sending prompt to LLM for QA report feedback (Report Length: {len(current_qa_report)})...")
    response = llm.invoke(prompt_text)
    feedback = response.content.strip()

    if not feedback: feedback = "[AI feedback generation resulted in empty content]"

    state["quality_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"**AI Feedback on QA Report:**\n\n{feedback}"))
    logger.info("Generated feedback on the Quality Analysis report.")
    return state

# Modified refine_quality_and_code
@with_retry
def refine_quality_and_code(state: MainState) -> MainState:
    """
    Refines QA report based on feedback and applies *minor* non-functional code tweaks if suggested.
    Uses structured output for the refined QA report and potentially polished code.

    Args:
        state: Current state, expecting 'quality_current_analysis', feedback keys,
               'final_test_code_files' (code base), and 'code_current' (for instructions).

    Returns:
        Updated state with refined 'quality_current_analysis', 'final_code_files', and 'code_current'.
    """
    func_name = "refine_quality_and_code"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError(f"LLM instance not found in state for {func_name}.")
    if 'messages' not in state: state['messages'] = []

    # Context Gathering
    current_qa_analysis = state.get('quality_current_analysis')
    if not current_qa_analysis or current_qa_analysis.startswith("[QA Skipped"):
        raise ValueError(f"Skipping {func_name} as initial QA analysis is missing or skipped.")

    ai_feedback_on_qa = state.get('quality_feedback', '[No AI Feedback Provided]')
    human_feedback_on_qa = state.get('quality_human_feedback', '[No Human Feedback Provided]')

    code_files_base = state.get("final_test_code_files")
    if code_files_base is None: raise ValueError(f"Tested code files ('final_test_code_files') missing for {func_name}.") # Allow empty list

    code_current_obj_before_refinement = state.get("code_current")
    existing_instructions = "[Instructions Not Found]"
    if code_current_obj_before_refinement and isinstance(code_current_obj_before_refinement, GeneratedCode):
         existing_instructions = code_current_obj_before_refinement.instructions

    code_content_str = get_code_context_string(code_files_base, MAX_CODE_CONTEXT_LEN, func_name) # Handles empty list

    project_name = state.get('project', 'Unnamed Project')
    coding_language = state.get('coding_language', 'Code')

    # --- Prompt Construction (Updated for Combined Structured Output) ---
    prompt_text = f"""
**Persona:** QA Lead finalizing report and suggesting/applying minor code polish.

**Goal:** Refine QA report for '{project_name}' based on feedback. Apply *only minor, non-functional* code improvements (comments, formatting, typos) if clearly suggested and safe. Ensure final instructions accurate. Output must use QualityCodeAndInstructionsOutput JSON schema.

**Input Context:**
*   **Current QA Report:** ```markdown\n{current_qa_analysis}\n```
*   **AI Feedback on QA:** ```{ai_feedback_on_qa}```
*   **Human Feedback on QA:** ```{human_feedback_on_qa}```
*   **Code Analyzed (Base for Polish):** ```{code_content_str}```
*   **Instructions for Base Code:** ```{existing_instructions}```

**Task:**
1.  **Refine QA Report:** Revise 'Current QA Report' based on all feedback. Improve clarity, logic, justifications, structure. Output as `refined_analysis` markdown string (non-empty, with QA sections).
2.  **Identify MINOR Code Polish ONLY:** Review QA/feedback *strictly* for suggestions of minor, non-functional code tweaks (comments, formatting, typos). NO logic changes.
3.  **Apply Minor Polish (If Applicable):** If identified, apply ONLY safe, non-functional changes to 'Code Analyzed'. If none, return original code. Store result in `refined_code.files` (must be list of valid CodeFiles, can be empty).
4.  **Confirm/Update Instructions:** Ensure `refined_code.instructions` are accurate for final code (likely unchanged). Ensure non-empty string.

**Desired Qualities:** Polished QA Report, Accurate Final Instructions, Code with only minor non-functional tweaks (if any).

**Output Format:**
Respond ONLY with a single, valid JSON object matching 'QualityCodeAndInstructionsOutput' schema. No ```json block.

**QualityCodeAndInstructionsOutput Schema:**
```json
{{
  "refined_analysis": "## Maintainability\\nHigh...", // Refined markdown report
  "refined_code": {{ // GeneratedCode object
    "files": [
        {{ "filename": "src/main.py", "content": "# Code with maybe a fixed comment..." }},
        // ALL files included, potentially polished
      ],
    "instructions": "1. Setup..." // Final accurate instructions
  }}
}}
```
Ensure valid, non-empty `refined_analysis`. Ensure `refined_code.files` is a list of CodeFiles (can be empty). Ensure `refined_code.instructions` is non-empty string.
"""

    # --- LLM Invocation & Validation ---
    logger.debug(f"Sending prompt to LLM for {func_name} (Code Context Length approx: {len(code_content_str)})...")
    # Bind the combined schema
    structured_llm = llm.with_structured_output(QualityCodeAndInstructionsOutput)
    try:
        response: QualityCodeAndInstructionsOutput = structured_llm.invoke(prompt_text)

        # --- Partially Relaxed Validation ---
        # Pydantic validated the overall QualityCodeAndInstructionsOutput structure.
        if not response: raise ValueError("LLM response object is null.")
        # Keep validation for the QA report part
        if not response.refined_analysis or len(response.refined_analysis) < 50:
            logger.warning(f"Refined analysis seems short or missing in {func_name}.")
            # Don't raise error, allow proceeding with potentially short report

        # Relax validation for the refined_code part, handle missing block
        if not response.refined_code:
            logger.warning(f"Missing 'refined_code' block in {func_name}. Assuming no code changes were made.")
            # Create a default object based on the input code to proceed.
            response.refined_code = GeneratedCode(files=code_files_base, instructions=existing_instructions)

        if response.refined_code.files is None:
            logger.warning(f"LLM response in {func_name} is missing the 'refined_code.files' list. Assuming empty list.")
            response.refined_code.files = []
        elif not response.refined_code.files:
            logger.warning(f"LLM response in {func_name} has an empty 'refined_code.files' list after QA polish. Proceeding.")
        # REMOVED: Explicit check for len(response.refined_code.instructions) < 10
        # --- END Partially Relaxed Validation ---

        # Log if code changed (using potentially default object from above)
        original_content_map = {f.filename: f.content for f in code_files_base}
        refined_content_map = {f.filename: f.content for f in response.refined_code.files}
        code_changed = False
        if len(original_content_map) != len(refined_content_map) or set(original_content_map.keys()) != set(refined_content_map.keys()): code_changed = True
        else: code_changed = any(original_content_map[fname] != content for fname, content in refined_content_map.items())
        log_msg = "Code changed (minor polish)" if code_changed else "No code changes applied"
        logger.info(f"{log_msg} during QA refinement in {func_name}.")

        # --- State Update ---
        state["quality_current_analysis"] = response.refined_analysis if response.refined_analysis else "[QA Report Refinement Failed]"
        state["final_code_files"] = response.refined_code.files # Absolute final code (even if empty)
        state["code_current"] = response.refined_code # Update current state (even if empty)

        # --- ADDED: Save Snapshot ---
        # Description indicates polish after QA analysis
        snapshot_path = _save_code_snapshot(state, "quality_analysis", "post_qa_polished")
        if snapshot_path:
            state["snapshot_path_qa_polished"] = snapshot_path # Store path
            logger.info(f"Post-QA polished code snapshot saved to: {snapshot_path}")
        else:
            logger.warning("Failed to save post-QA polished code snapshot.")
        # --- END ADDED ---
        
        state["messages"].append(AIMessage(content=f"**Refined Quality Analysis Report:**\n{state['quality_current_analysis']}"))
        logger.info(f"Refined Quality Analysis report. Code {'changed' if code_changed else 'did not change'}.")

    # Keep existing error handling
    except (PydanticValidationError, CoreValidationError) as e:
        logger.error(f"Pydantic/Structure validation failed during {func_name}: {e}", exc_info=True)
        raise ValueError(f"LLM structured output validation failed in {func_name}: {e}") from e
    except ValueError as ve: # Catch validation errors raised above
        logger.error(f"Output validation failed during {func_name}: {ve}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during {func_name}: {e}", exc_info=True)
        raise

    return state

# save_final_quality_analysis remains the same
def save_final_quality_analysis(state: MainState) -> MainState:
    """Saves the final QA report (MD and PDF). Code snapshot is saved by refine_quality_and_code."""
    logger.info("Executing save_final_quality_analysis (saving QA report only)...")
    final_qa_report = state.get("quality_current_analysis", "[No QA Report Generated or Finalized]")
    state["final_quality_analysis"] = final_qa_report

    qa_dir: Optional[str] = None
    qa_md_path: Optional[str] = None
    qa_pdf_path: Optional[str] = None

    try:
        project_folder = state.get("project_folder")
        if not project_folder: raise ValueError("Project folder path is missing in state.")

        abs_project_folder = os.path.abspath(project_folder)
        qa_dir = os.path.join(abs_project_folder, "8_quality_analysis") # Keep folder name
        os.makedirs(qa_dir, exist_ok=True)

        # Save the QA report file (MD)
        qa_md_path = os.path.join(qa_dir, "final_quality_analysis_report.md")
        md_content_with_header = f"# Final Quality Analysis Report\n\n{final_qa_report}"
        with open(qa_md_path, "w", encoding="utf-8") as f:
            f.write(md_content_with_header)
        logger.info(f"Saved final QA report markdown: {os.path.basename(qa_md_path)}")

        # Generate and Save PDF
        qa_pdf_path = os.path.join(qa_dir, "final_quality_analysis_report.pdf")
        if convert_md_to_pdf(md_content_with_header, qa_pdf_path):
             logger.info(f"Saved final QA report PDF: {os.path.basename(qa_pdf_path)}")
        else:
             logger.warning("Failed to generate PDF for final QA report.")
             qa_pdf_path = None

        # Set final_code_folder path to the snapshot saved by refine_quality_and_code
        state["final_code_folder"] = state.get("snapshot_path_qa_polished")
        logger.info(f"Final code folder path set to QA polished snapshot: {state['final_code_folder']}")

    except (ValueError, OSError, TypeError) as e:
        logger.error(f"Failed saving final QA outputs: {e}", exc_info=True)
        qa_md_path = None
        qa_pdf_path = None
        state["final_code_folder"] = None # Reset code folder path too

    state["final_quality_analysis_path"] = qa_md_path
    state["final_quality_analysis_pdf_path"] = qa_pdf_path
    return state
    
# ------------------------------------------------------------------------------
# --- 10. Deployment Cycle ---
# (Functions: generate_initial_deployment, generate_deployment_feedback, refine_deployment, save_final_deployment_plan - no changes needed)
# ------------------------------------------------------------------------------

@with_retry
def generate_initial_deployment(state: MainState, prefs: str) -> MainState:
    """Generates initial deployment plan based on final code and user preferences."""
    func_name = "generate_initial_deployment"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    final_code_files = state.get("final_code_files")
    if not final_code_files: raise ValueError("Cannot generate deployment plan without final code artifacts.")

    final_instructions_obj = state.get("code_current")
    final_instructions = "[Final Instructions Missing]"
    if final_instructions_obj and isinstance(final_instructions_obj, GeneratedCode): final_instructions = final_instructions_obj.instructions
    code_context_str = get_code_context_string(final_code_files, MAX_CODE_CONTEXT_LEN, func_name)

    final_design_document_sum = state.get('final_design_document', '[Missing Design Doc]')[:MAX_CONTEXT_LEN]
    final_quality_analysis_sum = state.get('final_quality_analysis', '[Missing QA Report]')[:MAX_CONTEXT_LEN]

    project_name = state.get('project', 'Unnamed Project')
    coding_language = state.get('coding_language', 'Code')
    user_prefs = prefs.strip() if prefs and prefs.strip() else "Standard cloud deployment (e.g., AWS, GCP, Azure), containerized."
    logger.info(f"Using deployment preferences for {func_name}: {user_prefs}")

    prompt_text = f"""
**Persona:** DevOps Engineer / Cloud Specialist
**Goal:** Generate detailed, step-by-step initial deployment plan for '{project_name}' ({coding_language}) based on final code, context, and user preferences.
**Input Context:**
*   **Design Doc Summary:** ```{final_design_document_sum}...```
*   **QA Report Summary:** ```{final_quality_analysis_sum}...```
*   **User Deployment Preferences:** ```{user_prefs}```
*   **Final Code Summary:** ```{code_context_str}```
*   **Final Instructions:** ```{final_instructions}```
**Task:** Create deployment plan based *specifically* on 'User Preferences' and code context. Include: `## 1. Target Environment Summary`, `## 2. Prerequisites` (tools, accounts, perms), `## 3. Build Process` (commands), `## 4. Infrastructure Setup` (commands for target platform), `## 5. Deployment Steps` (commands, config, secrets), `## 6. Verification` (steps), `## 7. Rollback Strategy (Brief)`.
**Desired Qualities:** Actionable, Specific Steps/Commands, Tool-Specific, Complete Lifecycle, Clear, Security Aware, Practical.
**Output Format:** Respond with *only* deployment plan text (markdown, `##` headers 1-7). Ensure all sections present. No introductions/summaries. Start with `## 1. Target Environment Summary`.
"""
    logger.debug(f"Sending prompt to LLM for initial deployment plan (Code Context Length approx: {len(code_context_str)})...")
    response = llm.invoke(prompt_text)
    deployment_plan = response.content.strip()

    required_headers = [f"## {i+1}." for i in range(7)]
    if not deployment_plan or len(deployment_plan) < 200 or not all(header in deployment_plan for header in required_headers):
        raise ValueError(f"LLM returned empty, minimal, or incorrectly structured content for the initial deployment plan in {func_name}.")

    state["deployment_current_process"] = deployment_plan
    state["messages"].append(AIMessage(content=f"**Initial Deployment Plan Generated:**\n\n{deployment_plan}"))
    logger.info("Generated initial deployment plan.")
    return state

@with_retry
def generate_deployment_feedback(state: MainState) -> MainState:
    """Generates AI feedback on the deployment plan's clarity, correctness, and best practices."""
    func_name = "generate_deployment_feedback"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    current_plan = state.get('deployment_current_process')
    if not current_plan:
        logger.warning(f"No deployment plan found for {func_name}. Skipping feedback.")
        state["deployment_feedback"] = "[Feedback Skipped: No deployment plan to review]"
        state["messages"].append(AIMessage(content="Deployment Plan Feedback: Skipped - No plan found."))
        return state

    final_code_files = state.get("final_code_files", [])
    code_summary_str = get_code_context_string(final_code_files, MAX_CODE_CONTEXT_LEN, func_name)
    final_design_document_sum = state.get('final_design_document', '[Missing Design Doc]')[:MAX_CONTEXT_LEN]
    project_name = state.get('project', 'Unnamed Project')

    prompt_text = f"""
**Persona:** Senior DevOps Engineer / Cloud Architect Reviewer
**Goal:** Review deployment plan for '{project_name}' for clarity, correctness, completeness, security, efficiency, best practices, considering context.
**Input Context (Background Only):**
*   *Design Doc Summary:* ```{final_design_document_sum}...```
*   *Final Code Summary:* ```{code_summary_str}...```
**Deployment Plan Under Review (Primary Input):** ```markdown\n{current_plan}\n```
**Task:** Review the plan. Provide feedback on: Clarity & Completeness (steps, details), Correctness & Feasibility (commands, procedures), Best Practices & Efficiency (DevOps, IaC, automation, secrets), Security (gaps, secure defaults), Verification & Rollback (robustness, clarity), Alignment (vs design/code). Suggest specific improvements.
**Desired Qualities:** Technical Depth, Security/DevOps Aware, Practical, Constructive, Actionable Suggestions.
**Output Format:** Respond with *only* feedback text. Structure clearly. No introductions or summaries. Start directly with feedback.
"""
    logger.debug(f"Sending prompt to LLM for deployment plan feedback (Plan Length: {len(current_plan)})...")
    response = llm.invoke(prompt_text)
    feedback = response.content.strip()

    if not feedback: feedback = "[AI feedback generation resulted in empty content]"

    state["deployment_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"**AI Feedback on Deployment Plan:**\n\n{feedback}"))
    logger.info("Generated feedback on deployment plan.")
    return state

@with_retry
def refine_deployment(state: MainState) -> MainState:
    """Refines deployment plan based on AI and human feedback."""
    func_name = "refine_deployment"
    logger.info(f"Executing {func_name}...")
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []

    current_plan = state.get('deployment_current_process')
    if not current_plan: raise ValueError("Missing current deployment plan for refinement.")

    ai_feedback = state.get('deployment_feedback', '[No AI Feedback Provided]')
    human_feedback = state.get('deployment_human_feedback', '[No Human Feedback Provided]')

    final_code_files = state.get("final_code_files", [])
    code_context_str = get_code_context_string(final_code_files, MAX_CODE_CONTEXT_LEN, func_name)
    final_instructions_obj = state.get("code_current")
    final_instructions = "[Final Instructions Missing]"
    if final_instructions_obj and isinstance(final_instructions_obj, GeneratedCode): final_instructions = final_instructions_obj.instructions

    final_design_document_sum = state.get('final_design_document', '[Missing Design Doc]')[:MAX_CONTEXT_LEN]
    project_name = state.get('project', 'Unnamed Project')

    prompt_text = f"""
**Persona:** DevOps Engineer / Cloud Specialist (Revising Plan)
**Goal:** Refine deployment plan for '{project_name}' incorporating AI/human feedback for a clearer, robust, secure, actionable procedure.
**Input Context:**
*   **Design Doc Summary:** ```{final_design_document_sum}...```
*   **Final Code Summary:** ```{code_context_str}```
*   **Final Instructions:** ```{final_instructions}```
*   **Current Deployment Plan (To Be Revised):** ```markdown\n{current_plan}\n```
*   **AI Feedback on Plan:** ```{ai_feedback}```
*   **Human Feedback on Plan:** ```{human_feedback}```
**Task:** Revise 'Current Deployment Plan'. Incorporate actionable feedback. Clarify steps/commands, correct errors, add missing details, improve security (secrets), enhance verification/rollback. Ensure consistency with code/design. Maintain 7-section structure (`## 1. ...`). Output complete refined plan.
**Desired Qualities:** Clearer, More Correct, More Complete, More Secure, Actionable, Incorporates Feedback, Consistent Structure.
**Output Format:** Respond with *only* complete, refined deployment plan (markdown, `##` headers 1-7). No introductions or summaries. Start with `## 1. Target Environment Summary`.
"""
    logger.debug(f"Sending prompt to LLM for deployment plan refinement...")
    response = llm.invoke(prompt_text)
    refined_plan = response.content.strip()

    required_headers = [f"## {i+1}." for i in range(7)]
    if not refined_plan or len(refined_plan) < 200 or not all(header in refined_plan for header in required_headers):
        raise ValueError(f"LLM returned empty, minimal, or incorrectly structured content when refining deployment plan in {func_name}.")

    state["deployment_current_process"] = refined_plan
    state["messages"].append(AIMessage(content=f"**Refined Deployment Plan:**\n\n{refined_plan}"))
    logger.info("Refined deployment plan based on feedback.")
    return state

def save_final_deployment_plan(state: MainState) -> MainState:
    """Saves the final deployment plan to MD and PDF files."""
    logger.info("Executing save_final_deployment_plan...")
    final_plan = state.get("deployment_current_process", "[No deployment plan was finalized]")
    state["final_deployment_process"] = final_plan
    md_path: Optional[str] = None
    pdf_path: Optional[str] = None
    try:
        project_folder = state.get("project_folder")
        if not project_folder: raise ValueError("Project folder path is missing in state.")

        abs_project_folder = os.path.abspath(project_folder)
        deploy_dir = os.path.join(abs_project_folder, "9_deployment")
        os.makedirs(deploy_dir, exist_ok=True)

        # Save MD
        md_path = os.path.join(deploy_dir, "final_deployment_plan.md")
        md_content_with_header = f"# Final Deployment Plan\n\n{final_plan}"
        with open(md_path, "w", encoding="utf-8") as f:
             f.write(md_content_with_header)
        logger.info(f"Saved final deployment plan markdown: {os.path.basename(md_path)}")

        # --- ADDED: Generate and Save PDF ---
        pdf_path = os.path.join(deploy_dir, "final_deployment_plan.pdf")
        if convert_md_to_pdf(md_content_with_header, pdf_path):
            logger.info(f"Saved final deployment plan PDF: {os.path.basename(pdf_path)}")
        else:
            logger.warning("Failed to generate PDF for final deployment plan.")
            pdf_path = None
        # --- END ADDED ---

    except (ValueError, OSError, TypeError) as e:
        logger.error(f"Failed to save final deployment plan artifacts: {e}", exc_info=True)
        md_path = None
        pdf_path = None

    state["final_deployment_path"] = md_path # Store MD Path (maybe rename key later if needed)
    state["final_deployment_pdf_path"] = pdf_path # Store PDF path
    return state

# ==============================================================================
# --- End of Workflow Functions ---
# ==============================================================================