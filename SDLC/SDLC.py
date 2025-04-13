# SDLC.py
import os
import sys
import shutil
from typing import List, Union, Dict, Annotated, Any
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain.schema import AIMessage, HumanMessage
from langchain_core.language_models.base import BaseLanguageModel # Correct import path
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
# Add imports for other potential providers if needed
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from tavily import TavilyClient
from dotenv import load_dotenv
import operator
import logging
import ast
import time
from plantuml import PlantUML
from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential, wait_fixed, retry_if_exception_type
import nest_asyncio 

# --- Basic logging setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Load Environment Variables ---
# Keep load_dotenv() in case some functions still rely on other env vars,
# but LLM/Tavily keys will now come from function args.
load_dotenv()

# --- REMOVED LLM / Tavily Initialization Block ---
# GLOBAL_LLM, OPENAI_LLM, tavily_client will be initialized dynamically

# --- Pydantic Models ---
# (Keep all Pydantic models as they were)
class DiagramSelection(BaseModel):
    diagram_types: List[str] = Field(..., description="List of 5 selected UML/DFD diagram types")
    justifications: List[str] = Field(..., description="Brief justifications for each diagram type")
class PlantUMLCode(BaseModel):
    diagram_type: str = Field(..., description="Type of UML/DFD diagram")
    code: str = Field(..., description="PlantUML code for the diagram")
class CodeFile(BaseModel):
    filename: str = Field(..., description="Name of the file, including path relative to project root")
    content: str = Field(..., description="Full content of the file")
class GeneratedCode(BaseModel):
    files: List[CodeFile] = Field(..., description="List of all files in the project")
    instructions: str = Field(..., description="Beginner-friendly setup and run instructions")
class TestCase(BaseModel):
    description: str = Field(..., description="Description of the test case")
    input_data: dict = Field(..., description="Fake input data, must be non-empty")
    expected_output: dict = Field(..., description="Expected fake output, must be non-empty")
class TestCases(BaseModel):
    test_cases: List[TestCase] = Field(..., description="List of test cases")

# --- Main State Definition ---
class MainState(TypedDict, total=False):
    # --- ADDED instance storage ---
    llm_instance: BaseLanguageModel | None # Store the initialized LLM
    tavily_instance: TavilyClient | None # Store the initialized Tavily client
    # --- END ADDED ---

    # Core conversation history
    messages: Annotated[List[Union[HumanMessage, AIMessage]], lambda x, y: (x or []) + (y or [])]

    # Project definition
    project_folder: str # Base name/relative path used for saving files
    project: str
    category: str
    subcategory: str
    coding_language: str

    # User Input Cycle State
    user_input_questions: List[str]
    user_input_answers: List[str]
    user_input_iteration: int
    user_input_min_iterations: int
    user_input_done: bool

    # Core Artifacts
    user_query_with_qa: str
    refined_prompt: str
    final_user_story: str
    final_product_review: str
    final_design_document: str
    final_uml_codes: List[PlantUMLCode]
    final_code_files: List[CodeFile]
    final_code_review: str
    final_security_issues: str
    final_test_code_files: List[CodeFile]
    final_quality_analysis: str
    final_deployment_process: str

    # File Paths
    final_user_story_path: str
    final_product_review_path: str
    final_design_document_path: str
    final_uml_diagram_folder: str
    final_uml_png_paths: List[str]
    final_review_security_folder: str
    review_code_snapshot_folder: str
    final_testing_folder: str
    testing_passed_code_folder: str
    final_quality_analysis_path: str
    final_code_folder: str
    final_deployment_path: str

    # Intermediate States
    user_story_current: str; user_story_feedback: str; user_story_human_feedback: str; user_story_done: bool;
    product_review_current: str; product_review_feedback: str; product_review_human_feedback: str; product_review_done: bool;
    design_doc_current: str; design_doc_feedback: str; design_doc_human_feedback: str; design_doc_done: bool;
    uml_selected_diagrams: List[str]; uml_current_codes: List[PlantUMLCode]; uml_feedback: Dict[str, str]; uml_human_feedback: Dict[str, str]; uml_done: bool;
    code_current: GeneratedCode;
    code_human_input: str; code_web_search_results: str; code_feedback: str; code_human_feedback: str; code_done: bool;
    code_review_current_feedback: str; security_current_feedback: str; review_security_human_feedback: str; review_security_done: bool;
    test_cases_current: List[TestCase]; test_cases_feedback: str; test_cases_human_feedback: str; test_cases_passed: bool;
    quality_current_analysis: str; quality_feedback: str; quality_human_feedback: str; quality_done: bool;
    deployment_current_process: str; deployment_feedback: str; deployment_human_feedback: str; deployment_done: bool;


# --- Constants and Helper Functions ---
PLANTUML_SYNTAX_RULES = { # Keep the full dictionary
    # ... (plantuml rules dictionary remains unchanged) ...
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
    "Level 2 DFD": {"template": "@startuml\nrectangle P1.1\nrectangle P1.2\ndatabase DS\nP1.1 --> P1.2 : Internal Data\nP1.2 --> DS : Store Detail\n@enduml", "required_keywords": ["rectangle", "-->", ":"], "notes": "Decomposition of Level 1 processes."},
    "Level 3 DFD": {"template": "@startuml\nrectangle P1.1.1\nrectangle P1.1.2\nP1.1.1 --> P1.1.2 : Sub-detail\n@enduml", "required_keywords": ["rectangle", "-->", ":"], "notes": "Further decomposition."},
    "General DFD": {"template": "@startuml\nentity E\nrectangle P\ndatabase DS\nE --> P : Input\nP --> DS : Store\nDS --> P : Retrieve\nP --> E : Output\n@enduml", "required_keywords": ["entity", "rectangle", "database", "-->", ":"], "notes": "Generic structure for DFDs."},
}

def validate_plantuml_code(diagram_type: str, code: str) -> bool:
    # (validate_plantuml_code function remains unchanged)
    if diagram_type not in PLANTUML_SYNTAX_RULES:
        logger.warning(f"Unknown diagram type for validation: {diagram_type}")
        return False
    rules = PLANTUML_SYNTAX_RULES[diagram_type]
    required_keywords = rules.get("required_keywords", [])
    if not code:
        logger.warning(f"Empty code provided for {diagram_type}.")
        return False
    code_cleaned = code.strip()
    if not code_cleaned.startswith("@startuml"):
        logger.warning(f"PlantUML code for {diagram_type} does not start with @startuml.")
    if not code_cleaned.endswith("@enduml"):
         logger.warning(f"PlantUML code for {diagram_type} does not end with @enduml.")
    if required_keywords:
        missing_keywords = [kw for kw in required_keywords if kw not in code]
        if missing_keywords:
            logger.warning(f"PlantUML code for {diagram_type} missing required keywords: {missing_keywords}.")
    return True

# --- UPDATED: Initialization Function ---
def initialize_llm_clients(provider: str, model_name: str, llm_api_key: str, tavily_api_key: str) -> tuple[BaseLanguageModel | None, TavilyClient | None, str | None]:
    """
    Initializes LLM and Tavily clients based on user-provided configuration.
    Applies nest_asyncio patch for compatibility with Streamlit threads.
    """
    # --- ADDED: Apply nest_asyncio ---
    nest_asyncio.apply()
    # --- END ADDED ---

    llm_instance = None
    tavily_instance = None
    error_message = None
    provider_lower = provider.lower()

    # --- Initialize LLM ---
    try:
        logger.info(f"Attempting to initialize LLM: Provider='{provider}', Model='{model_name}'")
        if not llm_api_key:
            raise ValueError("LLM API Key is required.")

        if provider_lower == "openai":
            llm_instance = ChatOpenAI(model=model_name, temperature=0.5, api_key=llm_api_key)
        elif provider_lower == "groq":
            llm_instance = ChatGroq(model=model_name, temperature=0.5, api_key=llm_api_key)
        elif provider_lower == "google":
            # This initialization should now work after nest_asyncio.apply()
            llm_instance = ChatGoogleGenerativeAI(model=model_name, google_api_key=llm_api_key, temperature=0.5)
        elif provider_lower == "anthropic":
            llm_instance = ChatAnthropic(model=model_name, anthropic_api_key=llm_api_key, temperature=0.5)
        elif provider_lower == "xai":
            xai_base_url = "https://api.x.ai/v1"
            logger.info(f"Using xAI endpoint: {xai_base_url}")
            llm_instance = ChatOpenAI(model=model_name, temperature=0.5, api_key=llm_api_key, base_url=xai_base_url)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        # Optional: Test call
        # ...

        logger.info(f"LLM {provider} - {model_name} initialized successfully.")

    except ValueError as ve:
        error_message = str(ve); logger.error(f"LLM Init Error: {error_message}"); llm_instance = None
    except ImportError:
         error_message = f"Missing library for {provider}. Install required package."; logger.error(error_message); llm_instance = None
    except Exception as e:
        # Check if it's the event loop error specifically, although nest_asyncio should fix it
        if "no current event loop" in str(e):
             error_message = f"Asyncio event loop issue persists even with nest_asyncio for {provider}: {e}"
        else:
             error_message = f"Unexpected error initializing LLM for {provider}: {e}"
        logger.error(error_message, exc_info=True); llm_instance = None

    # --- Initialize Tavily (No change) ---
    # (Tavily part remains the same)
    if tavily_api_key:
        try:
            logger.info("Initializing Tavily client..."); tavily_instance = TavilyClient(api_key=tavily_api_key); logger.info("Tavily client initialized.")
        except Exception as e:
            tavily_err = f"Failed to initialize Tavily: {e}"; logger.error(tavily_err, exc_info=True)
            if error_message is None: error_message = tavily_err
            tavily_instance = None
    else: logger.warning("Tavily API Key not provided."); tavily_instance = None


    return llm_instance, tavily_instance, error_message

# --- Modified Retry Decorator ---
# Removed the initial GLOBAL_LLM check
def with_retry(func):
    """Decorator to add retry logic to functions, especially LLM calls."""
    @wraps(func)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda rs: logger.warning(
            f"Retrying {func.__name__} (attempt {rs.attempt_number}) after {rs.next_action.sleep:.2f}s delay..."
        )
    )
    def wrapper(*args, **kwargs):
        try:
            # Execute the decorated function
            return func(*args, **kwargs)
        except Exception as e:
            # Log the error after all retries have failed
            logger.error(f"Error in {func.__name__} after retries: {e}", exc_info=True)
            raise # Re-raise the exception
    return wrapper

# --- Workflow Functions ---
# --- MODIFIED TO USE state['llm_instance'] and state['tavily_instance'] ---

# --- User Input Cycle ---
@with_retry
def generate_questions(state: MainState) -> MainState:
    """Generates clarification questions."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    context = f"Project: {state['project']} ({state['category']}/{state['subcategory']}) in {state['coding_language']}."
    iteration = state.get("user_input_iteration", 0)
    if iteration == 0:
        prompt = f"You are a requirements analyst. Ask exactly 5 concise questions to clarify the initial needs for this project: {context}"
    else:
        qa_history = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(state.get("user_input_questions",[]), state.get("user_input_answers",[]))])
        prompt = f"Based on the previous Q&A for the project ({context}), ask up to 5 more concise clarification questions...\nPrevious Q&A:\n{qa_history}"
    response = llm.invoke(prompt) # Use LLM from state
    questions = [q.strip() for q in response.content.strip().split("\n") if q.strip()]
    state["user_input_questions"] = state.get("user_input_questions", []) + questions
    state["messages"].append(AIMessage(content="\n".join(questions)))
    logger.info(f"Generated {len(questions)} questions for iteration {iteration}.")
    return state

@with_retry
def refine_prompt(state: MainState) -> MainState:
    """Synthesizes Q&A into a refined prompt."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    qa_history = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(state.get("user_input_questions",[]), state.get("user_input_answers",[]))])
    prompt = f"Based on the following Q&A history for project '{state['project']}', synthesize a concise 'Refined Prompt'...\nQ&A History:\n{qa_history}\n---\nOutput ONLY the refined prompt text."
    response = llm.invoke(prompt) # Use LLM from state
    refined_prompt_text = response.content.strip()
    state["refined_prompt"] = refined_prompt_text
    state["user_query_with_qa"] = qa_history
    state["messages"].append(AIMessage(content=f"Refined Prompt:\n{refined_prompt_text}"))
    logger.info("Refined project prompt based on Q&A.")
    # Save logic remains the same
    try:
        project_folder_name = state.get("project_folder", "default_project")
        abs_project_folder = os.path.abspath(project_folder_name)
        intro_dir = os.path.join(abs_project_folder, "1_intro")
        os.makedirs(intro_dir, exist_ok=True)
        qa_path = os.path.join(intro_dir, "user_query_with_qa.txt")
        prompt_path = os.path.join(intro_dir, "refined_prompt.md")
        with open(qa_path, "w", encoding="utf-8") as f: f.write(qa_history)
        with open(prompt_path, "w", encoding="utf-8") as f: f.write(refined_prompt_text)
        logger.info(f"Saved Q&A history and refined prompt to {intro_dir}")
    except Exception as e: logger.error(f"Failed to save intro files: {e}", exc_info=True)
    return state

# --- User Story Cycle ---
@with_retry
def generate_initial_user_stories(state: MainState) -> MainState:
    """Generates initial user stories."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    prompt = f"Generate a list of user stories for project '{state['project']}' using standard format 'As a..., I want..., so that...'. Base on:\nRefined Prompt:\n{state['refined_prompt']}"
    response = llm.invoke(prompt) # Use LLM from state
    initial_user_stories = response.content.strip()
    state["user_story_current"] = initial_user_stories
    state["messages"].append(AIMessage(content=f"Initial User Stories:\n{initial_user_stories}"))
    logger.info("Generated Initial User Stories.")
    return state

@with_retry
def generate_user_story_feedback(state: MainState) -> MainState:
    """Generates AI feedback on user stories."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    prompt = f"Act as QA. Review user stories for clarity, atomicity, testability, alignment...\nUser Stories:\n{state.get('user_story_current', 'N/A')}\n---\nRefined Prompt (Context):\n{state.get('refined_prompt', 'N/A')[:500]}..."
    response = llm.invoke(prompt) # Use LLM from state
    feedback = response.content.strip()
    state["user_story_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"User Story Feedback:\n{feedback}"))
    logger.info("Generated feedback on user stories.")
    return state

@with_retry
def refine_user_stories(state: MainState) -> MainState:
    """Refines user stories based on feedback."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    prompt = f"Refine user stories for '{state['project']}' based on feedback.\nCurrent Stories:\n{state.get('user_story_current', 'N/A')}\nAI FB:\n{state.get('user_story_feedback', 'N/A')}\nHuman FB:\n{state.get('user_story_human_feedback', 'N/A')}\n---\nOutput refined list."
    response = llm.invoke(prompt) # Use LLM from state
    refined_user_stories = response.content.strip()
    state["user_story_current"] = refined_user_stories
    state["messages"].append(AIMessage(content=f"Refined User Stories:\n{refined_user_stories}"))
    logger.info("Refined User Stories based on feedback.")
    return state

# save_final_user_story remains unchanged (no LLM calls)
def save_final_user_story(state: MainState) -> MainState:
    """Saves the final version of user stories to a file and updates the state."""
    state["final_user_story"] = state.get("user_story_current", "No user stories generated.")
    filepath = None # Initialize path as None
    try:
        abs_project_folder = os.path.abspath(state["project_folder"])
        us_dir = os.path.join(abs_project_folder, "2_user_story")
        os.makedirs(us_dir, exist_ok=True)
        filepath = os.path.join(us_dir, "final_user_story.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(state["final_user_story"])
        logger.info(f"Saved final user story to: {filepath}")
    except Exception as e:
        logger.error(f"Failed to save final user story: {e}", exc_info=True)
        filepath = None # Ensure path is None if saving failed
    state["final_user_story_path"] = filepath
    return state

# --- Product Owner Review Cycle ---
@with_retry
def generate_initial_product_review(state: MainState) -> MainState:
    """Generates an initial product review."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    prompt = f"Act as Product Owner for '{state['project']}'. Review prompt and stories, assess alignment, completeness, concerns...\nPrompt:\n{state.get('refined_prompt', 'N/A')}\nStories:\n{state.get('final_user_story', 'N/A')}"
    response = llm.invoke(prompt) # Use LLM from state
    initial_review = response.content.strip()
    state["product_review_current"] = initial_review
    state["messages"].append(AIMessage(content=f"Initial Product Review:\n{initial_review}"))
    logger.info("Generated initial product owner review.")
    return state

@with_retry
def generate_product_review_feedback(state: MainState) -> MainState:
    """Generates AI feedback on the product review."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    prompt = f"Review the PO assessment for clarity, logic, priorities...\nPO Review:\n{state.get('product_review_current', 'N/A')}\nStories (Context):\n{state.get('final_user_story', 'N/A')[:1000]}..."
    response = llm.invoke(prompt) # Use LLM from state
    feedback = response.content.strip()
    state["product_review_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"Product Review Feedback:\n{feedback}"))
    logger.info("Generated feedback on product review.")
    return state

@with_retry
def refine_product_review(state: MainState) -> MainState:
    """Refines the product review based on feedback."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    prompt = f"Refine the PO review for '{state['project']}' based on feedback.\nCurrent:\n{state.get('product_review_current', 'N/A')}\nAI FB:\n{state.get('product_review_feedback', 'N/A')}\nHuman FB:\n{state.get('product_review_human_feedback', 'N/A')}\n---\nOutput refined review."
    response = llm.invoke(prompt) # Use LLM from state
    refined_review = response.content.strip()
    state["product_review_current"] = refined_review
    state["messages"].append(AIMessage(content=f"Refined Product Review:\n{refined_review}"))
    logger.info("Refined product owner review.")
    return state

# save_final_product_review remains unchanged
def save_final_product_review(state: MainState) -> MainState:
    """Saves the final product review to a file."""
    state["final_product_review"] = state.get("product_review_current", "No review generated.")
    filepath = None
    try:
        abs_project_folder = os.path.abspath(state["project_folder"])
        pr_dir = os.path.join(abs_project_folder, "3_product_review")
        os.makedirs(pr_dir, exist_ok=True)
        filepath = os.path.join(pr_dir, "final_product_review.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(state["final_product_review"])
        logger.info(f"Saved final product review to: {filepath}")
    except Exception as e:
        logger.error(f"Failed to save final product review: {e}", exc_info=True)
        filepath = None
    state["final_product_review_path"] = filepath
    return state

# --- Design Document Cycle ---
@with_retry
def generate_initial_design_doc(state: MainState) -> MainState:
    """Generates the initial design document."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    prompt = f"Act as System Architect for '{state['project']}'. Create high-level design (Arch, Components, Data, API, Tech, Deploy) based on...\nPrompt:\n{state.get('refined_prompt', 'N/A')}\nStories:\n{state.get('final_user_story', 'N/A')}\nReview:\n{state.get('final_product_review', 'N/A')}"
    response = llm.invoke(prompt) # Use LLM from state
    initial_doc = response.content.strip()
    state["design_doc_current"] = initial_doc
    state["messages"].append(AIMessage(content=f"Initial Design Document:\n{initial_doc}"))
    logger.info("Generated Initial Design Document")
    return state

@with_retry
def generate_design_doc_feedback(state: MainState) -> MainState:
    """Generates AI feedback on the design document."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    prompt = f"Review Design Doc for completeness, clarity, consistency, feasibility...\nDoc:\n{state.get('design_doc_current', 'N/A')}\nStories (Context):\n{state.get('final_user_story', 'N/A')[:1000]}..."
    response = llm.invoke(prompt) # Use LLM from state
    feedback = response.content.strip()
    state["design_doc_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"Design Document Feedback:\n{feedback}"))
    logger.info("Generated Design Document Feedback")
    return state

@with_retry
def refine_design_doc(state: MainState) -> MainState:
    """Refines the design document based on feedback."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    prompt = f"Refine Design Doc for '{state['project']}' based on feedback.\nCurrent:\n{state.get('design_doc_current', 'N/A')}\nAI FB:\n{state.get('design_doc_feedback', 'N/A')}\nHuman FB:\n{state.get('design_doc_human_feedback', 'N/A')}\n---\nOutput refined doc."
    response = llm.invoke(prompt) # Use LLM from state
    refined_doc = response.content.strip()
    state["design_doc_current"] = refined_doc
    state["messages"].append(AIMessage(content=f"Refined Design Document:\n{refined_doc}"))
    logger.info("Refined Design Document")
    return state

# save_final_design_doc remains unchanged
def save_final_design_doc(state: MainState) -> MainState:
    """Saves the final design document."""
    state["final_design_document"] = state.get("design_doc_current", "No design generated.")
    filepath = None
    try:
        abs_project_folder = os.path.abspath(state["project_folder"])
        dd_dir = os.path.join(abs_project_folder, "4_design_doc")
        os.makedirs(dd_dir, exist_ok=True)
        filepath = os.path.join(dd_dir, "final_design_document.md")
        with open(filepath, "w", encoding="utf-8") as f: f.write(state["final_design_document"])
        logger.info(f"Saved final design doc: {filepath}")
    except Exception as e: logger.error(f"Failed save design doc: {e}", exc_info=True); filepath = None
    state["final_design_document_path"] = filepath
    return state


# --- UML Diagram Cycle ---
@with_retry
def select_uml_diagrams(state: MainState) -> MainState:
    """Selects relevant UML/DFD diagram types."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    all_diagram_types = ', '.join(PLANTUML_SYNTAX_RULES.keys())
    prompt = f"Select 5 most relevant UML/DFD types for '{state['project']}' from list [{all_diagram_types}] based on Design Doc:\n{state.get('final_design_document', 'N/A')}\nJustify choices. Output ONLY JSON (DiagramSelection model)."
    structured_llm = llm.with_structured_output(DiagramSelection) # Use LLM from state
    response = structured_llm.invoke(prompt)
    unique_types = list(dict.fromkeys(response.diagram_types))[:5]
    final_justifications = response.justifications[:len(unique_types)]
    state["uml_selected_diagrams"] = unique_types
    display_msg = "Selected Diagrams:\n" + "\n".join(f"- {dt} - {j}" for dt, j in zip(unique_types, final_justifications))
    state["messages"].append(AIMessage(content=display_msg))
    logger.info(f"Selected UML Diagrams: {', '.join(unique_types)}")
    return state

@with_retry
def generate_initial_uml_codes(state: MainState) -> MainState:
    """Generates initial PlantUML code for selected diagram types."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    generated_codes = []
    selected_diagrams = state.get("uml_selected_diagrams", [])
    if not selected_diagrams: logger.warning("No diagrams selected."); state["uml_current_codes"] = []; return state

    logger.info(f"Generating initial PlantUML code for: {', '.join(selected_diagrams)}")
    for diagram_type in selected_diagrams:
        syntax_info = PLANTUML_SYNTAX_RULES.get(diagram_type, {})
        default_code = "@startuml\n' Default template\n@enduml"
        code_to_use = syntax_info.get("template", default_code)
        prompt = f"Generate PlantUML code for a '{diagram_type}' for '{state['project']}'. Base on Design Doc:\n{state.get('final_design_document', 'N/A')[:2000]}...\nAdhere to syntax:\nTemplate:\n{syntax_info.get('template', 'N/A')}\nNotes: {syntax_info.get('notes', 'N/A')}\n---\nGenerate ONLY the PlantUML code block."
        try:
            structured_llm = llm.with_structured_output(PlantUMLCode) # Use LLM from state
            response = structured_llm.invoke(prompt)
            generated_code = response.code.strip() if response and response.code else ""
            if validate_plantuml_code(diagram_type, generated_code): code_to_use = generated_code
            else: logger.warning(f"Generated code for {diagram_type} failed validation. Using template.")
        except Exception as e: logger.error(f"Failed to generate/validate PlantUML for {diagram_type}: {e}. Using template.", exc_info=True)
        generated_codes.append(PlantUMLCode(diagram_type=diagram_type, code=code_to_use))

    state["uml_current_codes"] = generated_codes
    summary = "\n".join([f"**{c.diagram_type}**:\n```plantuml\n{c.code}\n```" for c in generated_codes])
    state["messages"].append(AIMessage(content=f"Generated Initial UML Codes:\n{summary}"))
    logger.info(f"Generated initial code for {len(generated_codes)} UML diagrams.")
    return state

@with_retry
def generate_uml_feedback(state: MainState) -> MainState:
    """Generates AI feedback for each current UML diagram."""
    # Use primary LLM from state, fallback needed? Or rely on app config? Assuming primary.
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    feedback_dict = {}
    current_codes = state.get('uml_current_codes', [])
    if not current_codes: logger.warning("No UML codes for feedback."); state["uml_feedback"] = {}; return state

    logger.info(f"Generating feedback for {len(current_codes)} UML diagrams.")
    for plantuml_code in current_codes:
        diagram_type = plantuml_code.diagram_type; code_to_review = plantuml_code.code
        syntax_info = PLANTUML_SYNTAX_RULES.get(diagram_type, {})
        prompt = f"Review PlantUML code for '{diagram_type}' of '{state['project']}'. Check Syntax, Alignment with Design, Clarity.\nSyntax (Ref):\n{syntax_info.get('template', 'N/A')}\nNotes: {syntax_info.get('notes', 'N/A')}\nCode:\n```plantuml\n{code_to_review}\n```\nDesign (Context):\n{state.get('final_design_document', 'N/A')[:1000]}...\n---\nProvide feedback."
        try:
            # Maybe use OPENAI_LLM if available and different? For now, use primary.
            response = llm.invoke(prompt) # Use LLM from state
            feedback_dict[diagram_type] = response.content.strip()
        except Exception as e: logger.error(f"Failed feedback for {diagram_type}: {e}"); feedback_dict[diagram_type] = f"Error: {e}"

    state["uml_feedback"] = feedback_dict
    summary = "\n\n".join([f"**Feedback for {dt}:**\n{fb}" for dt, fb in feedback_dict.items()])
    state["messages"].append(AIMessage(content=f"UML Feedback Provided:\n{summary}"))
    logger.info("Generated feedback for all current UML diagrams.")
    return state

@with_retry
def refine_uml_codes(state: MainState) -> MainState:
    """Refines UML codes based on feedback."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    refined_codes_list = []
    current_codes = state.get('uml_current_codes', [])
    ai_feedback = state.get('uml_feedback', {})
    human_feedback = state.get('uml_human_feedback', {})
    if not current_codes: logger.warning("No UML codes to refine."); return state

    logger.info(f"Refining {len(current_codes)} UML diagrams.")
    for plantuml_code_obj in current_codes:
        diagram_type = plantuml_code_obj.diagram_type; current_code = plantuml_code_obj.code
        syntax_info = PLANTUML_SYNTAX_RULES.get(diagram_type, {})
        specific_human_feedback = human_feedback.get(diagram_type, human_feedback.get('all', 'N/A'))
        prompt = f"Refine PlantUML for '{diagram_type}' of '{state['project']}' based on feedback.\nSyntax (Ref):\n{syntax_info.get('template', 'N/A')}\nNotes: {syntax_info.get('notes', 'N/A')}\nCurrent:\n```plantuml\n{current_code}\n```\nAI FB:\n{ai_feedback.get(diagram_type, 'N/A')}\nHuman FB:\n{specific_human_feedback}\n---\nGenerate ONLY refined PlantUML block."
        try:
            structured_llm = llm.with_structured_output(PlantUMLCode) # Use LLM from state
            response = structured_llm.invoke(prompt)
            refined_code = response.code.strip() if response and response.code else ""
            if validate_plantuml_code(diagram_type, refined_code):
                refined_codes_list.append(PlantUMLCode(diagram_type=diagram_type, code=refined_code))
            else: logger.warning(f"Refined {diagram_type} invalid. Reverting."); refined_codes_list.append(plantuml_code_obj)
        except Exception as e: logger.error(f"Failed refine {diagram_type}: {e}. Reverting.", exc_info=True); refined_codes_list.append(plantuml_code_obj)

    state["uml_current_codes"] = refined_codes_list
    summary = "\n".join([f"**{c.diagram_type} (Refined):**\n```plantuml\n{c.code}\n```" for c in refined_codes_list])
    state["messages"].append(AIMessage(content=f"Refined UML Codes:\n{summary}"))
    logger.info(f"Refined {len(refined_codes_list)} UML diagrams.")
    return state

# save_final_uml_diagrams remains unchanged (no LLM calls)
def save_final_uml_diagrams(state: MainState) -> MainState:
    """Saves the final Puml files and attempts to generate PNGs."""
    state["final_uml_codes"] = state.get("uml_current_codes", [])
    png_paths = [] # List to store paths of successfully generated PNGs
    uml_dir = None
    try:
        abs_project_folder = os.path.abspath(state["project_folder"])
        uml_dir = os.path.join(abs_project_folder, "5_uml_diagrams")
        os.makedirs(uml_dir, exist_ok=True)
        state["final_uml_diagram_folder"] = uml_dir # Store path to folder
        can_generate_png = False
        server = None
        try:
            server = PlantUML(url="http://www.plantuml.com/plantuml/png/")
            can_generate_png = True
            logger.info("PlantUML server connection appears OK.")
        except Exception as p_e:
            logger.warning(f"PlantUML server connection failed: {p_e}. PNG generation will be skipped. Check Java/PlantUML setup and network connectivity.", exc_info=True)
        if not state["final_uml_codes"]:
            logger.warning("No UML codes found to save."); state["final_uml_png_paths"] = []; return state
        logger.info(f"Saving {len(state['final_uml_codes'])} UML diagrams to {uml_dir}...")
        for i, pc in enumerate(state["final_uml_codes"], 1):
            safe_type_name = "".join(c if c.isalnum() or c in ['_','-'] else '_' for c in pc.diagram_type).lower()
            name = f"diagram_{i}_{safe_type_name}"
            puml_path = os.path.join(uml_dir, f"{name}.puml")
            png_path = os.path.join(uml_dir, f"{name}.png")
            try:
                with open(puml_path, "w", encoding="utf-8") as f: f.write(pc.code)
                logger.debug(f"Saved PUML file: {puml_path}")
            except Exception as file_e: logger.error(f"Error saving PUML file {puml_path}: {file_e}", exc_info=True); continue
            if can_generate_png and server:
                logger.debug(f"Attempting PNG generation for {name}...")
                try:
                    server.processes_file(filename=puml_path, outfile=png_path)
                    if os.path.exists(png_path) and os.path.getsize(png_path) > 0:
                        logger.info(f"Successfully generated PNG: {png_path}"); png_paths.append(png_path)
                    else: logger.error(f"PlantUML processed '{name}' but output PNG is missing or empty: {png_path}")
                except FileNotFoundError as fnf_err: logger.error(f"PNG generation failed for {name}: Executable/Java not found? Error: {fnf_err}", exc_info=False)
                except Exception as png_e: logger.error(f"PNG generation failed for {name} ({pc.diagram_type}): {png_e}", exc_info=False)
            elif not can_generate_png: logger.debug(f"Skipping PNG generation for {name} due to server connection issue.")
        state["final_uml_png_paths"] = png_paths
        logger.info(f"Finished UML saving. Saved {len(state['final_uml_codes'])} PUML files. Generated {len(png_paths)} PNG files.")
    except Exception as e:
        logger.error(f"General error in save_final_uml_diagrams: {e}", exc_info=True)
        state["final_uml_diagram_folder"] = None; state["final_uml_png_paths"] = []
    return state


# --- Code Generation Cycle ---
@with_retry
def generate_initial_code(state: MainState) -> MainState:
    """Generates the initial codebase."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    uml_types = ', '.join([c.diagram_type for c in state.get('final_uml_codes', [])])
    prompt = f"Generate complete, runnable '{state['coding_language']}' project for '{state['project']}'. Base on Design Doc, User Stories, and UML ({uml_types}). Include main scripts, modules, requirements, basic README, comments.\nDesign:\n{state.get('final_design_document', 'N/A')}\nStories (Context):\n{state.get('final_user_story', 'N/A')}...\n---\nOutput ONLY JSON (GeneratedCode model)."
    structured_llm = llm.with_structured_output(GeneratedCode) # Use LLM from state
    response = structured_llm.invoke(prompt)
    if not response or not isinstance(response, GeneratedCode) or not response.files:
        logger.error("Initial code gen failed or invalid format."); raise ValueError("Did not produce expected file structure.")
    state["code_current"] = response
    summary = f"Generated {len(response.files)} files. Key: {', '.join([f.filename for f in response.files[:3]])}...\nInstructions:\n{response.instructions[:200]}..."
    state["messages"].append(AIMessage(content=f"Initial Code Generation:\n{summary}"))
    logger.info(f"Generated initial code with {len(response.files)} files.")
    return state

@with_retry
def web_search_code(state: MainState) -> MainState:
    """Performs web search based on user feedback."""
    tavily = state.get('tavily_instance') # Use Tavily from state
    if not tavily: logger.warning("Tavily client not in state, skipping web search."); state["code_web_search_results"] = "Skipped (Tavily client not configured)"; state["messages"].append(AIMessage(content="Web Search: Skipped")); return state
    if 'messages' not in state: state['messages'] = []
    human_input = state.get('code_human_input', '')
    if not human_input or not human_input.strip(): logger.info("Skipping web search - no issue provided."); state["code_web_search_results"] = "Skipped (No specific issue)"; state["messages"].append(AIMessage(content="Web Search: Skipped")); return state
    human_input_summary = human_input[:200]; coding_language = state.get('coding_language', 'programming'); project_context = state.get('project', 'project')[:50]
    search_query = f"{coding_language} issues related to '{human_input_summary}' in {project_context}"
    logger.info(f"Performing Tavily search: {search_query}")
    try:
        response = tavily.search(query=search_query, search_depth="basic", max_results=3) # Use tavily from state
        search_results = response.get("results", [])
        if search_results:
            results_text = "\n\n".join([f"**{r.get('title', 'N/A')}**\nURL: {r.get('url', 'N/A')}\nSnippet: {r.get('content', 'N/A')[:300]}..." for r in search_results])
            state["code_web_search_results"] = results_text; logger.info(f"Tavily found {len(search_results)} results.")
        else: state["code_web_search_results"] = "No relevant results found."; logger.info("Tavily found no results.")
    except Exception as e:
        error_detail = str(e); logger.error(f"Tavily search failed: {error_detail}", exc_info=True); state["code_web_search_results"] = f"Error during web search: {e}"
    summary = state['code_web_search_results'][:500] + ('...' if len(state['code_web_search_results']) > 500 else '')
    state["messages"].append(AIMessage(content=f"Web Search Summary:\n{summary}"))
    logger.info("Completed Web Search.")
    return state

@with_retry
def generate_code_feedback(state: MainState) -> MainState:
    """Generates AI feedback on the current code."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    func_name = "generate_code_feedback"
    code_c = state.get("code_current"); instructions = ""
    # --- CORRECTED LOOP ---
    code_str_parts = []; total_len = 0; max_code_len = 250000
    files_to_process = code_c.files if code_c and isinstance(code_c, GeneratedCode) else []
    if not files_to_process: logger.warning(f"No files in code_current for {func_name}"); code_content = "No code files provided."; instructions = "N/A"
    else:
        instructions = code_c.instructions
        for file in files_to_process:
            header = f"--- {file.filename} ---\n"; remaining_len = max_code_len - total_len - len(header)
            if remaining_len <= 0: code_str_parts.append("\n*... (Code context truncated)*"); logger.debug(f"Code context truncated for {func_name}"); break
            snippet = file.content[:remaining_len]; is_truncated = len(file.content) > remaining_len
            code_str_parts.append(header + snippet + ('...' if is_truncated else '')); total_len += len(header) + len(snippet)
            if total_len >= max_code_len:
                if not code_str_parts[-1].endswith("truncated)*"): code_str_parts.append("\n*... (Code context truncated)*")
                logger.debug(f"Code context max length for {func_name}"); break
        code_content = "\n".join(code_str_parts)
    # --- END CORRECTED LOOP ---
    prompt = f"Act as reviewer for '{state['project']}' ({state['coding_language']}). Review code, instructions, user feedback, search results. Suggest improvements.\nCode:\n{code_content}\nInstr:\n{instructions}\nUser FB:\n{state.get('code_human_input', 'N/A')}\nSearch:\n{state.get('code_web_search_results', 'N/A')}\n---\nProvide feedback."
    response = llm.invoke(prompt) # Use LLM from state
    feedback_text = response.content.strip()
    state["code_feedback"] = feedback_text
    state["messages"].append(AIMessage(content=f"AI Code Feedback:\n{feedback_text}"))
    logger.info("Generated AI feedback on the code.")
    return state

@with_retry
def refine_code(state: MainState) -> MainState:
    """Refines the code based on feedback."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    func_name = "refine_code"
    code_c = state.get("code_current"); instructions = ""
    # --- CORRECTED LOOP ---
    code_str_parts = []; total_len = 0; max_code_len = 25000
    files_to_process = code_c.files if code_c and isinstance(code_c, GeneratedCode) else []
    if not files_to_process: logger.warning(f"No files in code_current for {func_name}"); code_content = "No previous code."; instructions = state.get("code_current", GeneratedCode(files=[], instructions="")).instructions
    else:
        instructions = code_c.instructions
        for file in files_to_process:
            header = f"--- {file.filename} ---\n"; remaining_len = max_code_len - total_len - len(header)
            if remaining_len <= 0: code_str_parts.append("\n*... (Code context truncated)*"); logger.debug(f"Code context truncated for {func_name}"); break
            snippet = file.content[:remaining_len]; is_truncated = len(file.content) > remaining_len
            code_str_parts.append(header + snippet + ('...' if is_truncated else '')); total_len += len(header) + len(snippet)
            if total_len >= max_code_len:
                if not code_str_parts[-1].endswith("truncated)*"): code_str_parts.append("\n*... (Code context truncated)*")
                logger.debug(f"Code context max length for {func_name}"); break
        code_content = "\n".join(code_str_parts)
    # --- END CORRECTED LOOP ---
    prompt = f"Act as senior {state['coding_language']} dev refining '{state['project']}'. Update code based on all feedback. Address bugs, improve style, update instructions if needed.\nCode:\n{code_content}\nInstr:\n{instructions}\nUser Exec FB:\n{state.get('code_human_input','N/A')}\nSearch:\n{state.get('code_web_search_results','N/A')}\nAI Review:\n{state.get('code_feedback','N/A')}\nHuman Comments:\n{state.get('code_human_feedback','N/A')}\n---\nOutput ONLY JSON (GeneratedCode model)."
    structured_llm = llm.with_structured_output(GeneratedCode) # Use LLM from state
    response = structured_llm.invoke(prompt)
    if not response or not isinstance(response, GeneratedCode) or not response.files:
        logger.error("Code refinement failed or invalid format."); raise ValueError("Did not produce expected file structure.")
    state["code_current"] = response
    summary = f"Refined code - {len(response.files)} files. Instructions:\n{response.instructions[:200]}..."
    state["messages"].append(AIMessage(content=f"Refined Code:\n{summary}"))
    logger.info(f"Refined code, resulting in {len(response.files)} files.")
    return state

# --- Code Review & Security Cycle ---
@with_retry
def code_review(state: MainState) -> MainState:
    """Performs code review on final_code_files."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    func_name = "code_review"
    code_files_to_review = state.get("final_code_files", [])
    if not code_files_to_review: logger.warning(f"No files in final_code_files for {func_name}"); state["code_review_current_feedback"] = "No code available."; state["messages"].append(AIMessage(content="Code Review: No code.")); return state
    # --- CORRECTED LOOP ---
    code_str_parts = []; total_len = 0; max_code_len = 25000
    instructions = state.get("code_current", GeneratedCode(files=[], instructions="")).instructions
    files_to_process = code_files_to_review
    for file in files_to_process:
        header = f"--- {file.filename} ---\n"; remaining_len = max_code_len - total_len - len(header)
        if remaining_len <= 0: code_str_parts.append("\n*... (Code context truncated)*"); logger.debug(f"Code context truncated for {func_name}"); break
        snippet = file.content[:remaining_len]; is_truncated = len(file.content) > remaining_len
        code_str_parts.append(header + snippet + ('...' if is_truncated else '')); total_len += len(header) + len(snippet)
        if total_len >= max_code_len:
            if not code_str_parts[-1].endswith("truncated)*"): code_str_parts.append("\n*... (Code context truncated)*")
            logger.debug(f"Code context max length for {func_name}"); break
    code_content = "\n".join(code_str_parts)
    # --- END CORRECTED LOOP ---
    prompt = f"Perform detailed code review for '{state['project']}' ({state['coding_language']}). Focus on best practices, readability, logic, efficiency, robustness.\nCode:\n{code_content}\nInstr:\n{instructions}\n---\nProvide feedback."
    response = llm.invoke(prompt) # Use LLM from state
    feedback = response.content.strip()
    state["code_review_current_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"Code Review:\n{feedback}"))
    logger.info("Performed code review.")
    return state

@with_retry
def security_check(state: MainState) -> MainState:
    """Performs security check on final_code_files."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    func_name = "security_check"
    code_files_to_check = state.get("final_code_files", [])
    if not code_files_to_check: logger.warning(f"No files in final_code_files for {func_name}"); state["security_current_feedback"] = "No code available."; state["messages"].append(AIMessage(content="Security Check: No code.")); return state
    # --- CORRECTED LOOP ---
    code_str_parts = []; total_len = 0; max_code_len = 25000
    instructions = state.get("code_current", GeneratedCode(files=[], instructions="")).instructions
    files_to_process = code_files_to_check
    for file in files_to_process:
        header = f"--- {file.filename} ---\n"; remaining_len = max_code_len - total_len - len(header)
        if remaining_len <= 0: code_str_parts.append("\n*... (Code context truncated)*"); logger.debug(f"Code context truncated for {func_name}"); break
        snippet = file.content[:remaining_len]; is_truncated = len(file.content) > remaining_len
        code_str_parts.append(header + snippet + ('...' if is_truncated else '')); total_len += len(header) + len(snippet)
        if total_len >= max_code_len:
            if not code_str_parts[-1].endswith("truncated)*"): code_str_parts.append("\n*... (Code context truncated)*")
            logger.debug(f"Code context max length for {func_name}"); break
    code_content = "\n".join(code_str_parts)
    # --- END CORRECTED LOOP ---
    prompt = f"Act as security expert. Analyze {state['coding_language']} code for '{state['project']}'. Check for injection, XSS, auth issues, data exposure, input validation, misconfigs, vulnerable deps.\nCode:\n{code_content}\nInstr:\n{instructions}\n---\nProvide findings, impact, remediation."
    response = llm.invoke(prompt) # Use LLM from state
    feedback = response.content.strip()
    state["security_current_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"Security Check:\n{feedback}"))
    logger.info("Performed security check.")
    return state

@with_retry
def refine_code_with_reviews(state: MainState) -> MainState:
    """Refines code based on review, security, and human feedback."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    func_name = "refine_code_with_reviews"
    code_files_to_refine = state.get("final_code_files", [])
    if not code_files_to_refine: logger.error(f"No files in final_code_files for {func_name}"); raise ValueError("No code available.")
    instructions = state.get("code_current", GeneratedCode(files=[], instructions="")).instructions
    # --- CORRECTED LOOP ---
    code_str_parts = []; total_len = 0; max_code_len = 25000
    files_to_process = code_files_to_refine
    if not files_to_process: logger.warning(f"No files for {func_name}"); code_content = "No previous code."
    else:
        for file in files_to_process:
            header = f"--- {file.filename} ---\n"; remaining_len = max_code_len - total_len - len(header)
            if remaining_len <= 0: code_str_parts.append("\n*... (Code context truncated)*"); logger.debug(f"Code context truncated for {func_name}"); break
            snippet = file.content[:remaining_len]; is_truncated = len(file.content) > remaining_len
            code_str_parts.append(header + snippet + ('...' if is_truncated else '')); total_len += len(header) + len(snippet)
            if total_len >= max_code_len:
                if not code_str_parts[-1].endswith("truncated)*"): code_str_parts.append("\n*... (Code context truncated)*")
                logger.debug(f"Code context max length for {func_name}"); break
        code_content = "\n".join(code_str_parts)
    # --- END CORRECTED LOOP ---
    prompt = f"Refine {state['coding_language']} code for '{state['project']}'. Incorporate Code Review, Security Analysis, User Comments. Prioritize security/critical points. Update instructions if needed.\nCode:\n{code_content}\nInstr:\n{instructions}\nReview FB:\n{state.get('code_review_current_feedback', 'N/A')}\nSecurity FB:\n{state.get('security_current_feedback', 'N/A')}\nUser FB:\n{state.get('review_security_human_feedback', 'N/A')}\n---\nOutput ONLY JSON (GeneratedCode model)."
    structured_llm = llm.with_structured_output(GeneratedCode) # Use LLM from state
    response = structured_llm.invoke(prompt)
    if not response or not isinstance(response, GeneratedCode) or not response.files:
        logger.error("Code refinement post-review failed/invalid."); raise ValueError("Did not produce expected file structure.")
    state["final_code_files"] = response.files; state["code_current"] = response
    summary = f"Refined code ({len(response.files)} files) post-review."
    state["messages"].append(AIMessage(content=f"Code Refined Post-Review:\n{summary}"))
    logger.info(f"Refined code post-review, {len(response.files)} files.")
    return state

# save_review_security_outputs remains unchanged
def save_review_security_outputs(state: MainState) -> MainState:
    """Saves review/security feedback and the corresponding code snapshot."""
    state["final_code_review"] = state.get("code_review_current_feedback", "N/A")
    state["final_security_issues"] = state.get("security_current_feedback", "N/A")
    rs_dir, code_snap_dir = None, None # Initialize paths
    try:
        abs_project_folder = os.path.abspath(state["project_folder"])
        rs_dir = os.path.join(abs_project_folder, "6_review_security")
        os.makedirs(rs_dir, exist_ok=True)
        code_snap_dir = os.path.join(rs_dir, "code_snapshot")
        os.makedirs(code_snap_dir, exist_ok=True)

        # Store paths in state
        state["final_review_security_folder"] = rs_dir
        state["review_code_snapshot_folder"] = code_snap_dir

        # Save feedback files
        review_path = os.path.join(rs_dir, "final_code_review.md")
        security_path = os.path.join(rs_dir, "final_security_issues.md")
        with open(review_path, "w", encoding="utf-8") as f: f.write(state["final_code_review"])
        with open(security_path, "w", encoding="utf-8") as f: f.write(state["final_security_issues"])
        logger.debug(f"Saved review feedback files to {rs_dir}")

        # Save the code snapshot (should be the version just refined)
        files_to_save = state.get("final_code_files", [])
        instructions = state.get("code_current", GeneratedCode(files=[], instructions="")).instructions

        if files_to_save:
            logger.info(f"Saving {len(files_to_save)} code files to snapshot folder: {code_snap_dir}")
            for file in files_to_save:
                filename = file.filename; content = file.content
                relative_path = filename.lstrip('/\\'); filepath = os.path.normpath(os.path.join(code_snap_dir, relative_path))
                if not os.path.abspath(filepath).startswith(os.path.abspath(code_snap_dir)):
                    logger.warning(f"Attempted path traversal! Skipping file: {filename} -> {filepath}"); continue
                try:
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, "w", encoding="utf-8") as f: f.write(content)
                    logger.debug(f"Saved code file: {filepath}")
                except OSError as path_err: logger.error(f"Could not create directory or save file '{filepath}': {path_err}")
                except Exception as write_err: logger.error(f"Error writing file '{filepath}': {write_err}")
            try: # Save instructions
                instr_path = os.path.join(code_snap_dir, "instructions.md")
                with open(instr_path, "w", encoding="utf-8") as f: f.write(instructions)
                logger.debug(f"Saved instructions file: {instr_path}")
            except Exception as instr_err: logger.error(f"Error writing instructions file: {instr_err}")
            logger.info(f"Finished saving review/security outputs and code snapshot to {rs_dir}")
        else: logger.warning("No code files found in 'final_code_files' to save for review snapshot.")
    except Exception as e:
        logger.error(f"General error in save_review_security_outputs: {e}", exc_info=True)
        state["final_review_security_folder"] = None; state["review_code_snapshot_folder"] = None
    return state

# --- Test Case Generation Cycle ---
@with_retry
def generate_initial_test_cases(state: MainState) -> MainState:
    """Generates initial test cases."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    func_name = "generate_initial_test_cases"
    # --- RECOMMENDED: Use corrected loop ---
    code_str_parts = []; total_len = 0; max_code_len = 25000
    files_to_process = state.get("final_code_files", [])
    if not files_to_process: logger.warning(f"No files for {func_name}"); code_str = "No code files provided."
    else:
        for file in files_to_process:
            header = f"--- {file.filename} ---\n"; remaining_len = max_code_len - total_len - len(header)
            if remaining_len <= 0: code_str_parts.append("\n*... (Code context truncated)*"); break
            snippet = file.content[:remaining_len]; is_truncated = len(file.content) > remaining_len
            code_str_parts.append(header + snippet + ('...' if is_truncated else '')); total_len += len(header) + len(snippet)
            if total_len >= max_code_len:
                if not code_str_parts[-1].endswith("truncated)*"): code_str_parts.append("\n*... (Code context truncated)*")
                break
        code_str = "\n".join(code_str_parts)
    # --- END RECOMMENDED LOOP ---
    if not state.get("final_code_files"): raise ValueError("No code found for test case generation.")
    prompt = f"Generate >=3 diverse test cases (happy, edge, error) for '{state['project']}' ({state['coding_language']}). Base on stories, design, code.\nStories:\n{state.get('final_user_story', 'N/A')[:1000]}...\nDesign:\n{state.get('final_design_document', 'N/A')[:1000]}...\nCode:\n{code_str}\n---\nOutput ONLY JSON (TestCases model)."
    structured_llm = llm.with_structured_output(TestCases) # Use LLM from state
    response = structured_llm.invoke(prompt)
    if not response or not isinstance(response, TestCases) or not response.test_cases:
        logger.error("Test case gen failed/invalid."); raise ValueError("Did not produce valid test cases.")
    state["test_cases_current"] = response.test_cases
    summary = "\n".join([f"- {tc.description}" for tc in response.test_cases])
    state["messages"].append(AIMessage(content=f"Generated Initial Test Cases:\n{summary}"))
    logger.info(f"Generated {len(response.test_cases)} initial test cases.")
    return state

@with_retry
def generate_test_cases_feedback(state: MainState) -> MainState:
    """Generates AI feedback on test cases."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    current_tests = state.get("test_cases_current", [])
    if not current_tests: logger.warning("No test cases for feedback."); state["test_cases_feedback"] = "No tests found."; return state
    tests_str = "\n".join([f"- {tc.description}: Input={tc.input_data}, Expected={tc.expected_output}" for tc in current_tests])
    code_files = state.get("final_code_files", []); code_sample = code_files[0].content[:500] + '...' if code_files else "N/A"
    prompt = f"Review test cases for '{state['project']}'. Assess coverage, clarity, effectiveness, realism. Suggest improvements.\nTests:\n{tests_str}\nStories (Context):\n{state.get('final_user_story', 'N/A')[:1000]}...\nCode (Context):\n{code_sample}\n---\nProvide feedback."
    response = llm.invoke(prompt) # Use LLM from state
    feedback = response.content.strip()
    state["test_cases_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"Test Case Feedback:\n{feedback}"))
    logger.info("Generated feedback on test cases.")
    return state

@with_retry
def refine_test_cases_and_code(state: MainState) -> MainState:
    """Refines test cases and code based on feedback."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    func_name = "refine_test_cases_and_code"
    current_tests = state.get("test_cases_current", []); current_code_files = state.get("final_code_files", [])
    instructions = state.get("code_current", GeneratedCode(files=[], instructions="")).instructions
    if not current_tests or not current_code_files: logger.error(f"Missing tests or code for {func_name}"); raise ValueError("Missing data.")
    tests_str = "\n".join([f"- {tc.description}: Input={tc.input_data}, Expected={tc.expected_output}" for tc in current_tests])
    # --- CORRECTED LOOP ---
    code_str_parts = []; total_len = 0; max_code_len = 25000
    files_to_process = current_code_files
    if not files_to_process: logger.warning(f"No files for {func_name}"); code_str = "No code."
    else:
        for file in files_to_process:
            header = f"--- {file.filename} ---\n"; remaining_len = max_code_len - total_len - len(header)
            if remaining_len <= 0: code_str_parts.append("\n*... (Code context truncated)*"); logger.debug(f"Code context truncated for {func_name}"); break
            snippet = file.content[:remaining_len]; is_truncated = len(file.content) > remaining_len
            code_str_parts.append(header + snippet + ('...' if is_truncated else '')); total_len += len(header) + len(snippet)
            if total_len >= max_code_len:
                if not code_str_parts[-1].endswith("truncated)*"): code_str_parts.append("\n*... (Code context truncated)*")
                logger.debug(f"Code context max length for {func_name}"); break
        code_str = "\n".join(code_str_parts)
    # --- END CORRECTED LOOP ---
    class TestAndCode(BaseModel):
        test_cases: List[TestCase]; files: List[CodeFile]
    prompt = f"Tests failed for '{state['project']}'. Refine BOTH tests AND code based on feedback. Goal: refined code passes refined tests.\nTests:\n{tests_str}\nCode:\n{code_str}\nInstr:\n{instructions}\nAI Test FB:\n{state.get('test_cases_feedback','N/A')}\nHuman FB/Results:\n{state.get('test_cases_human_feedback','N/A')}\n---\nOutput ONLY JSON (TestAndCode model)."
    structured_llm = llm.with_structured_output(TestAndCode) # Use LLM from state
    response = structured_llm.invoke(prompt)
    if not response or not isinstance(response, TestAndCode) or not response.test_cases or not response.files:
        logger.error("Refinement of tests/code failed/invalid."); raise ValueError("Did not produce expected results.")
    state["test_cases_current"] = response.test_cases; state["final_code_files"] = response.files
    state["code_current"] = GeneratedCode(files=response.files, instructions=instructions) # Keep old instructions
    summary = f"Refined {len(response.files)} code files & {len(response.test_cases)} tests."
    state["messages"].append(AIMessage(content=f"Refined Tests and Code:\n{summary}"))
    logger.info("Refined test cases and code.")
    return state

# save_testing_outputs remains unchanged
def save_testing_outputs(state: MainState) -> MainState:
    """Saves the final tests and the code version that passed them."""
    state["final_test_code_files"] = state.get("final_code_files", [])
    final_tests = state.get("test_cases_current", [])
    test_dir, code_snap_dir = None, None
    try:
        abs_project_folder = os.path.abspath(state["project_folder"])
        test_dir = os.path.join(abs_project_folder, "7_testing"); os.makedirs(test_dir, exist_ok=True)
        code_snap_dir = os.path.join(test_dir, "passed_code"); os.makedirs(code_snap_dir, exist_ok=True)
        state["final_testing_folder"] = test_dir; state["testing_passed_code_folder"] = code_snap_dir

        # Save test cases file
        tc_path = os.path.join(test_dir, "final_test_cases.md")
        tc_str = "\n\n".join([f"**{tc.description}**\nInput:`{tc.input_data}`\nExpected:`{tc.expected_output}`" for tc in final_tests])
        with open(tc_path, "w", encoding="utf-8") as f: f.write(f"# Final Test Cases ({len(final_tests)} Passed)\n\n{tc_str}")
        logger.debug(f"Saved test cases file: {tc_path}")

        # Save the code snapshot that passed
        passed_code_files = state.get("final_test_code_files",[]);
        instructions = state.get("code_current", GeneratedCode(files=[],instructions="")).instructions
        if passed_code_files:
            logger.info(f"Saving {len(passed_code_files)} passed code files to snapshot: {code_snap_dir}")
            for file in passed_code_files: # Save files with path safety
                fn=file.filename; content=file.content; safe_fn=os.path.basename(fn)
                if not safe_fn or ('/' in fn and '..' in fn) or ('\\' in fn and '..' in fn): logger.warning(f"Skip unsafe file: {fn}"); continue
                rel_path=fn.lstrip('/\\'); filepath=os.path.normpath(os.path.join(code_snap_dir, rel_path))
                if not os.path.abspath(filepath).startswith(os.path.abspath(code_snap_dir)): logger.warning(f"Skip traversal: {fn}"); continue
                try:
                    os.makedirs(os.path.dirname(filepath), exist_ok=True);
                    with open(filepath, "w", encoding="utf-8") as f: f.write(content)
                    logger.debug(f"Saved code file: {filepath}")
                except OSError as path_err: logger.error(f"Path error saving '{filepath}': {path_err}")
                except Exception as write_err: logger.error(f"Error writing '{filepath}': {write_err}")
            try: # Save instructions
                instr_path = os.path.join(code_snap_dir, "instructions.md")
                with open(instr_path,"w",encoding="utf-8") as f: f.write(instructions)
                logger.debug(f"Saved instructions: {instr_path}")
            except Exception as instr_err: logger.error(f"Error writing instructions: {instr_err}")
            logger.info(f"Finished saving testing outputs and passed code to {test_dir}")
        else: logger.warning("No passed code files found in state to save.")
    except Exception as e: logger.error(f"Failed save testing outputs: {e}", exc_info=True); state["final_testing_folder"]=None; state["testing_passed_code_folder"]=None
    return state


# --- Quality Analysis Cycle ---
@with_retry
def generate_initial_quality_analysis(state: MainState) -> MainState:
    """Generates an overall quality analysis report."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    func_name = "generate_initial_quality_analysis"
    code_files_passed = state.get("final_test_code_files", [])
    instructions = state.get("code_current", GeneratedCode(files=[], instructions="")).instructions
    if not code_files_passed: logger.warning(f"No tested code for {func_name}."); state["quality_current_analysis"] = "No passed code available."; return state
    # --- CORRECTED LOOP ---
    code_str_parts = []; total_len = 0; max_code_len = 25000
    files_to_process = code_files_passed
    if not files_to_process: logger.error(f"Logic error: files_to_process empty in {func_name}"); code_str = "Error retrieving code."
    else:
        for file in files_to_process:
            header = f"--- {file.filename} ---\n"; remaining_len = max_code_len - total_len - len(header)
            if remaining_len <= 0: code_str_parts.append("\n*... (Code context truncated)*"); logger.debug(f"Code context truncated for {func_name}"); break
            snippet = file.content[:remaining_len]; is_truncated = len(file.content) > remaining_len
            code_str_parts.append(header + snippet + ('...' if is_truncated else '')); total_len += len(header) + len(snippet)
            if total_len >= max_code_len:
                if not code_str_parts[-1].endswith("truncated)*"): code_str_parts.append("\n*... (Code context truncated)*")
                logger.debug(f"Code context max length for {func_name}"); break
        code_str = "\n".join(code_str_parts)
    # --- END CORRECTED LOOP ---
    tests_str = "\n".join([f"- {tc.description}" for tc in state.get("test_cases_current", [])])[:500] + "..."
    prompt = f"Generate QA report for '{state['project']}' ({state['coding_language']}). Code passed tests. Assess Maintainability, Perf, Scale, Security, Coverage, Docs, Confidence Score (1-10).\nCode:\n{code_str}\nTests:\n{tests_str}\nInstr:\n{instructions}\nReview Sum:\n{state.get('final_code_review','N/A')[:500]}...\nSecurity Sum:\n{state.get('final_security_issues','N/A')[:500]}...\n---"
    response = llm.invoke(prompt) # Use LLM from state
    qa_report = response.content.strip()
    state["quality_current_analysis"] = qa_report
    state["messages"].append(AIMessage(content=f"Initial Quality Analysis Report:\n{qa_report}"))
    logger.info("Generated Initial Quality Analysis Report.")
    return state

@with_retry
def generate_quality_feedback(state: MainState) -> MainState:
    """Generates AI feedback on the QA report."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    current_qa_report = state.get('quality_current_analysis', 'N/A')
    if current_qa_report == 'N/A': logger.warning("No QA report for feedback."); state["quality_feedback"] = "No QA report."; return state
    prompt = f"Review QA report for '{state['project']}'. Critique fairness, comprehensiveness, logic, missing aspects.\nReport:\n{current_qa_report}"
    response = llm.invoke(prompt) # Use LLM from state
    feedback = response.content.strip()
    state["quality_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"Feedback on QA Report:\n{feedback}"))
    logger.info("Generated feedback on the Quality Analysis report.")
    return state

@with_retry
def refine_quality_and_code(state: MainState) -> MainState:
    """Refines QA report and potentially minor code aspects."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    func_name = "refine_quality_and_code"
    code_files_base = state.get("final_test_code_files", [])
    instructions = state.get("code_current", GeneratedCode(files=[], instructions="")).instructions
    # --- CORRECTED LOOP ---
    code_str_parts = []; total_len = 0; max_code_len = 25000
    files_to_process = code_files_base
    if not files_to_process: logger.warning(f"No tested code for {func_name}"); code_content = "N/A"
    else:
        for file in files_to_process:
            header = f"--- {file.filename} ---\n"; remaining_len = max_code_len - total_len - len(header)
            if remaining_len <= 0: code_str_parts.append("\n*... (Code context truncated)*"); logger.debug(f"Code context truncated for {func_name}"); break
            snippet = file.content[:remaining_len]; is_truncated = len(file.content) > remaining_len
            code_str_parts.append(header + snippet + ('...' if is_truncated else '')); total_len += len(header) + len(snippet)
            if total_len >= max_code_len:
                if not code_str_parts[-1].endswith("truncated)*"): code_str_parts.append("\n*... (Code context truncated)*")
                logger.debug(f"Code context max length for {func_name}"); break
        code_content = "\n".join(code_str_parts)
    # --- END CORRECTED LOOP ---
    class QualityAndCode(BaseModel):
        analysis: str; files: List[CodeFile]
    prompt = f"Refine QA report for '{state['project']}' based on feedback. Also apply *minor, non-functional* code improvements (docs, names) suggested by feedback to 'Passed Code' if simple, else return original files.\nQA Report:\n{state.get('quality_current_analysis','N/A')}\nPassed Code:\n{code_content}\nInstr:\n{instructions}\nAI FB:\n{state.get('quality_feedback','N/A')}\nHuman FB:\n{state.get('quality_human_feedback','N/A')}\n---\nOutput ONLY JSON (QualityAndCode model)."
    structured_llm = llm.with_structured_output(QualityAndCode) # Use LLM from state
    response = structured_llm.invoke(prompt)
    if not response or not isinstance(response, QualityAndCode) or not response.analysis:
        logger.error("Refinement of QA report failed/invalid."); raise ValueError("Did not produce expected result.")
    state["quality_current_analysis"] = response.analysis; state["final_code_files"] = response.files
    current_instructions = state.get("code_current", GeneratedCode(files=[],instructions="")).instructions
    state["code_current"] = GeneratedCode(files=response.files, instructions=current_instructions)
    state["messages"].append(AIMessage(content=f"Refined Quality Analysis Report:\n{state['quality_current_analysis']}"))
    logger.info("Refined Quality Analysis report.")
    return state

# save_final_quality_analysis remains unchanged
def save_final_quality_analysis(state: MainState) -> MainState:
    """Saves the final QA report and the associated final code snapshot."""
    state["final_quality_analysis"] = state.get("quality_current_analysis", "N/A")
    qa_dir, code_snap_dir, qa_path = None, None, None
    try:
        abs_project_folder = os.path.abspath(state["project_folder"])
        qa_dir = os.path.join(abs_project_folder, "8_quality_analysis"); os.makedirs(qa_dir, exist_ok=True)
        qa_path = os.path.join(qa_dir, "final_quality_analysis.md")
        with open(qa_path, "w", encoding="utf-8") as f: f.write(state["final_quality_analysis"])
        state["final_quality_analysis_path"] = qa_path; logger.info(f"Saved final QA report: {qa_path}")
        code_snap_dir = os.path.join(qa_dir, "final_code"); os.makedirs(code_snap_dir, exist_ok=True)
        state["final_code_folder"] = code_snap_dir
        files_to_save = state.get("final_code_files",[]); instructions = state.get("code_current", GeneratedCode(files=[],instructions="")).instructions
        if files_to_save:
            logger.info(f"Saving final code snapshot ({len(files_to_save)} files) to {code_snap_dir}")
            for file in files_to_save:
                fn=file.filename; content=file.content; safe_fn=os.path.basename(fn)
                if not safe_fn or ('/' in fn and '..' in fn) or ('\\' in fn and '..' in fn): logger.warning(f"Skip unsafe file: {fn}"); continue
                rel_path=fn.lstrip('/\\'); filepath=os.path.normpath(os.path.join(code_snap_dir, rel_path))
                if not os.path.abspath(filepath).startswith(os.path.abspath(code_snap_dir)): logger.warning(f"Skip traversal: {fn}"); continue
                try:
                    os.makedirs(os.path.dirname(filepath), exist_ok=True);
                    with open(filepath, "w", encoding="utf-8") as f: f.write(content)
                    logger.debug(f"Saved final code file: {filepath}")
                except OSError as path_err: logger.error(f"Path error saving final code '{filepath}': {path_err}")
                except Exception as write_err: logger.error(f"Error writing final code '{filepath}': {write_err}")
            try: # Save instructions
                instr_path = os.path.join(code_snap_dir, "instructions.md")
                with open(instr_path,"w",encoding="utf-8") as f: f.write(instructions)
                logger.debug(f"Saved final instructions: {instr_path}")
            except Exception as instr_err: logger.error(f"Error writing final instructions: {instr_err}")
        else: logger.warning("No final code files found to save with QA report.")
    except Exception as e:
        logger.error(f"Failed saving QA outputs: {e}", exc_info=True);
        state["final_quality_analysis_path"]=None; state["final_code_folder"]=None
    return state

# --- Deployment Cycle ---
@with_retry
def generate_initial_deployment(state: MainState, prefs: str) -> MainState:
    """Generates initial deployment plan."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    func_name = "generate_initial_deployment"
    final_code = state.get("final_code_files", [])
    if not final_code: logger.error(f"No final code for {func_name}"); raise ValueError("Final code missing.")
    instructions = state.get("code_current", GeneratedCode(files=[], instructions="")).instructions
    # --- CORRECTED LOOP ---
    code_str_parts = []; total_len = 0; max_code_len = 25000
    files_to_process = final_code
    if not files_to_process: logger.warning(f"No files for {func_name}"); code_context = "No code files."
    else:
        for file in files_to_process:
            is_key_file = ("requirements" in file.filename.lower() or "dockerfile" in file.filename.lower() or "main." in file.filename.lower() or "app." in file.filename.lower() or ".env" in file.filename.lower() or "config" in file.filename.lower())
            if is_key_file:
                header = f"--- {file.filename} ---\n"; remaining_len = max_code_len - total_len - len(header)
                if remaining_len <= 0: code_str_parts.append("\n*... (Key file context truncated)*"); logger.debug(f"Key file context truncated for {func_name}"); break
                snippet = file.content[:remaining_len]; is_truncated = len(file.content) > remaining_len
                code_str_parts.append(header + snippet + ('...' if is_truncated else '')); total_len += len(header) + len(snippet)
                if total_len >= max_code_len:
                    if not code_str_parts[-1].endswith("truncated)*"): code_str_parts.append("\n*... (Key file context truncated)*")
                    logger.debug(f"Key file context max length for {func_name}"); break
        code_context = "\n".join(code_str_parts) if code_str_parts else "No key deployment files found."
    # --- END CORRECTED LOOP ---
    prompt = f"Act as DevOps. Generate detailed deployment plan for '{state['project']}' ({state['coding_language']}). Base on user prefs, code structure (reqs, docker). Include commands, examples, verification steps.\nPrefs:\n{prefs}\nCode Context (Key Files):\n{code_context}\nInstr:\n{instructions}\n---"
    response = llm.invoke(prompt) # Use LLM from state
    deployment_plan = response.content.strip()
    state["deployment_current_process"] = deployment_plan
    state["messages"].append(AIMessage(content=f"Initial Deployment Plan:\n{deployment_plan}"))
    logger.info("Generated initial deployment plan.")
    return state

@with_retry
def generate_deployment_feedback(state: MainState) -> MainState:
    """Generates AI feedback on deployment plan."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    current_plan = state.get('deployment_current_process', 'N/A')
    if current_plan == 'N/A': logger.warning("No deploy plan to review."); state["deployment_feedback"] = "No plan."; return state
    prompt = f"Review Deployment Plan for '{state['project']}'. Assess clarity, correctness, completeness, security, alignment with practices.\nPlan:\n{current_plan}\n---\nSuggest improvements."
    response = llm.invoke(prompt) # Use LLM from state
    feedback = response.content.strip()
    state["deployment_feedback"] = feedback
    state["messages"].append(AIMessage(content=f"Deployment Plan Feedback:\n{feedback}"))
    logger.info("Generated feedback on deployment plan.")
    return state

@with_retry
def refine_deployment(state: MainState) -> MainState:
    """Refines deployment plan based on feedback."""
    llm = state.get('llm_instance')
    if not llm: raise ConnectionError("LLM instance not found in state.")
    if 'messages' not in state: state['messages'] = []
    func_name = "refine_deployment"
    current_plan = state.get('deployment_current_process', 'N/A'); ai_feedback = state.get('deployment_feedback', 'N/A'); human_feedback = state.get('deployment_human_feedback', 'N/A')
    # --- ADDED LOOP ---
    code_str_parts = []; total_len = 0; max_code_len = 25000
    final_code = state.get("final_code_files", []); instructions = state.get("code_current", GeneratedCode(files=[], instructions="")).instructions
    files_to_process = final_code
    if not files_to_process: logger.warning(f"No files for {func_name}"); code_context = "No code files."
    else:
        for file in files_to_process:
            is_key_file = ("requirements" in file.filename.lower() or "dockerfile" in file.filename.lower() or "main." in file.filename.lower() or "app." in file.filename.lower() or ".env" in file.filename.lower() or "config" in file.filename.lower())
            if is_key_file:
                header = f"--- {file.filename} ---\n"; remaining_len = max_code_len - total_len - len(header)
                if remaining_len <= 0: code_str_parts.append("\n*... (Key file context truncated)*"); logger.debug(f"Key file context truncated for {func_name}"); break
                snippet = file.content[:remaining_len]; is_truncated = len(file.content) > remaining_len
                code_str_parts.append(header + snippet + ('...' if is_truncated else '')); total_len += len(header) + len(snippet)
                if total_len >= max_code_len:
                    if not code_str_parts[-1].endswith("truncated)*"): code_str_parts.append("\n*... (Key file context truncated)*")
                    logger.debug(f"Key file context max length for {func_name}"); break
        code_context = "\n".join(code_str_parts) if code_str_parts else "No key files."
    # --- END ADDED LOOP ---
    prompt = f"Refine deployment plan for '{state['project']}'. Update based on feedback.\nCurrent Plan:\n{current_plan}\nCode Context:\n{code_context}\nInstr:\n{instructions}\nAI FB:\n{ai_feedback}\nHuman FB:\n{human_feedback}\n---\nGenerate updated plan."
    response = llm.invoke(prompt) # Use LLM from state
    refined_plan = response.content.strip()
    state["deployment_current_process"] = refined_plan
    state["messages"].append(AIMessage(content=f"Refined Deployment Plan:\n{refined_plan}"))
    logger.info("Refined deployment plan.")
    return state

# save_final_deployment_plan remains unchanged
def save_final_deployment_plan(state: MainState) -> MainState:
    """Saves the final deployment plan."""
    state["final_deployment_process"] = state.get("deployment_current_process", "No deployment plan generated.")
    filepath = None
    try:
        abs_project_folder = os.path.abspath(state["project_folder"])
        deploy_dir = os.path.join(abs_project_folder, "9_deployment"); os.makedirs(deploy_dir, exist_ok=True)
        filepath = os.path.join(deploy_dir, "final_deployment_plan.md")
        with open(filepath, "w", encoding="utf-8") as f: f.write(state["final_deployment_process"])
        logger.info(f"Saved final deployment plan: {filepath}")
    except Exception as e: logger.error(f"Failed save deployment plan: {e}", exc_info=True); filepath=None
    state["final_deployment_path"] = filepath
    return state

# --- END OF SDLC.py ---
