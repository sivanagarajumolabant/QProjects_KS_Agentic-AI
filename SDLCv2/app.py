# app.py
"""
Streamlit frontend application for orchestrating an AI-driven SDLC workflow.

This application manages the user interface, state transitions, and calls
backend logic functions defined in SDLC.py to generate project artifacts.
Includes cycle-based chat history display.
"""

# --- Standard Library Imports ---
import streamlit as st
import os
import shutil
import logging
from datetime import datetime
import time
import zipfile # Standard library zipfile

# --- Third-party Imports ---
import pydantic_core # For specific error checking

# --- Import core logic from SDLC.py ---
try:
    import SDLC
    from SDLC import (
        # State and Models
        MainState, GeneratedCode, PlantUMLCode, TestCase, CodeFile, TestCases,
        # Initialization function
        initialize_llm_clients,
        # Workflow Functions (Import all necessary functions)
        generate_questions, refine_prompt,
        generate_initial_user_stories, generate_user_story_feedback, refine_user_stories, save_final_user_story,
        generate_initial_product_review, generate_product_review_feedback, refine_product_review, save_final_product_review,
        generate_initial_design_doc, generate_design_doc_feedback, refine_design_doc, save_final_design_doc,
        select_uml_diagrams, generate_initial_uml_codes, generate_uml_feedback, refine_uml_codes, save_final_uml_diagrams,
        generate_initial_code, web_search_code, generate_code_feedback, refine_code,
        code_review, security_check, refine_code_with_reviews, save_review_security_outputs,
        generate_initial_test_cases, generate_test_cases_feedback, refine_test_cases_and_code, save_testing_outputs,
        generate_initial_quality_analysis, generate_quality_feedback, refine_quality_and_code, save_final_quality_analysis,
        generate_initial_deployment, generate_deployment_feedback, refine_deployment, save_final_deployment_plan,
        # Message Types
        HumanMessage, AIMessage
    )
    logging.info("Successfully imported components from SDLC.py.")
except ImportError as e:
    st.error(f"Import Error: {e}. Critical file 'SDLC.py' not found or contains errors.")
    logging.critical(f"Failed to import SDLC.py: {e}", exc_info=True)
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred during import from SDLC: {e}")
    logging.critical(f"Unexpected error during import from SDLC: {e}", exc_info=True)
    st.stop()

# --- Application Setup ---
st.set_page_config(layout="wide", page_title="AI SDLC Workflow")
logger = logging.getLogger(__name__)
# Ensure logger is configured
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Streamlit app logger configured.")

# --- Constants for Configuration ---
# Define available providers and their models
AVAILABLE_MODELS = {
    "Google": [
        "gemini-2.0-flash", "gemini-1.5-pro-latest", "gemini-1.5-flash-latest",
        "gemini-1.0-pro", "gemini-1.0-flash", "gemini-2.5-pro-exp-03-25", 
    ],
    "OpenAI": [
        "gpt-4o-mini", "gpt-4o-mini-2024-07-18",
        "gpt-4o", "gpt-4o-2024-08-06",
        "o1-mini", "o1-mini-2024-09-12",
        "o3-mini", "o3-mini-2025-01-31",
    ],
    "Groq": [
        "llama3-8b-8192", "llama3-70b-8192", "llama-3.1-8b-instant",
        "llama-3.2-1b-preview", "llama-3.2-3b-preview", "llama-3.3-70b-specdec",
        "llama-3.3-70b-versatile", "mistral-saba-24b", "gemma2-9b-it",
        "deepseek-r1-distill-llama-70b", "deepseek-r1-distill-qwen-32b",
        "qwen-2.5-32b", "qwen-2.5-coder-32b", "qwen-qwq-32b",
        "mixtral-8x7b-32768",
    ],

    "Anthropic": [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-5-haiku-latest",
        "claude-3-5-sonnet-latest",
        "claude-3-7-sonnet-latest"
    ],
    "xAI": [
        "grok-1",
        "grok-2-latest",
        "grok-3",
        "grok-3-mini"
    ]
}
LLM_PROVIDERS = list(AVAILABLE_MODELS.keys())

# --- Define Cycle Order and Stage-to-Cycle Mapping ---
CYCLE_ORDER = [
    "Requirements", "User Story", "Product Review", "Design", "UML",
    "Code Generation", "Review & Security", "Testing", "Quality Analysis", "Deployment"
]
STAGE_TO_CYCLE = {
    "initial_setup": "Requirements",
    "run_generate_questions": "Requirements",
    "collect_answers": "Requirements",
    "run_refine_prompt": "Requirements",
    "run_generate_initial_user_stories": "User Story",
    "run_generate_user_story_feedback": "User Story",
    "collect_user_story_human_feedback": "User Story",
    "run_refine_user_stories": "User Story",
    "collect_user_story_decision": "User Story",
    "run_generate_initial_product_review": "Product Review",
    "run_generate_product_review_feedback": "Product Review",
    "collect_product_review_human_feedback": "Product Review",
    "run_refine_product_review": "Product Review",
    "collect_product_review_decision": "Product Review",
    "run_generate_initial_design_doc": "Design",
    "run_generate_design_doc_feedback": "Design",
    "collect_design_doc_human_feedback": "Design",
    "run_refine_design_doc": "Design",
    "collect_design_doc_decision": "Design",
    "run_select_uml_diagrams": "UML",
    "run_generate_initial_uml_codes": "UML",
    "run_generate_uml_feedback": "UML",
    "collect_uml_human_feedback": "UML",
    "run_refine_uml_codes": "UML",
    "collect_uml_decision": "UML",
    "run_generate_initial_code": "Code Generation",
    "collect_code_human_input": "Code Generation",
    "run_web_search_code": "Code Generation",
    "run_generate_code_feedback": "Code Generation",
    "collect_code_human_feedback": "Code Generation",
    "run_refine_code": "Code Generation",
    "collect_code_decision": "Code Generation",
    "run_code_review": "Review & Security",
    "run_security_check": "Review & Security",
    "merge_review_security_feedback": "Review & Security", # Stage name from prompt
    "collect_review_security_human_feedback": "Review & Security", # Hypothetical, check if needed
    "run_refine_code_with_reviews": "Review & Security",
    "collect_review_security_decision": "Review & Security",
    "run_generate_initial_test_cases": "Testing",
    "run_generate_test_cases_feedback": "Testing",
    "collect_test_cases_human_feedback": "Testing",
    "run_refine_test_cases_and_code": "Testing",
    "run_save_testing_outputs": "Testing",
    "run_generate_initial_quality_analysis": "Quality Analysis",
    "run_generate_quality_feedback": "Quality Analysis",
    "collect_quality_human_feedback": "Quality Analysis",
    "run_refine_quality_and_code": "Quality Analysis",
    "collect_quality_decision": "Quality Analysis",
    "generate_initial_deployment": "Deployment", # Stage for form display
    "run_generate_initial_deployment": "Deployment", # Stage for processing
    "run_generate_deployment_feedback": "Deployment",
    "collect_deployment_human_feedback": "Deployment",
    "run_refine_deployment": "Deployment",
    "collect_deployment_decision": "Deployment",
    "END": "END" # Final stage marker
}

# --- Helper Functions ---

def initialize_state():
    """Initializes or resets the Streamlit session state."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_project_folder = f"ai_sdlc_project_{timestamp}"

    # --- Existing Clear and Basic Init ---
    st.session_state.clear() # Clear all session state keys
    st.session_state.stage = "initial_setup"
    st.session_state.workflow_state = {} # Master state dictionary
    st.session_state.user_input = "" # Temporary storage for text area
    st.session_state.display_content = "Welcome! Please configure API keys and project details to start." # Main display area content
    st.session_state.project_folder_base = default_project_folder # Base folder name default
    st.session_state.current_prefs = "" # For deployment preferences
    # ZIP file paths for download buttons
    st.session_state.zip_path = None # Full project zip
    st.session_state.review_code_zip_path = None
    st.session_state.testing_code_zip_path = None
    st.session_state.final_code_zip_path = None
    # Configuration state
    st.session_state.config_applied = False
    st.session_state.selected_provider = LLM_PROVIDERS[0]
    st.session_state.selected_model = AVAILABLE_MODELS[LLM_PROVIDERS[0]][0]
    st.session_state.llm_api_key = ""
    st.session_state.tavily_api_key = ""
    st.session_state.llm_instance = None
    st.session_state.tavily_instance = None
    # Chat history state for current cycle display
    st.session_state.current_cycle_messages = [] # List to hold messages for display in the current cycle
    st.session_state.previous_major_cycle = None # Track the previous cycle to detect changes

    # --- >>> ADDED: Initialize Form Default Keys Directly Here <<< ---
    # This ensures the keys exist when the initial setup form is rendered.
    st.session_state.proj_name_default = "Multi-feature Web Application Example\n- User Authentication\n- Task Management\n- Reporting"
    st.session_state.proj_cat_default = "Web Development\n- Full Stack"
    st.session_state.proj_subcat_default = "Productivity Tool\n- Internal Business Application"
    st.session_state.proj_lang_default = "Python (Flask Backend)\nJavaScript (React Frontend)\nDocker"
    st.session_state.min_iter_default = 2
    # --- >>> END ADDED BLOCK <<< ---

    # --- Existing Initialization for MD/PDF Paths ---
    st.session_state.refined_prompt_path = None
    st.session_state.refined_prompt_pdf_path = None
    st.session_state.final_user_story_path = None
    st.session_state.final_user_story_pdf_path = None
    st.session_state.final_product_review_path = None
    st.session_state.final_product_review_pdf_path = None
    st.session_state.final_design_document_path = None
    st.session_state.final_design_document_pdf_path = None
    st.session_state.final_quality_analysis_path = None
    st.session_state.final_quality_analysis_pdf_path = None
    st.session_state.final_deployment_path = None
    st.session_state.final_deployment_pdf_path = None
    # --- END ADDED --- # This comment was slightly misplaced, path init is correct

    # --- Existing Initialization for Snapshot Paths ---
    st.session_state.snapshot_path_codegen_initial = None
    st.session_state.snapshot_path_codegen_refined = None
    st.session_state.snapshot_path_review_refined = None
    st.session_state.snapshot_path_testing_refined = None
    st.session_state.snapshot_path_qa_polished = None
    # Keep final folder paths (might point to last snapshot or dedicated folder)
    st.session_state.review_code_snapshot_folder = None # Points to post_review snapshot
    st.session_state.testing_passed_code_folder = None # Points to snapshot saved by save_testing_outputs
    st.session_state.final_code_folder = None # Points to post_qa snapshot
    # --- END ADDED/MODIFIED --- # This comment was slightly misplaced, path init is correct

    logger.info("Streamlit session state initialized/reset including form defaults, PDF, and Snapshot paths.") # Keep the original log message or update if desired


def update_display(new_content: str):
    """Updates the main display area content in the session state."""
    st.session_state.display_content = new_content
    logger.debug("Main display content updated.")

def create_download_button(file_path: str, label: str, mime: str, key_suffix: str, help_text: str = ""):
    """Creates a download button for a given file path if it exists and is valid."""
    if not file_path or not isinstance(file_path, str):
        # logger.debug(f"Download button skipped for '{label}': Invalid path ({file_path}).")
        return # Skip if path is invalid

    abs_file_path = os.path.abspath(file_path)
    if os.path.exists(abs_file_path) and os.path.isfile(abs_file_path):
        try:
            with open(abs_file_path, "rb") as fp:
                # Sanitize label for key generation, keep it simple
                safe_label_part = "".join(c for c in label if c.isalnum() or c in ['_']).lower()[:15]
                button_key = f"dl_btn_{key_suffix}_{safe_label_part}" # Unique key per button
                st.download_button(
                    label=f"Download {label}",
                    data=fp,
                    file_name=os.path.basename(abs_file_path),
                    mime=mime,
                    key=button_key,
                    help=help_text or f"Download the {label} file."
                )
        except FileNotFoundError:
            # This shouldn't happen if os.path.exists passed, but handle defensively
            logger.warning(f"File disappeared before download button creation: {abs_file_path}")
        except Exception as e:
            logger.error(f"Error preparing download button for '{abs_file_path}': {e}", exc_info=True)
            # Show a less intrusive warning in the UI
            st.warning(f"Could not create download for {label}. Error: {e}", icon="⚠️")
    # else: logger.debug(f"Download button skipped for '{label}': File not found or not a file ({abs_file_path}).")


def create_zip_and_download_button(folder_path_key: str, zip_path_key: str, zip_basename: str, button_label_prefix: str, sidebar_context):
    """
    Creates a button to generate a ZIP archive of a specified folder
    and provides a download button for the generated ZIP file.

    Args:
        folder_path_key: Key in workflow_state holding the path to the folder to zip.
        zip_path_key: Key in session_state where the path to the created zip file will be stored.
        zip_basename: The base name for the output zip file (without .zip).
        button_label_prefix: Prefix for the button labels (e.g., "Review Stage Code").
        sidebar_context: The Streamlit container (e.g., st.sidebar) where buttons are placed.
    """
    folder_path = st.session_state.workflow_state.get(folder_path_key)
    abs_folder_path = os.path.abspath(folder_path) if folder_path and isinstance(folder_path, str) else None

    if abs_folder_path and os.path.exists(abs_folder_path) and os.path.isdir(abs_folder_path):
        # --- Button to Generate ZIP ---
        zip_label = f"Generate & Download {button_label_prefix} ZIP"
        existing_zip = st.session_state.get(zip_path_key)
        if existing_zip and os.path.exists(existing_zip):
            zip_label = f"Download {button_label_prefix} ZIP" # Change label if ZIP exists

        # Use a descriptive and unique key for the generation button
        zip_gen_key = f"zip_gen_btn_{zip_path_key}"
        if sidebar_context.button(zip_label, key=zip_gen_key, help=f"Package the {button_label_prefix} folder into a downloadable ZIP file."):
            with st.spinner(f"Creating {button_label_prefix} archive..."):
                try:
                    # Define output directory (same level as project folder) and base name
                    out_dir = os.path.dirname(abs_folder_path) # Place zip next to the folder being zipped
                    archive_base = os.path.join(out_dir, zip_basename) # e.g., ../ai_sdlc_project_xxx/code_snapshot_review

                    # Define the root directory and the directory to archive relative to the root
                    root_dir = os.path.dirname(abs_folder_path) # The parent directory of the folder to zip
                    base_dir = os.path.basename(abs_folder_path) # The name of the folder to zip

                    logger.info(f"Zipping: base_name='{archive_base}', format='zip', root_dir='{root_dir}', base_dir='{base_dir}'")

                    # Construct the expected output zip file path
                    zip_file_path = archive_base + ".zip"

                    # Remove old zip file if it exists to avoid conflicts
                    if os.path.exists(zip_file_path):
                        try:
                            os.remove(zip_file_path)
                            logger.info(f"Removed existing ZIP: {zip_file_path}")
                        except Exception as del_e:
                            logger.warning(f"Could not remove existing ZIP {zip_file_path}: {del_e}")

                    # Create the archive
                    archive_path = shutil.make_archive(
                        base_name=archive_base,
                        format='zip',
                        root_dir=root_dir,
                        base_dir=base_dir
                    )

                    # Verify the archive was created
                    if not os.path.exists(archive_path):
                        raise OSError(f"ZIP archive creation failed: File not found at {archive_path}")

                    # Store the path to the created zip file in session state
                    st.session_state[zip_path_key] = archive_path
                    st.success(f"{button_label_prefix} ZIP created successfully!")
                    logger.info(f"Successfully created ZIP archive: {archive_path}")
                    st.rerun() # Rerun to update the UI and show the download button

                except Exception as e:
                    sidebar_context.error(f"ZIP Creation Error: {e}")
                    logger.error(f"ZIP creation failed for folder '{abs_folder_path}': {e}", exc_info=True)

        # --- Download Button for Existing ZIP ---
        generated_zip = st.session_state.get(zip_path_key)
        if generated_zip and os.path.exists(generated_zip):
             try:
                 with open(generated_zip, "rb") as fp:
                     # Use a descriptive and unique key for the download button
                     safe_prefix = "".join(c for c in button_label_prefix if c.isalnum()).lower()[:10]
                     dl_key = f"dl_zip_btn_{zip_path_key}_{safe_prefix}"
                     sidebar_context.download_button(
                         label=f"Download {button_label_prefix} ZIP",
                         data=fp,
                         file_name=os.path.basename(generated_zip),
                         mime="application/zip",
                         key=dl_key,
                         help=f"Download the generated {button_label_prefix} ZIP archive."
                     )
             except Exception as e:
                 sidebar_context.warning(f"Error reading ZIP file for download: {e}")
                 logger.error(f"Error reading ZIP file {generated_zip} for download: {e}", exc_info=True)
    # else: logger.debug(f"ZIP button skipped for '{button_label_prefix}': Folder path invalid or not found ({folder_path}).")

# --- Initialize State if First Run ---
if 'stage' not in st.session_state:
    initialize_state()

# --- Sidebar UI ---
with st.sidebar:
    st.header("AI SDLC Orchestrator")
    st.caption("Automated workflow from requirements to deployment.")
    st.divider()

    # --- Configuration Expander ---
    with st.expander("Configuration", expanded=not st.session_state.get('config_applied', False)):
        st.subheader("LLM & API Keys")

        # LLM Provider Selection
        selected_provider = st.selectbox(
            "Select LLM Provider",
            options=LLM_PROVIDERS,
            key="selected_provider", # Keep existing key for state consistency
            index=LLM_PROVIDERS.index(st.session_state.selected_provider) if st.session_state.selected_provider in LLM_PROVIDERS else 0,
            help="Choose the primary Large Language Model provider."
        )

        # Dynamically update available models based on provider
        available_models = AVAILABLE_MODELS.get(selected_provider, ["N/A"])
        current_model_selection = st.session_state.selected_model
        model_index = available_models.index(current_model_selection) if current_model_selection in available_models else 0

        selected_model = st.selectbox(
            f"Select Model ({selected_provider})",
            options=available_models,
            key="selected_model", # Keep existing key
            index=model_index,
            help=f"Choose a specific model from {selected_provider}."
        )

        # API Key Inputs
        llm_api_key_input = st.text_input(
            f"{selected_provider} API Key",
            type="password",
            key="llm_api_key_input", # Keep existing key
            help=f"Enter your API key for the selected {selected_provider} provider.",
            value=st.session_state.get("llm_api_key", "") # Pre-fill if exists
        )

        tavily_api_key_input = st.text_input(
            "Tavily API Key (Optional)",
            type="password",
            key="tavily_api_key_input", # Keep existing key
            help="Enter your Tavily API key for enabling web search functionality.",
            value=st.session_state.get("tavily_api_key", "") # Pre-fill if exists
        )

        # Apply Configuration Button
        if st.button("Apply Configuration", key="apply_config_button"): # Changed key slightly to avoid potential conflicts if previous runs errored strangely
            with st.spinner("Initializing LLM and Tavily clients..."):
                # Store keys from inputs into session state
                st.session_state.llm_api_key = llm_api_key_input
                st.session_state.tavily_api_key = tavily_api_key_input

                # Attempt to initialize clients using the backend function
                llm_inst, tav_inst, error_msg = SDLC.initialize_llm_clients(
                    provider=st.session_state.selected_provider,
                    model_name=st.session_state.selected_model,
                    llm_api_key=st.session_state.llm_api_key,
                    tavily_api_key=st.session_state.tavily_api_key
                )

                # Update state based on initialization result
                if llm_inst:
                    st.session_state.llm_instance = llm_inst
                    st.session_state.tavily_instance = tav_inst
                    st.session_state.config_applied = True
                    st.success("Configuration applied successfully!")
                    logger.info(f"LLM ({selected_provider}/{selected_model}) and Tavily clients configured via UI.")
                    time.sleep(1) # Brief pause for user to see success message
                    st.rerun() # Rerun to potentially collapse expander and enable main workflow
                else:
                    st.session_state.config_applied = False
                    st.session_state.llm_instance = None
                    st.session_state.tavily_instance = None
                    error_display = f"Configuration Failed: {error_msg or 'An unknown error occurred.'}"
                    st.error(error_display)
                    logger.error(error_display)

    st.divider()

    # --- Downloads Section ---
    st.header("Downloads")
    st.caption("Access generated artifacts and code snapshots.")

    # --- MODIFIED: Document Downloads (MD and PDF) ---
    st.markdown("---")
    st.subheader("Documents") # Combined header

    # Refined Prompt (Appears after Q&A cycle is complete)
    st.markdown("**Requirements Cycle:**") # Header for this artifact
    create_download_button(st.session_state.workflow_state.get("refined_prompt_path"), "Refined Prompt (MD)", "text/markdown", "refined_prompt_md", help_text="The final prompt generated after Q&A.")
    create_download_button(st.session_state.workflow_state.get("refined_prompt_pdf_path"), "Refined Prompt (PDF)", "application/pdf", "refined_prompt_pdf", help_text="PDF version of the refined prompt.")
    st.markdown("---") # Separator

    # User Story
    st.markdown("**User Story Cycle:**")
    create_download_button(st.session_state.workflow_state.get("final_user_story_path"), "User Story (MD)", "text/markdown", "final_us_md")
    create_download_button(st.session_state.workflow_state.get("final_user_story_pdf_path"), "User Story (PDF)", "application/pdf", "final_us_pdf")
    st.markdown("---")

    # Product Review
    st.markdown("**Product Review Cycle:**")
    create_download_button(st.session_state.workflow_state.get("final_product_review_path"), "Product Review (MD)", "text/markdown", "final_pr_md")
    create_download_button(st.session_state.workflow_state.get("final_product_review_pdf_path"), "Product Review (PDF)", "application/pdf", "final_pr_pdf")
    st.markdown("---")

    # Design Document
    st.markdown("**Design Cycle:**")
    create_download_button(st.session_state.workflow_state.get("final_design_document_path"), "Design Document (MD)", "text/markdown", "final_dd_md")
    create_download_button(st.session_state.workflow_state.get("final_design_document_pdf_path"), "Design Document (PDF)", "application/pdf", "final_dd_pdf")
    st.markdown("---")

    # QA Report
    st.markdown("**Quality Analysis Cycle:**")
    create_download_button(st.session_state.workflow_state.get("final_quality_analysis_path"), "QA Report (MD)", "text/markdown", "final_qa_md")
    create_download_button(st.session_state.workflow_state.get("final_quality_analysis_pdf_path"), "QA Report (PDF)", "application/pdf", "final_qa_pdf")
    st.markdown("---")

    # Deployment Plan
    st.markdown("**Deployment Cycle:**")
    create_download_button(st.session_state.workflow_state.get("final_deployment_path"), "Deployment Plan (MD)", "text/markdown", "final_deploy_md")
    create_download_button(st.session_state.workflow_state.get("final_deployment_pdf_path"), "Deployment Plan (PDF)", "application/pdf", "final_deploy_pdf")
    # --- END MODIFIED Document Downloads ---

    # UML Diagram Downloads
    st.markdown("---")
    st.subheader("UML Diagrams")
    uml_png_paths = st.session_state.workflow_state.get("final_uml_png_paths", [])
    uml_folder = st.session_state.workflow_state.get("final_uml_diagram_folder")

    if uml_png_paths:
        st.caption("Download generated PNG images:")
        # Create download buttons for each generated PNG
        for i, png_path in enumerate(uml_png_paths):
            # Attempt to create a meaningful label from the filename
            try:
                base_name = os.path.basename(png_path)
                # Assumes format like 'diagram_01_class_diagram.png'
                label_parts = base_name.split('_')[2:] # Get parts after 'diagram_xx_'
                label = ' '.join(label_parts).replace('.png', '').replace('_', ' ').title()
                if not label: label = f"Diagram {i+1}" # Fallback label
            except Exception:
                label = f"Diagram {i+1}" # Generic fallback

            create_download_button(png_path, f"UML: {label}", "image/png", f"uml_png_{i}")
    elif uml_folder and os.path.exists(uml_folder):
        # Indicates UML stage ran but PNGs weren't generated or found
        st.caption("*No PNG diagrams available for download (check PlantUML setup/server). Puml files might be available in the full project ZIP.*")
    else:
        # Indicates UML stage hasn't run or failed before saving
        st.caption("*UML diagrams have not been generated yet.*")

 # --- MODIFIED: Code Snapshot Downloads (ZIP) ---
    st.markdown("---")
    st.subheader("Code Snapshots (ZIP)")
    st.caption("Download code versions from various stages.")

    # Code Generation Cycle Snapshots
    st.markdown("**Code Generation Cycle:**")
    create_zip_and_download_button(
        folder_path_key="snapshot_path_codegen_initial", # Use the new state key
        zip_path_key="zip_path_cg_initial", # Unique key for session state zip path
        zip_basename="snapshot_codegen_initial",
        button_label_prefix="Initial Code",
        sidebar_context=st.sidebar
    )
    create_zip_and_download_button(
        folder_path_key="snapshot_path_codegen_refined", # Use the new state key
        zip_path_key="zip_path_cg_refined", # Unique key
        zip_basename="snapshot_codegen_refined",
        button_label_prefix="Refined Code (Latest)", # Label indicates latest
        sidebar_context=st.sidebar
    )
    st.markdown("---")

    # Review & Security Cycle Snapshot
    st.markdown("**Review & Security Cycle:**")
    create_zip_and_download_button(
        folder_path_key="snapshot_path_review_refined", # Use the new state key
        zip_path_key="zip_path_review_refined", # Unique key
        zip_basename="snapshot_review_refined",
        button_label_prefix="Post-Review Code",
        sidebar_context=st.sidebar
    )
    st.markdown("---")

    # Testing Cycle Snapshots
    st.markdown("**Testing Cycle:**")
    create_zip_and_download_button(
        folder_path_key="snapshot_path_testing_refined", # Use the new state key for failed refinement
        zip_path_key="zip_path_testing_refined", # Unique key
        zip_basename="snapshot_testing_refined",
        button_label_prefix="Post-Failure Refined Code (Latest)",
        sidebar_context=st.sidebar
    )
    create_zip_and_download_button(
        folder_path_key="testing_passed_code_folder", # Keep the one saved on PASS
        zip_path_key="zip_path_testing_passed", # Unique key
        zip_basename="snapshot_testing_passed",
        button_label_prefix="Passed Testing Code",
        sidebar_context=st.sidebar
    )
    st.markdown("---")

    # Quality Analysis Cycle Snapshot (Final Code)
    st.markdown("**Quality Analysis Cycle:**")
    create_zip_and_download_button(
        folder_path_key="snapshot_path_qa_polished", # Use the new state key (points to final code)
        zip_path_key="zip_path_qa_polished", # Unique key
        zip_basename="snapshot_qa_polished_final",
        button_label_prefix="Final Polished Code",
        sidebar_context=st.sidebar
    )
    # --- END MODIFIED Code Snapshots ---

    st.divider()

    # --- Full Project ZIP (only appears at the end) ---
    if st.session_state.stage == "END":
        st.markdown("**Full Project Archive**")
        st.caption("Download all generated artifacts and code snapshots in a single ZIP.")
        proj_folder = st.session_state.workflow_state.get("project_folder")
        abs_proj = os.path.abspath(proj_folder) if proj_folder and isinstance(proj_folder, str) else None

        if abs_proj and os.path.isdir(abs_proj):
            zip_label = "Generate & Download Full Project ZIP"
            if st.session_state.get("zip_path") and os.path.exists(st.session_state.zip_path):
                zip_label = "Download Full Project ZIP" # Change label if already generated

            if st.sidebar.button(zip_label, key="zip_gen_final_project_btn"): # Unique key
                with st.spinner("Creating full project archive..."):
                    try:
                        # Use the project_folder_base which is set at init and guaranteed unique
                        zip_base = os.path.abspath(st.session_state.project_folder_base)
                        out_dir = os.path.dirname(zip_base) # Place zip in parent dir
                        os.makedirs(out_dir, exist_ok=True)

                        root_dir = os.path.dirname(abs_proj) # Parent of the project folder
                        base_dir = os.path.basename(abs_proj) # Name of the project folder

                        logger.info(f"Zipping full project: base_name='{zip_base}', format='zip', root_dir='{root_dir}', base_dir='{base_dir}'")
                        zip_file_path = zip_base + ".zip"

                        # Remove old zip if exists
                        if os.path.exists(zip_file_path):
                            try:
                                os.remove(zip_file_path)
                                logger.info(f"Removed old final project ZIP: {zip_file_path}")
                            except Exception as del_e:
                                logger.warning(f"Could not remove old final project ZIP {zip_file_path}: {del_e}")

                        # Create the archive
                        archive_path = shutil.make_archive(
                            base_name=zip_base,
                            format='zip',
                            root_dir=root_dir,
                            base_dir=base_dir
                        )

                        # Verify creation
                        if not os.path.exists(archive_path):
                            raise OSError(f"Final project ZIP creation failed: File not found at {archive_path}")

                        st.session_state.zip_path = archive_path # Store path
                        st.success(f"Full project ZIP created: {os.path.basename(archive_path)}")
                        st.rerun() # Update UI

                    except Exception as e:
                        st.sidebar.error(f"Final Project ZIP Error: {e}")
                        logger.error(f"Final project ZIP creation failed: {e}", exc_info=True)

            # Provide download button if zip exists
            if st.session_state.get("zip_path") and os.path.exists(st.session_state.zip_path):
                 try:
                     with open(st.session_state.zip_path, "rb") as fp:
                         st.sidebar.download_button(
                             label="Download Full Project ZIP",
                             data=fp,
                             file_name=os.path.basename(st.session_state.zip_path),
                             mime="application/zip",
                             key="dl_zip_final_project_btn" # Unique key
                            )
                 except Exception as read_e:
                     st.sidebar.warning(f"Error reading final project ZIP: {read_e}")
                     logger.error(f"Error reading final project ZIP {st.session_state.zip_path}: {read_e}", exc_info=True)
        elif proj_folder:
            st.sidebar.warning(f"Project folder '{proj_folder}' not found for final ZIP.")
        else:
            st.sidebar.caption("*Project folder not yet defined.*")

    st.divider()

    # --- Restart Button ---
    if st.sidebar.button("Restart Workflow", key="restart_workflow_button", help="Clear all progress and configuration, then start over."):
        # Optional: Add confirmation dialog here if desired
        logger.info("Workflow restart requested by user.")
        # Clean up project directory if it exists
        proj_folder_to_delete = st.session_state.workflow_state.get("project_folder")
        if proj_folder_to_delete and os.path.isdir(proj_folder_to_delete):
             try:
                 shutil.rmtree(proj_folder_to_delete)
                 logger.info(f"Removed project folder on restart: {proj_folder_to_delete}")
             except Exception as e:
                 logger.warning(f"Could not remove project folder '{proj_folder_to_delete}' on restart: {e}")
        initialize_state()
        st.rerun()

# ==============================================================================
# --- Main Layout Area ---
# ==============================================================================

main_col, indicator_col = st.columns([4, 1]) # Main content area, Cycle indicator sidebar

# --- Cycle Change Detection and History Reset ---
current_stage = st.session_state.stage
current_major_cycle = STAGE_TO_CYCLE.get(current_stage, "Unknown")

# Initialize previous cycle tracker if it doesn't exist
if 'previous_major_cycle' not in st.session_state:
     st.session_state.previous_major_cycle = current_major_cycle

# Check if the cycle has changed since the last run
if st.session_state.previous_major_cycle != current_major_cycle and current_major_cycle != "Unknown":
    logger.info(f"Detected cycle change: '{st.session_state.previous_major_cycle}' -> '{current_major_cycle}'. Clearing current cycle message display.")
    st.session_state.current_cycle_messages = [] # Reset the list for the new cycle
    st.session_state.previous_major_cycle = current_major_cycle # Update the tracker

# --- Main Column Content ---
with main_col:
    # Display current stage and cycle title
    stage_display_name = current_stage.replace('_', ' ').title()
    if current_stage == "END":
        st.header("🏁 Workflow Complete")
    else:
        st.header(f"Cycle: {current_major_cycle} | Stage: {stage_display_name}")

    # --- Chat History Display Area (Current Cycle Only) ---
    st.markdown("### Current Cycle Interaction History")
    # Get the messages specifically for the current cycle display
    current_cycle_messages_list = st.session_state.get("current_cycle_messages", [])

    # Use a container with fixed height for scrollable chat
    chat_container = st.container(height=350, border=True)
    with chat_container:
        if not current_cycle_messages_list:
            st.caption("No interactions recorded for this cycle yet.")
        else:
            # Iterate through messages stored for the current cycle display
            for msg in current_cycle_messages_list:
                # Determine role based on message type
                if isinstance(msg, AIMessage):
                    role = "assistant"
                    avatar = "🤖"
                elif isinstance(msg, HumanMessage):
                    role = "user"
                    avatar = "🧑‍💻"
                else:
                    role = "system" # Or handle other types if necessary
                    avatar = "⚙️"

                with st.chat_message(role, avatar=avatar):
                    # Display message content using markdown
                    # Ensure content is string; handle potential non-string data safely
                    content_display = str(msg.content) if msg.content is not None else "[No Content]"
                    st.markdown(content_display, unsafe_allow_html=False) # Security best practice

    st.divider() # Visual separator

    # --- Current Task / Output Display ---
    st.markdown("### Current Task / Latest Output:")
    display_area = st.container(border=True) # Add border for visual separation
    with display_area:
        # Get content safely, default to a clear message
        display_content_md = st.session_state.get("display_content", "Awaiting next step...")
        # Ensure it's a string before displaying
        if not isinstance(display_content_md, str):
            display_content_md = str(display_content_md)
        st.markdown(display_content_md, unsafe_allow_html=False) # Disable HTML rendering

    st.divider() # Visual separator

    # --- Input / Decision Widgets ---
    # Only show workflow UI elements if configuration is applied
    if not st.session_state.get('config_applied', False):
        if st.session_state.stage != "initial_setup": # Don't show warning during initial setup itself
            st.warning("👈 Please apply LLM & API Key configuration in the sidebar to start the workflow.")
    else:
        # Determine which UI elements to show based on the current stage
        current_stage_ui = st.session_state.stage # Use a distinct variable for clarity

        input_needed_stages = {
            "collect_answers", "collect_user_story_human_feedback",
            "collect_product_review_human_feedback", "collect_design_doc_human_feedback",
            "collect_uml_human_feedback", "collect_code_human_input",
            "collect_code_human_feedback", "merge_review_security_feedback", # This stage now collects feedback
            "collect_quality_human_feedback", "collect_deployment_human_feedback"
        }
        decision_needed_stages = {
            "collect_user_story_decision", "collect_product_review_decision",
            "collect_design_doc_decision", "collect_uml_decision", "collect_code_decision",
            "collect_review_security_decision", "collect_quality_decision",
            "collect_deployment_decision"
        }

        show_initial_setup_form = (current_stage_ui == "initial_setup")
        show_deployment_prefs_form = (current_stage_ui == "generate_initial_deployment")
        show_input_box = current_stage_ui in input_needed_stages
        show_test_feedback_area = (current_stage_ui == "collect_test_cases_human_feedback")
        show_decision_buttons = current_stage_ui in decision_needed_stages

        # --- Initial Setup Form ---
        if show_initial_setup_form:
            with st.form("initial_project_setup_form"): # Descriptive key
                st.markdown("### Project Configuration")
                st.info("Define the initial parameters for your software project.")

                # --- Project Folder (Standard Input) ---
                proj_folder = st.text_input(
                    "Project Folder Name",
                    value=st.session_state.project_folder_base,
                    key="proj_folder_input",
                    help="Directory name for saved outputs. Use valid filesystem characters (no spaces/special chars like /\\:*?\"<>| recommended)."
                )

                # --- Project Description (Text Area with Height) ---
                proj_name = st.text_area( # MODIFIED: Use text_area
                    "Project Description",
                    value=st.session_state.proj_name_default, # Use a potentially multi-line default
                    key="proj_name_input",
                    height=300, # MODIFIED: Set height
                    help="A detailed description of the project's purpose, features, and goals."
                )

                # --- Category (Text Area with Height) ---
                proj_cat = st.text_area( # MODIFIED: Use text_area
                    "Category",
                    value=st.session_state.proj_cat_default, # Use a potentially multi-line default
                    key="proj_cat_input",
                    height=150, # MODIFIED: Set height
                    help="Broad category (e.g., Web Development, Data Science). Can be multi-line if needed."
                )

                # --- Subcategory (Text Area with Height) ---
                proj_subcat = st.text_area( # MODIFIED: Use text_area
                    "Subcategory",
                    value=st.session_state.proj_subcat_default, # Use a potentially multi-line default
                    key="proj_subcat_input",
                    height=150, # MODIFIED: Set height
                    help="More specific classification (e.g., API, Full-Stack App). Can be multi-line."
                )

                # --- Coding Language (Text Area with Height) ---
                proj_lang = st.text_area( # MODIFIED: Use text_area
                    "Coding Language(s) / Tech Stack",
                    value=st.session_state.proj_lang_default, # Use a potentially multi-line default
                    key="proj_lang_input",
                    height=150, # MODIFIED: Set height
                    help="Primary language(s) and key technologies (e.g., Python, React, Docker). Can be multi-line."
                )

                # --- Min Iterations (Standard Number Input) ---
                min_iter = st.number_input(
                    "Min Q&A Rounds",
                    min_value=1, max_value=10, # Increased max slightly
                    value=st.session_state.min_iter_default,
                    key="min_iter_input",
                    help="Minimum required rounds of questions and answers for requirements gathering."
                )

                # --- Submit Button ---
                submitted = st.form_submit_button("Start Workflow")

                # --- Post-Submission Logic (Your existing code) ---
                if submitted:
                    # Validation checks
                    error_messages = []
                    # Trim whitespace from inputs before validation
                    proj_folder = proj_folder.strip()
                    proj_name = proj_name.strip()
                    proj_cat = proj_cat.strip()
                    proj_subcat = proj_subcat.strip()
                    proj_lang = proj_lang.strip()

                    if not all([proj_folder, proj_name, proj_cat, proj_subcat, proj_lang]):
                        error_messages.append("Please fill all configuration fields.")
                    # Basic check for invalid characters, can be expanded
                    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
                    if any(c in proj_folder for c in invalid_chars) or ' ' in proj_folder:
                        error_messages.append("Project Folder Name should not contain spaces or special characters like /\\:*?\"<>|.")

                    if error_messages:
                        for msg in error_messages: st.error(msg)
                    else:
                        try:
                            # Prepare absolute path and check filesystem status
                            abs_proj_folder = os.path.abspath(proj_folder)
                            if os.path.exists(abs_proj_folder) and not os.path.isdir(abs_proj_folder):
                                st.error(f"Error: A file (not a folder) already exists with the name '{proj_folder}'. Please choose a different name.")
                            else:
                                # Create folder if it doesn't exist, warn if it does
                                if os.path.exists(abs_proj_folder):
                                    st.warning(f"Warning: Project folder '{abs_proj_folder}' already exists. Files within might be overwritten during the workflow.")
                                else:
                                    os.makedirs(abs_proj_folder, exist_ok=True)
                                    st.success(f"Project folder created/confirmed: '{abs_proj_folder}'")
                                    logger.info(f"Project folder ready: {abs_proj_folder}")

                                # --- Initialize workflow_state ---
                                # Use the (potentially multi-line) inputs directly
                                initial_human_message_content = f"Initial Setup:\n- Project: {proj_name}\n- Category: {proj_cat}/{proj_subcat}\n- Language: {proj_lang}\n- Min Q&A Rounds: {min_iter}"
                                initial_human_message = SDLC.HumanMessage(content=initial_human_message_content)

                                # Build the initial state dictionary carefully
                                initial_workflow_state = {
                                    # Core instances (must be present if config applied)
                                    "llm_instance": st.session_state.llm_instance,
                                    "tavily_instance": st.session_state.tavily_instance,
                                    # Communication history starts with the setup message
                                    "messages": [initial_human_message],
                                    # Project Configuration (using validated/stripped values)
                                    "project_folder": proj_folder,
                                    "project": proj_name,
                                    "category": proj_cat,
                                    "subcategory": proj_subcat,
                                    "coding_language": proj_lang,
                                    # Requirements Gathering State
                                    "user_input_iteration": 0,
                                    "user_input_min_iterations": min_iter,
                                    "user_input_questions": [],
                                    "user_input_answers": [],
                                    "user_input_done": False,
                                    "user_query_with_qa": "", # Will be built later
                                    "refined_prompt": "",
                                    # Initialize cycle states (using defaults where appropriate)
                                    "user_story_current": "", "user_story_feedback": "", "user_story_human_feedback": "", "user_story_done": False,
                                    "product_review_current": "", "product_review_feedback": "", "product_review_human_feedback": "", "product_review_done": False,
                                    "design_doc_current": "", "design_doc_feedback": "", "design_doc_human_feedback": "", "design_doc_done": False,
                                    "uml_selected_diagrams": [], "uml_current_codes": [], "uml_feedback": {}, "uml_human_feedback": {}, "uml_done": False,
                                    # Use a valid default GeneratedCode object with placeholder instructions meeting min_length
                                    "code_current": SDLC.GeneratedCode(files=[], instructions="[Placeholder - Code not generated yet.]"),
                                    "code_human_input": "", "code_web_search_results": "", "code_feedback": "", "code_human_feedback": "", "code_done": False,
                                    "code_review_current_feedback": "", "security_current_feedback": "", "review_security_human_feedback": "", "review_security_done": False,
                                    "test_cases_current": [], "test_cases_feedback": "", "test_cases_human_feedback": "", "test_cases_passed": False,
                                    "quality_current_analysis": "", "quality_feedback": "", "quality_human_feedback": "", "quality_done": False,
                                    "deployment_current_process": "", "deployment_feedback": "", "deployment_human_feedback": "", "deployment_done": False,
                                    # Final artifact storage (initialize as None or empty)
                                    "final_user_story": "", "final_product_review": "", "final_design_document": "",
                                    "final_uml_codes": [], "final_code_files": [], "final_code_review": "",
                                    "final_security_issues": "", "final_test_code_files": [], "final_quality_analysis": "",
                                    "final_deployment_process": "",
                                    # --- ADDED/MODIFIED: Initialize MD/PDF paths ---
                                    "refined_prompt_path": None,
                                    "refined_prompt_pdf_path": None,
                                    "final_user_story_path": None,
                                    "final_user_story_pdf_path": None,
                                    "final_product_review_path": None,
                                    "final_product_review_pdf_path": None,
                                    "final_design_document_path": None,
                                    "final_design_document_pdf_path": None,
                                    "final_uml_diagram_folder": None,
                                    "final_uml_png_paths": [],
                                    "final_review_security_folder": None,
                                    "review_code_snapshot_folder": None,
                                    "final_testing_folder": None,
                                    "testing_passed_code_folder": None,
                                    "final_quality_analysis_path": None, # MD path
                                    "final_quality_analysis_pdf_path": None, # PDF path
                                    "final_code_folder": None,
                                    "final_deployment_path": None, # MD path
                                    "final_deployment_pdf_path": None, # PDF path
                                    # --- END ADDED/MODIFIED ---
                                    # Intermediate Snapshot Paths
                                    "snapshot_path_codegen_initial": None,
                                    "snapshot_path_codegen_refined": None,
                                    "snapshot_path_review_refined": None,
                                    "snapshot_path_testing_refined": None,
                                    "snapshot_path_qa_polished": None,
                                }

                                # Update the main session state variables
                                st.session_state.workflow_state = initial_workflow_state
                                st.session_state.project_folder_base = proj_folder # Update base if user changed it
                                st.session_state.stage = "run_generate_questions" # Move to the first processing stage

                                # Add the initial setup message to the current cycle display list
                                st.session_state.current_cycle_messages.append(initial_human_message)
                                # Ensure previous_major_cycle is set for the first cycle
                                if st.session_state.previous_major_cycle is None:
                                    st.session_state.previous_major_cycle = STAGE_TO_CYCLE.get("initial_setup", "Requirements")

                                logger.info(f"Initial setup complete. Starting workflow for project '{proj_name}'.")
                                st.rerun() # Rerun to start the workflow execution

                        except OSError as oe:
                            st.error(f"Filesystem Error creating folder '{proj_folder}': {oe}. Check permissions or choose a different name.")
                            logger.error(f"OSError during initial setup folder creation: {oe}", exc_info=True)
                        except Exception as e:
                            st.error(f"An unexpected error occurred during setup: {e}")
                            logger.error(f"Unexpected error during initial setup: {e}", exc_info=True)

        # --- Deployment Preferences Form ---
        elif show_deployment_prefs_form:
            with st.form("deployment_preferences_form"): # Descriptive key
                st.markdown("### Deployment Preferences")
                st.info("Specify your desired deployment target and any relevant details.")

                # Common deployment targets
                deploy_target = st.selectbox(
                    "Target Environment",
                    options=["Localhost (using Docker)", "Docker (generic)", "AWS EC2", "AWS ECS/Fargate", "AWS Lambda", "Google Cloud Run", "Google Kubernetes Engine (GKE)", "Azure App Service", "Azure Kubernetes Service (AKS)", "Other Cloud VM", "Other Serverless", "Other Container Orchestrator"],
                    key="deploy_target_select",
                    help="Choose the primary target environment for deployment."
                )

                deploy_details = st.text_area(
                    "Additional Details / Constraints:",
                    height=100,
                    key="deploy_details_input",
                    placeholder="e.g., Specific AWS region (us-east-1), use Nginx as reverse proxy, database connection string source, required OS, any existing infrastructure to leverage.",
                    help="Provide any specific requirements, configurations, or constraints for the deployment."
                )

                submitted = st.form_submit_button("Generate Deployment Plan")
                if submitted:
                    # Combine preferences into a string for the backend
                    prefs = f"Target Environment: {deploy_target}\nAdditional Details: {deploy_details}"
                    st.session_state.current_prefs = prefs # Store for potential use/display later
                    st.session_state.stage = "run_generate_initial_deployment" # Move to the processing stage
                    logger.info(f"Deployment preferences collected: Target='{deploy_target}'")

                    # Add human message for context
                    deploy_prefs_message = SDLC.HumanMessage(content=f"Deployment Preferences Set:\n{prefs}")
                    st.session_state.workflow_state["messages"].append(deploy_prefs_message)
                    st.session_state.current_cycle_messages.append(deploy_prefs_message)

                    st.rerun()

        # --- General Input/Feedback Text Area ---
        elif show_input_box:
             input_label = "Your Input / Feedback:"
             input_help = "Provide your answers or feedback here. For Q&A, type '#DONE' on a new line when finished with the current round."
             # Customize label/help based on stage if needed
             if current_stage_ui == "collect_answers":
                 input_label = "Your Answers:"
             elif current_stage_ui == "collect_code_human_input":
                 input_label = "Describe Issues / Provide Input for Code:"
                 input_help = "Describe any errors encountered, unexpected behavior, or specific inputs you want the AI to test/consider."
             elif current_stage_ui == "merge_review_security_feedback":
                 input_label = "Your Feedback on Review/Security Reports:"
                 input_help = "Provide any comments, clarifications, or priorities regarding the code review and security findings."

             input_key = f"text_input_{current_stage_ui}" # Stage-specific key
             user_val = st.text_area(
                 input_label,
                 height=150,
                 key=input_key,
                 value=st.session_state.get('user_input', ''), # Use temporary storage if needed for complex edits
                 help=input_help
             )

             submit_key = f"submit_button_{current_stage_ui}" # Stage-specific key
             if st.button("Submit", key=submit_key):
                 user_text = user_val.strip()
                 # Basic validation: Ensure input is not empty
                 if not user_text:
                     st.warning("Please enter some input before submitting.")
                 else:
                     state = st.session_state.workflow_state
                     # Validate state type
                     if not isinstance(state, dict):
                         st.error("Workflow state is invalid. Restarting.")
                         logger.critical("Workflow state became invalid (not a dict). Forcing restart.")
                         initialize_state()
                         st.rerun()
                         st.stop()

                     try:
                         next_stage = None # Initialize next stage
                         # Ensure message list exists in state
                         if 'messages' not in state or not isinstance(state['messages'], list):
                             state['messages'] = []

                         # Create the HumanMessage object
                         human_message = SDLC.HumanMessage(content=user_text)
                         # Add to master list
                         state["messages"].append(human_message)
                         # Add to current cycle display list
                         if 'current_cycle_messages' not in st.session_state: st.session_state.current_cycle_messages = []
                         st.session_state.current_cycle_messages.append(human_message)

                         # --- Map current stage to state key, next run stage, and input type ---
                         # Tuple format: (state_key_to_update, next_processing_stage, needs_list_append)
                         map_logic = {
                             "collect_answers": ("user_input_answers", "run_generate_questions", True),
                             "collect_user_story_human_feedback": ("user_story_human_feedback", "run_refine_user_stories", False),
                             "collect_product_review_human_feedback": ("product_review_human_feedback", "run_refine_product_review", False),
                             "collect_design_doc_human_feedback": ("design_doc_human_feedback", "run_refine_design_doc", False),
                             "collect_uml_human_feedback": ("uml_human_feedback", "run_refine_uml_codes", False), # Special dict handling below
                             "collect_code_human_input": ("code_human_input", "run_web_search_code", False),
                             "collect_code_human_feedback": ("code_human_feedback", "run_refine_code", False),
                             "merge_review_security_feedback": ("review_security_human_feedback", "run_refine_code_with_reviews", False),
                             "collect_quality_human_feedback": ("quality_human_feedback", "run_refine_quality_and_code", False),
                             "collect_deployment_human_feedback": ("deployment_human_feedback", "run_refine_deployment", False),
                         }

                         if current_stage_ui in map_logic:
                             key_to_update, next_process_stage, is_list_input = map_logic[current_stage_ui]

                             # Store the input text in the workflow state dictionary
                             if is_list_input:
                                 # Append input to the list for this key
                                 state[key_to_update] = state.get(key_to_update, []) + [user_text]
                             elif key_to_update == "uml_human_feedback":
                                 # Store UML feedback in the expected dict format, using 'all' for simplicity
                                 state[key_to_update] = {"all": user_text}
                             else:
                                 # Overwrite state key with the new text value
                                 state[key_to_update] = user_text

                             next_stage = next_process_stage # Set the next stage for processing

                             # --- Special Handling Logic ---

                             # Q&A Completion Check
                             if current_stage_ui == "collect_answers":
                                 state["user_input_iteration"] = state.get("user_input_iteration", 0) + 1
                                 min_iterations_required = state.get("user_input_min_iterations", 1)
                                 # Check if #DONE is present (case-insensitive) in the last non-empty line
                                 lines = [line.strip() for line in user_text.splitlines() if line.strip()]
                                 is_done_signal_present = "#DONE" in lines[-1].upper() if lines else False

                                 logger.debug(f"Q&A Iteration: {state['user_input_iteration']} / {min_iterations_required}. '#DONE' signal present: {is_done_signal_present}")

                                 # Check if minimum iterations met AND done signal given
                                 if state["user_input_iteration"] >= min_iterations_required and is_done_signal_present:
                                     state["user_input_done"] = True
                                     next_stage = "run_refine_prompt" # Override: Q&A phase is finished, move to refining the prompt
                                     logger.info("Minimum Q&A iterations met and #DONE signal received. Proceeding to prompt refinement.")
                                 else:
                                     state["user_input_done"] = False
                                     # next_stage remains 'run_generate_questions' (to ask more questions)
                                     logger.info("Continuing Q&A round.")

                             # Skip Web Search if Tavily is not configured
                             if current_stage_ui == "collect_code_human_input" and not state.get('tavily_instance'):
                                 state["code_web_search_results"] = "Skipped (Tavily client not configured)"
                                 next_stage = "run_generate_code_feedback" # Skip web search and go directly to code feedback
                                 logger.info("Tavily not configured. Skipping web search step.")

                         else:
                             # Fallback if stage logic is somehow missing
                             st.error(f"Internal Error: Input handling logic is undefined for stage '{current_stage_ui}'. Please report this.")
                             logger.error(f"Input handling logic missing for defined input stage: {current_stage_ui}")

                         # --- Transition to Next Stage ---
                         if next_stage:
                             st.session_state.workflow_state = state # Commit state changes
                             st.session_state.user_input = "" # Clear the temporary input box content on successful submission
                             st.session_state.stage = next_stage # Update the application stage
                             logger.info(f"User input submitted for stage '{current_stage_ui}'. Transitioning to stage '{next_stage}'.")
                             st.rerun() # Rerun Streamlit to reflect the new stage

                     except Exception as e:
                         st.error(f"An error occurred while processing your input: {e}")
                         logger.error(f"Error processing input for stage '{current_stage_ui}': {e}", exc_info=True)
                         # Keep the input in the text box on error by not clearing st.session_state.user_input

        # --- Test Execution Feedback Area ---
        elif show_test_feedback_area:
            st.markdown("### Test Execution & Feedback")
            st.info("Please execute the generated tests against the code. Then, provide feedback on the results and indicate if the core functionality passed.")

            # Display AI feedback on the tests for context
            ai_test_feedback = st.session_state.workflow_state.get("test_cases_feedback", "*No AI feedback on tests was generated.*")
            with st.expander("View AI Feedback on Test Cases"):
                st.markdown(ai_test_feedback)

            # Input area for human feedback/results
            human_fb_text = st.text_area(
                "Your Feedback & Test Results:",
                height=150,
                key="test_case_human_feedback_input", # Unique key
                help="Describe which tests passed/failed, provide any error messages, stack traces, or observations from running the tests."
            )

            # Radio button for overall PASS/FAIL status
            pass_fail_status = st.radio(
                "Did the core functionality pass the tests?",
                options=("PASS", "FAIL"),
                index=1, # Default to FAIL
                key="test_case_pass_fail_radio", # Unique key
                horizontal=True,
                help="Select PASS only if the critical user stories are working as expected based on your testing."
            )

            # Action buttons
            col1, col2 = st.columns(2)
            with col1: # Submit Results button
                submit_key_test = "submit_test_results_button" # Unique key
                if st.button("Submit Test Results", key=submit_key_test):
                    state = st.session_state.workflow_state
                    # Ensure messages list exists
                    if 'messages' not in state or not isinstance(state['messages'], list): state['messages'] = []

                    # Format feedback and create HumanMessage
                    feedback_content = f"Test Execution Summary:\n- Overall Status: {pass_fail_status}\n- Detailed Feedback/Results:\n{human_fb_text}"
                    human_message = SDLC.HumanMessage(content=feedback_content)

                    # Add message to master list and current cycle display
                    state["messages"].append(human_message)
                    if 'current_cycle_messages' not in st.session_state: st.session_state.current_cycle_messages = []
                    st.session_state.current_cycle_messages.append(human_message)

                    # Update state with feedback and pass/fail status
                    state["test_cases_human_feedback"] = feedback_content
                    state["test_cases_passed"] = (pass_fail_status == "PASS")
                    logger.info(f"Test results submitted. Overall status: {pass_fail_status}.")

                    # Determine next stage based on pass/fail
                    next_stage_after_test = "run_save_testing_outputs" if state["test_cases_passed"] else "run_refine_test_cases_and_code"
                    st.session_state.stage = next_stage_after_test
                    st.session_state.workflow_state = state # Commit state changes
                    logger.info(f"Transitioning to stage '{next_stage_after_test}' based on test results.")
                    st.rerun()

            with col2: # Submit & Regenerate Code button (optional, allows skipping refinement)
                regen_key_test = "regenerate_code_from_testing_button" # Unique key
                if st.button("Regenerate Code (If Stuck)", key=regen_key_test, help="Use this if refinement isn't working and you want the AI to try generating code again from scratch, incorporating this test feedback."):
                    state = st.session_state.workflow_state
                    if 'messages' not in state or not isinstance(state['messages'], list): state['messages'] = []

                    # Format feedback indicating regeneration request
                    feedback_content_regen = f"Test Execution Summary:\n- Overall Status: {pass_fail_status}\n- Detailed Feedback/Results:\n{human_fb_text}\n\nDecision: Requesting full code regeneration based on this feedback."
                    human_message_regen = SDLC.HumanMessage(content=feedback_content_regen)

                    # Add message to history
                    state["messages"].append(human_message_regen)
                    if 'current_cycle_messages' not in st.session_state: st.session_state.current_cycle_messages = []
                    st.session_state.current_cycle_messages.append(human_message_regen)

                    # Store feedback, ensure test_cases_passed is False
                    state["test_cases_human_feedback"] = feedback_content_regen # Store context
                    state["test_cases_passed"] = False # Force refinement/regen path
                    logger.info(f"Test feedback submitted ({pass_fail_status}), requesting code regeneration.")

                    # --- Prepare Context for Code Regeneration ---
                    # Package testing feedback to guide the *initial* code generation step again
                    regen_context = f"Context from Failed Testing Cycle:\n- Overall Status: {pass_fail_status}\n- User Feedback/Errors:\n{human_fb_text}\n- AI Feedback on Failed Tests:\n{ai_test_feedback}\n\nInstruction: Regenerate the entire codebase attempting to address these issues from the start."
                    state["code_human_input"] = regen_context # Use the input field of the code generation cycle

                    # Add context message (optional, can be verbose but useful for tracing)
                    context_message = SDLC.HumanMessage(content=f"Context Forwarded for Code Regeneration (from Testing): {regen_context[:300]}...")
                    state["messages"].append(context_message) # Add to master list
                    st.session_state.current_cycle_messages.append(context_message) # Add to cycle list

                    # --- Transition Back to Code Generation ---
                    # NOTE: This jumps back significantly. Consider if a less drastic jump is desired.
                    # For now, jumping back to the *input* stage before initial code gen.
                    st.session_state.stage = "run_generate_initial_code" # Go back to generate initial code
                    st.session_state.workflow_state = state # Commit state
                    logger.info("Transitioning back to 'run_generate_initial_code' for regeneration based on test feedback.")
                    st.rerun()

        # --- Decision Buttons (Approve/Refine) ---
        elif show_decision_buttons:
            st.markdown("### Decision Point")
            st.info("Review the latest output for this cycle. Choose whether to refine it further based on feedback or approve it and proceed to the next cycle.")

            # Define mappings for Refine and Proceed actions based on the current stage
            # Refine Map: current_decision_stage -> next_feedback_or_input_stage
            refine_map = {
                "collect_user_story_decision": "run_generate_user_story_feedback",
                "collect_product_review_decision": "run_generate_product_review_feedback",
                "collect_design_doc_decision": "run_generate_design_doc_feedback",
                "collect_uml_decision": "run_generate_uml_feedback",
                "collect_code_decision": "collect_code_human_input", # Refining code usually needs new input/issues
                "collect_review_security_decision": "run_code_review", # Restart review cycle
                "collect_quality_decision": "run_generate_quality_feedback",
                "collect_deployment_decision": "run_generate_deployment_feedback",
            }
            # Proceed Map: current_decision_stage -> (done_flag_key, save_function or None, next_cycle_start_stage)
            proceed_map = {
                "collect_user_story_decision": ("user_story_done", SDLC.save_final_user_story, "run_generate_initial_product_review"),
                "collect_product_review_decision": ("product_review_done", SDLC.save_final_product_review, "run_generate_initial_design_doc"),
                "collect_design_doc_decision": ("design_doc_done", SDLC.save_final_design_doc, "run_select_uml_diagrams"),
                "collect_uml_decision": ("uml_done", SDLC.save_final_uml_diagrams, "run_generate_initial_code"),
                # Proceeding from Code Generation saves the current code to final_code_files
                "collect_code_decision": ("code_done", None, "run_code_review"), # No specific save func here, handled in logic below
                "collect_review_security_decision": ("review_security_done", SDLC.save_review_security_outputs, "run_generate_initial_test_cases"),
                "collect_quality_decision": ("quality_done", SDLC.save_final_quality_analysis, "generate_initial_deployment"), # Go to deployment prefs form
                "collect_deployment_decision": ("deployment_done", SDLC.save_final_deployment_plan, "END"), # End of workflow
            }

            # Determine button layout (add third button for QA code regen)
            num_cols = 3 if current_stage_ui == "collect_quality_decision" else 2
            cols = st.columns(num_cols)

            # --- Refine Button ---
            with cols[0]:
                refine_key = f"refine_button_{current_stage_ui}" # Unique key
                if st.button("Refine Further", key=refine_key, help="Go back and provide more feedback or request AI changes for the current artifact(s)."):
                    if current_stage_ui in refine_map:
                        state = st.session_state.workflow_state
                        # Mark as not done (to allow refinement loop)
                        done_key = current_stage_ui.replace("collect_", "").replace("_decision", "_done")
                        state[done_key] = False
                        next_refine_stage = refine_map[current_stage_ui]

                        # Add human message indicating decision
                        refine_message = SDLC.HumanMessage(content=f"Decision: Refine '{current_major_cycle}' cycle further.")
                        state['messages'] = state.get('messages', []) + [refine_message]
                        if 'current_cycle_messages' not in st.session_state: st.session_state.current_cycle_messages = []
                        st.session_state.current_cycle_messages.append(refine_message)

                        # Transition to the refinement starting stage
                        st.session_state.stage = next_refine_stage
                        st.session_state.workflow_state = state
                        logger.info(f"Decision made to Refine cycle '{current_major_cycle}'. Transitioning to stage '{next_refine_stage}'.")
                        st.rerun()
                    else:
                        st.warning(f"Refinement logic is not defined for stage '{current_stage_ui}'.")
                        logger.warning(f"Attempted to refine from stage '{current_stage_ui}' but no refine path is defined.")

            # --- Proceed Button ---
            with cols[1]:
                proceed_key = f"proceed_button_{current_stage_ui}" # Unique key
                if st.button("Approve & Proceed", key=proceed_key, help="Finalize the current cycle's artifacts and move to the next stage of the workflow."):
                    if current_stage_ui in proceed_map:
                        state = st.session_state.workflow_state
                        done_key, save_function, next_major_stage = proceed_map[current_stage_ui]
                        error_occurred = False

                        try:
                            # Mark the cycle as done
                            state[done_key] = True
                            logger.info(f"Decision made to Proceed from cycle '{current_major_cycle}'. Marked '{done_key}'=True.")

                            # Add human message indicating decision
                            proceed_message = SDLC.HumanMessage(content=f"Decision: Approve and proceed from '{current_major_cycle}' cycle.")
                            state['messages'] = state.get('messages', []) + [proceed_message]
                            if 'current_cycle_messages' not in st.session_state: st.session_state.current_cycle_messages = []
                            st.session_state.current_cycle_messages.append(proceed_message)

                            # --- Special Handling for Code Promotion ---
                            # When proceeding from Code Generation, store the current code as the baseline for Review/Security
                            if current_stage_ui == "collect_code_decision":
                                 current_code_object = state.get("code_current")
                                 if current_code_object and isinstance(current_code_object, SDLC.GeneratedCode) and current_code_object.files:
                                     state["final_code_files"] = current_code_object.files # This becomes the input for the next stage
                                     logger.info(f"Promoted {len(current_code_object.files)} code files from 'code_current' to 'final_code_files' for Review cycle.")
                                 else:
                                     st.warning("Proceeding from Code Generation, but the 'code_current' state seems invalid or empty. Review cycle might lack code.")
                                     logger.warning("Proceeding from Code Generation, but 'code_current' is invalid or has no files. Setting 'final_code_files' to empty list.")
                                     state["final_code_files"] = []

                            # --- Execute Save Function (if applicable) ---
                            if save_function:
                                save_func_name = getattr(save_function, '__name__', 'artifact_save_function')
                                logger.info(f"Executing save function: {save_func_name}")
                                with st.spinner(f"Saving {save_func_name.replace('save_final_', '').replace('_', ' ')}..."):
                                    state = save_function(state) # Update state with results of save function (e.g., file paths)
                                    st.session_state.workflow_state = state # Commit state update

                                # --- Post-Save Validation (Check if expected output path exists) ---
                                # Map save functions to the state keys where they store output paths
                                save_path_keys = {
                                    SDLC.save_final_user_story: "final_user_story_path",
                                    SDLC.save_final_product_review: "final_product_review_path",
                                    SDLC.save_final_design_doc: "final_design_document_path",
                                    SDLC.save_final_uml_diagrams: "final_uml_diagram_folder", # Check folder for UML
                                    SDLC.save_review_security_outputs: "final_review_security_folder", # Check main folder
                                    SDLC.save_testing_outputs: "final_testing_folder", # Check main folder
                                    SDLC.save_final_quality_analysis: "final_quality_analysis_path", # Check report path
                                    SDLC.save_final_deployment_plan: "final_deployment_path",
                                }
                                expected_path_key = save_path_keys.get(save_function)
                                saved_path_value = state.get(expected_path_key) if expected_path_key else True # Assume success if no path key expected

                                # Check if the path exists (and is a file/dir as appropriate)
                                save_successful = False
                                if expected_path_key:
                                    if saved_path_value and isinstance(saved_path_value, str) and os.path.exists(saved_path_value):
                                         # Basic check: path exists. Could add isfile/isdir if needed.
                                         save_successful = True
                                else:
                                    save_successful = True # No specific path to check

                                # Additionally check for QA saving the final code folder
                                if save_function == SDLC.save_final_quality_analysis:
                                    final_code_folder_path = state.get("final_code_folder")
                                    if not (final_code_folder_path and os.path.isdir(final_code_folder_path)):
                                        save_successful = False # Mark as failed if final code didn't save properly

                                if not save_successful:
                                     st.warning(f"Proceeding, but the save operation for '{current_major_cycle}' might have failed (output path invalid or missing). Check logs.")
                                     logger.warning(f"Save check failed after running {save_func_name}. Expected path key: {expected_path_key}, Value: {saved_path_value}")
                                else:
                                     logger.info(f"Save function {save_func_name} completed successfully and path validation passed (if applicable).")

                        except Exception as e:
                            st.error(f"An error occurred while finalizing cycle '{current_major_cycle}': {e}")
                            logger.error(f"Error during 'Proceed' action for stage '{current_stage_ui}': {e}", exc_info=True)
                            error_occurred = True

                        # Transition only if no errors occurred
                        if not error_occurred:
                            st.session_state.stage = next_major_stage
                            logger.info(f"Transitioning to the next cycle's start stage: '{next_major_stage}'")
                            st.rerun()
                    else:
                        st.warning(f"Proceed logic is not defined for stage '{current_stage_ui}'.")
                        logger.warning(f"Attempted to proceed from stage '{current_stage_ui}' but no proceed path is defined.")

            # --- Regenerate Code Button (Only for QA Decision) ---
            if current_stage_ui == "collect_quality_decision":
                with cols[2]:
                    regen_key_qa = "regenerate_code_from_qa_button" # Unique key
                    if st.button("Regenerate Code", key=regen_key_qa, help="If QA revealed significant issues needing a code rewrite, use this to jump back to code generation, providing QA feedback as context."):
                        state = st.session_state.workflow_state
                        if 'messages' not in state or not isinstance(state['messages'], list): state['messages'] = []
                        logger.info("Decision: Requesting code regeneration based on QA findings.")

                        # Add human message
                        regen_message = SDLC.HumanMessage(content="Decision: Regenerate code based on Quality Analysis findings.")
                        state["messages"].append(regen_message)
                        if 'current_cycle_messages' not in st.session_state: st.session_state.current_cycle_messages = []
                        st.session_state.current_cycle_messages.append(regen_message)

                        # --- Prepare context for regeneration ---
                        qa_report_summary = state.get('quality_current_analysis', 'No QA report available.')[:1500] # Limit summary length
                        regen_context = f"Context from Quality Analysis Cycle:\n- Final QA Report Summary:\n{qa_report_summary}\n\nInstruction: Regenerate the codebase attempting to address the quality concerns raised in the report."
                        state["code_human_input"] = regen_context # Feed context into the code gen input

                        # Add context message to history
                        context_message = SDLC.HumanMessage(content=f"Context Forwarded for Code Regeneration (from QA): {regen_context[:300]}...")
                        state["messages"].append(context_message)
                        st.session_state.current_cycle_messages.append(context_message)

                        # --- Transition back to Code Generation ---
                        st.session_state.stage = "run_generate_initial_code" # Jump back
                        st.session_state.workflow_state = state
                        logger.info("Transitioning back to 'run_generate_initial_code' for regeneration based on QA feedback.")
                        st.rerun()

        # --- End Stage ---
        elif current_stage_ui == "END":
            st.balloons()
            final_message = "## 🎉 Workflow Completed Successfully! 🎉\n\nAll cycles have been processed.\n\nYou can download the final artifacts and code snapshots from the sidebar.\n\nUse the 'Restart Workflow' button in the sidebar to begin a new project."
            update_display(final_message) # Update the display area as well
            st.markdown(final_message)
            logger.info("Workflow reached END stage.")

        # --- Fallback for Unknown UI Stages ---
        # This handles cases where the stage is not 'initial_setup', not a 'run_' stage,
        # and not one of the known input/decision stages. Should ideally not happen.
        elif not current_stage_ui.startswith("run_"):
             st.error(f"Internal Error: Reached an unknown UI interaction stage: '{current_stage_ui}'. The workflow might be stuck. Consider restarting.")
             logger.error(f"Reached unknown UI stage: {current_stage_ui}. State might be inconsistent.")


# ==============================================================================
# --- Cycle Indicator Column ---
# ==============================================================================
with indicator_col:
    st.subheader("Workflow Cycles")
    st.caption("Current progress through the SDLC.")

    # Determine the current cycle index for highlighting
    current_major_indicator = STAGE_TO_CYCLE.get(st.session_state.stage, "Unknown")
    current_idx_indicator = -1 # Default if stage/cycle is unknown
    if current_major_indicator == "END":
        current_idx_indicator = len(CYCLE_ORDER) # Mark as completed
    elif current_major_indicator in CYCLE_ORDER:
        current_idx_indicator = CYCLE_ORDER.index(current_major_indicator)

    # Simple CSS for styling the cycle list
    st.markdown("""
    <style>
        .cycle-item { margin-bottom: 0.75em; transition: all 0.3s ease-in-out; padding: 4px 0; border-radius: 4px; }
        .cycle-past { opacity: 0.5; font-size: 0.9em; padding-left: 15px; border-left: 4px solid #cccccc; }
        .cycle-current { font-weight: bold; font-size: 1.05em; color: #008080; border-left: 4px solid #008080; padding-left: 11px; background-color: #f0fafa; }
        .cycle-future { opacity: 0.8; font-size: 0.95em; padding-left: 15px; border-left: 4px solid #eeeeee; }
        .cycle-end { font-weight: bold; font-size: 1.0em; color: #4CAF50; border-left: 4px solid #4CAF50; padding-left: 11px; background-color: #f0fff0; }
    </style>
    """, unsafe_allow_html=True)

    # Display the cycle list with indicators
    # Optionally implement windowing/scrolling if list gets very long
    # win_before, win_after = 2, 4 # Example windowing parameters
    # start = max(0, current_idx_indicator - win_before)
    # end = min(len(CYCLE_ORDER), start + win_before + win_after + 1)
    # start = max(0, end - (win_before + win_after + 1)) # Adjust start if end was clamped

    for i, cycle_name in enumerate(CYCLE_ORDER):
        # if start <= i < end : # Apply windowing if uncommented above
            css_class = "cycle-item"
            display_name = cycle_name

            if i < current_idx_indicator:
                css_class += " cycle-past"
                display_name = f"✓ {cycle_name}" # Indicate past cycles
            elif i == current_idx_indicator and current_major_indicator != "END":
                css_class += " cycle-current"
                display_name = f"➡️ {cycle_name}" # Indicate current cycle
            else: # Future cycles
                css_class += " cycle-future"

            # Render the cycle item using markdown with embedded HTML/CSS
            st.markdown(f'<div class="{css_class}">{display_name}</div>', unsafe_allow_html=True)

    # Display completion marker if workflow is finished
    if current_major_indicator == "END":
        st.markdown(f'<div class="cycle-item cycle-end">✅ Workflow End</div>', unsafe_allow_html=True)


# ==============================================================================
# --- Invisible Stage Execution Logic ---
# ==============================================================================

def run_workflow_step(func, next_display_stage, *args):
    """
    Executes a backend workflow function (from SDLC.py), handles state updates,
    manages display content, adds messages to history, and transitions the UI stage.

    Args:
        func: The backend function to execute (e.g., SDLC.generate_questions).
        next_display_stage: The stage the UI should transition to after this step completes.
        *args: Additional arguments required by the backend function.
    """
    state_before = st.session_state.workflow_state
    messages_before_count = len(state_before.get('messages', []))

    # --- Define a VALID default GeneratedCode object for safety ---
    # This object includes the required 'instructions' field.
    valid_default_code = SDLC.GeneratedCode(files=[], instructions="[Default Instructions - Code Not Generated or Error]")

    # --- Pre-execution Checks ---
    if not isinstance(state_before, dict):
        st.error("Workflow state has become invalid. Please restart.")
        logger.critical("Workflow state is not a dictionary. Halting execution.")
        initialize_state() # Consider resetting state automatically or just stopping
        st.rerun()
        return # Stop execution

    # Get function name for logging/display
    func_name = getattr(func, '__name__', repr(func))
    # Handle lambda function name (specifically for deployment)
    if func_name == '<lambda>': func_name = "generate_initial_deployment"

    logger.info(f"Executing workflow step: {func_name}")
    try:
        # Show spinner during execution
        with st.spinner(f"Running: {func_name.replace('_',' ').title()}..."):

            # --- Check for Required Resources (LLM, Tavily) ---
            needs_llm = func not in [
                SDLC.save_final_user_story, SDLC.save_final_product_review,
                SDLC.save_final_design_doc, SDLC.save_final_uml_diagrams,
                SDLC.save_review_security_outputs, SDLC.save_testing_outputs,
                SDLC.save_final_quality_analysis, SDLC.save_final_deployment_plan,
                SDLC.web_search_code # Web search uses Tavily, checked separately
            ]
            if needs_llm and not state_before.get('llm_instance'):
                raise ConnectionError("LLM client is not configured or initialized in the workflow state.")

            # --- Handle Skippable Steps (e.g., Web Search) ---
            if func == SDLC.web_search_code and not state_before.get('tavily_instance'):
                 logger.warning("Web search step called, but Tavily client is not available in state. Skipping step.")
                 state_before["code_web_search_results"] = "Skipped (Tavily client not configured or API key missing)"
                 # Add a message indicating the skip
                 skip_message = AIMessage(content="Web Search: Skipped (Tavily client unavailable)")
                 state_before["messages"] = state_before.get("messages", []) + [skip_message]
                 if 'current_cycle_messages' not in st.session_state: st.session_state.current_cycle_messages = []
                 st.session_state.current_cycle_messages.append(skip_message)

                 # Manually update state and transition
                 st.session_state.workflow_state = state_before
                 st.session_state.stage = "run_generate_code_feedback" # Define the stage *after* web search
                 logger.info("Skipped web search. Transitioning directly to 'run_generate_code_feedback'.")
                 st.rerun()
                 return # Exit this function call

            # --- Special Handling for Sequential Review/Security Steps ---
            # If the function is code_review, run it, update state, and immediately trigger security_check
            if func == SDLC.code_review:
                 logger.info("Executing code review step...")
                 state_after_review = SDLC.code_review(state_before, *args)
                 if not isinstance(state_after_review, dict):
                     raise TypeError(f"Function 'code_review' did not return a dictionary state. Got: {type(state_after_review)}")

                 # Add any new messages from code_review to the cycle display
                 messages_after_review_count = len(state_after_review.get('messages', []))
                 new_review_messages = state_after_review.get('messages', [])[messages_before_count:messages_after_review_count]
                 if new_review_messages:
                     if 'current_cycle_messages' not in st.session_state: st.session_state.current_cycle_messages = []
                     st.session_state.current_cycle_messages.extend(new_review_messages)

                 # Update the main state
                 st.session_state.workflow_state = state_after_review
                 # Transition directly to the security check stage
                 st.session_state.stage = "run_security_check"
                 logger.info("Code review completed. Transitioning directly to 'run_security_check'.")
                 st.rerun()
                 return # Exit this function call, security check will run on the next rerun

            # --- Normal Function Execution ---
            updated_state = func(state_before, *args)

        # --- Post-execution State Update and Validation ---
        if not isinstance(updated_state, dict):
            # This indicates a fundamental issue with the backend function
            logger.error(f"Workflow function '{func_name}' returned an invalid type: {type(updated_state)}. Expected a dictionary.")
            st.error(f"Internal Error: Step '{func_name}' failed due to an unexpected return type. Workflow halted.")
            st.stop() # Halt execution as state is likely corrupted
            return

        st.session_state.workflow_state = updated_state
        logger.debug(f"State successfully updated after executing {func_name}.")

        # --- Add New AI Messages to Cycle Display ---
        messages_after_count = len(updated_state.get('messages', []))
        new_messages = updated_state.get('messages', [])[messages_before_count:messages_after_count]
        if new_messages:
            # Filter to only add AI messages generated by this step
            new_ai_messages = [msg for msg in new_messages if isinstance(msg, AIMessage)]
            if new_ai_messages:
                if 'current_cycle_messages' not in st.session_state: st.session_state.current_cycle_messages = []
                st.session_state.current_cycle_messages.extend(new_ai_messages)
                logger.debug(f"Added {len(new_ai_messages)} new AI message(s) from {func_name} to cycle display.")

        # --- Determine Display Content for the Next UI Stage ---
        # (This complex block sets `display_text` and potentially overrides `next_display_stage`)
        display_text = f"Completed step: {func_name}. Preparing for {next_display_stage}..." # Default message

        if func == SDLC.generate_questions:
            # Display the newly generated questions
            questions = updated_state.get("user_input_questions", [])[-5:] # Get last 5 questions
            if questions:
                min_iter = updated_state.get('user_input_min_iterations', 1)
                current_iter = updated_state.get("user_input_iteration", 0) # Iteration *before* answering these
                is_min_met = (current_iter + 1 >= min_iter) # Check if *this round* meets the minimum
                min_iter_msg = f"(Minimum {min_iter} rounds required)" if not is_min_met else ""
                display_text = f"**Please answer the following questions {min_iter_msg}:**\n\n" + "\n".join(f"- {q}" for q in questions)
                if is_min_met:
                    display_text += "\n\n*When finished answering, type **#DONE** on a new line to proceed.*"
                next_display_stage = "collect_answers" # Ensure UI goes to answer collection
            else:
                # If no questions were generated (e.g., AI decided it's enough)
                display_text = "The AI generated no further questions. Refining the project prompt based on the discussion..."
                logger.info("No new questions generated by AI. Moving to refine prompt.")
                next_display_stage = "run_refine_prompt" # Skip answer collection

        elif func == SDLC.refine_prompt:
            refined_prompt = updated_state.get('refined_prompt', '*Error: Refined prompt not found in state.*')
            display_text = f"**Refined Project Prompt:**\n```markdown\n{refined_prompt}\n```\n\n*Generating initial User Stories based on this prompt...*"

        elif func == SDLC.generate_initial_user_stories:
             stories = updated_state.get('user_story_current', '*Error: User stories not found.*')
             display_text = f"**Initial User Stories Generated:**\n\n{stories}\n\n*Generating AI feedback on these stories...*"

        elif func == SDLC.generate_user_story_feedback:
             current_stories = updated_state.get('user_story_current', '*N/A*')
             ai_feedback = updated_state.get('user_story_feedback', '*N/A*')
             display_text = f"**Current User Stories:**\n```\n{current_stories}\n```\n---\n**AI Feedback on Stories:**\n\n{ai_feedback}\n\n---\n*Please provide your feedback or desired changes below.*"
             next_display_stage = "collect_user_story_human_feedback" # Ready for human input

        elif func == SDLC.refine_user_stories:
             refined_stories = updated_state.get('user_story_current', '*N/A*')
             display_text = f"**Refined User Stories:**\n\n{refined_stories}\n\n*Please review the refined stories. Choose 'Refine Further' or 'Approve & Proceed' below.*"
             next_display_stage = "collect_user_story_decision" # Ready for decision

        elif func == SDLC.generate_initial_product_review:
             review = updated_state.get('product_review_current', '*N/A*')
             display_text = f"**Initial Product Owner Review Generated:**\n\n{review}\n\n*Generating AI feedback on this review...*"

        elif func == SDLC.generate_product_review_feedback:
             current_review = updated_state.get('product_review_current', '*N/A*')
             ai_feedback = updated_state.get('product_review_feedback', '*N/A*')
             display_text = f"**Current Product Review:**\n```\n{current_review}\n```\n---\n**AI Feedback on Review:**\n\n{ai_feedback}\n\n---\n*Please provide your feedback or desired changes below.*"
             next_display_stage = "collect_product_review_human_feedback"

        elif func == SDLC.refine_product_review:
             refined_review = updated_state.get('product_review_current', '*N/A*')
             display_text = f"**Refined Product Review:**\n\n{refined_review}\n\n*Please review the refined PO review. Choose 'Refine Further' or 'Approve & Proceed' below.*"
             next_display_stage = "collect_product_review_decision"

        elif func == SDLC.generate_initial_design_doc:
             doc = updated_state.get('design_doc_current', '*N/A*')
             display_text = f"**Initial Design Document Generated:**\n```markdown\n{doc}\n```\n\n*Generating AI feedback on this document...*"

        elif func == SDLC.generate_design_doc_feedback:
             current_doc = updated_state.get('design_doc_current', '*N/A*')
             ai_feedback = updated_state.get('design_doc_feedback', '*N/A*')
             display_text = f"**Current Design Document:**\n```markdown\n{current_doc}\n```\n---\n**AI Feedback on Design:**\n\n{ai_feedback}\n\n---\n*Please provide your feedback or desired changes below.*"
             next_display_stage = "collect_design_doc_human_feedback"

        elif func == SDLC.refine_design_doc:
             refined_doc = updated_state.get('design_doc_current', '*N/A*')
             display_text = f"**Refined Design Document:**\n```markdown\n{refined_doc}\n```\n\n*Please review the refined design. Choose 'Refine Further' or 'Approve & Proceed' below.*"
             next_display_stage = "collect_design_doc_decision"

        elif func == SDLC.select_uml_diagrams:
             messages = updated_state.get('messages', [])
             # Try to find the specific justification message from the AI
             justification_msg_content = "Relevant UML diagram types selected based on the design." # Default
             if messages and isinstance(messages[-1], AIMessage) and ("selected" in messages[-1].content.lower() or "recommend" in messages[-1].content.lower()):
                 justification_msg_content = messages[-1].content # Use the actual AI message content
             display_text = f"**UML Diagram Selection:**\n\n{justification_msg_content}\n\n*Generating initial PlantUML code for selected diagrams...*"

        elif func == SDLC.generate_initial_uml_codes:
             codes = updated_state.get('uml_current_codes', [])
             if codes:
                 codes_display = "\n\n".join([f"**{c.diagram_type}**:\n```plantuml\n{c.code}\n```" for c in codes])
             else:
                 codes_display = "*No UML codes were generated.*"
             display_text = f"**Generated Initial PlantUML Codes:**\n\n{codes_display}\n\n*Generating AI feedback on these diagrams...*"

        elif func == SDLC.generate_uml_feedback:
             codes = updated_state.get('uml_current_codes', [])
             feedback_dict = updated_state.get('uml_feedback', {})
             codes_display = "\n\n".join([f"**{c.diagram_type}**:\n```plantuml\n{c.code}\n```" for c in codes]) if codes else "*N/A*"
             feedback_display = "\n\n".join([f"**Feedback for {dt}:**\n{fb}" for dt, fb in feedback_dict.items()]) if feedback_dict else "*N/A*"
             display_text = f"**Current UML Codes:**\n{codes_display}\n---\n**AI Feedback on Diagrams:**\n{feedback_display}\n\n---\n*Provide your overall feedback or specific changes needed below.*"
             next_display_stage = "collect_uml_human_feedback"

        elif func == SDLC.refine_uml_codes:
             codes = updated_state.get('uml_current_codes', [])
             codes_display = "\n\n".join([f"**{c.diagram_type} (Refined):**\n```plantuml\n{c.code}\n```" for c in codes]) if codes else "*N/A*"
             display_text = f"**Refined UML Codes:**\n\n{codes_display}\n\n*Please review the refined diagrams. Choose 'Refine Further' or 'Approve & Proceed' below.*"
             next_display_stage = "collect_uml_decision"

        elif func == SDLC.generate_initial_code:
             code_data = updated_state.get("code_current", valid_default_code) # Use valid default here!
             files_display = []
             total_len, max_len = 0, 4000 # Limit display length
             num_files = len(code_data.files) if code_data and code_data.files else 0
             instr = code_data.instructions if code_data else "[Instructions not available]"

             if num_files > 0:
                 for f in code_data.files:
                     header = f"**File: {f.filename}**:\n```\n"
                     footer = "\n```\n"
                     # Calculate max content preview length safely
                     max_content = max(0, max_len - total_len - len(header) - len(footer) - 50) # 50 char buffer
                     content_preview = f.content[:max_content] if f.content else ""
                     is_truncated = len(f.content) > len(content_preview) if f.content else False
                     preview_str = f"{header}{content_preview}{'... (content truncated)' if is_truncated else ''}{footer}"
                     files_display.append(preview_str)
                     total_len += len(preview_str)
                     if total_len >= max_len:
                         files_display.append("\n*...(Code file display truncated due to length)*")
                         break
                 code_files_str = "".join(files_display)
                 display_text = f"**Initial Code Generated ({num_files} file{'s' if num_files != 1 else ''}):**\n{code_files_str}\n---\n**Setup & Run Instructions:**\n```\n{instr}\n```\n\n---\n*Try to set up and run the code. Describe any errors or issues below.*"
             else:
                 display_text = "Initial code generation step completed, but no code files were generated. This might indicate an issue with the request or the LLM's response.\n\n*Please describe the expected outcome or provide feedback below.*"
                 logger.warning("generate_initial_code resulted in a valid GeneratedCode structure but with an empty file list.")
             next_display_stage = "collect_code_human_input"

        elif func == SDLC.web_search_code:
            results = updated_state.get('code_web_search_results', '*No web search results available.*')
            display_text = f"**Web Search Results (if applicable):**\n\n{results}\n\n*Generating AI feedback on the code, considering your input and these search results...*"

        elif func == SDLC.generate_code_feedback:
             ai_feedback = updated_state.get('code_feedback', '*N/A*')
             user_input = updated_state.get('code_human_input', None) # Get the input that triggered this
             context_header = "**Context Provided (User Input/Issue):**\n" if user_input else ""
             user_input_display = f"```\n{user_input}\n```\n---\n" if user_input else ""
             display_text = f"{context_header}{user_input_display}**AI Code Feedback:**\n\n{ai_feedback}\n\n---\n*Please provide your comments on the AI's feedback below (e.g., 'Yes, suggestion 1 seems right', 'No, the issue is actually in file X').*"
             next_display_stage = "collect_code_human_feedback"

        elif func == SDLC.refine_code:
             code_data = updated_state.get("code_current", valid_default_code) # Use valid default
             files_display=[]; total_len, max_len=0, 4000
             num_files = len(code_data.files) if code_data else 0
             instr = code_data.instructions if code_data else "[Instructions not available]"
             if num_files > 0:
                 for f in code_data.files:
                     header = f"**File: {f.filename} (Refined):**\n```\n"; footer = "\n```\n"
                     max_content = max(0, max_len - total_len - len(header) - len(footer) - 50)
                     content_preview = f.content[:max_content] if f.content else ""; is_truncated = len(f.content) > len(content_preview) if f.content else False
                     preview_str = f"{header}{content_preview}{'... (content truncated)' if is_truncated else ''}{footer}"
                     files_display.append(preview_str); total_len += len(preview_str)
                     if total_len >= max_len: files_display.append("\n*...(Code file display truncated)*"); break
                 code_files_str = "".join(files_display)
                 display_text = f"**Refined Code ({num_files} file{'s' if num_files != 1 else ''}):**\n{code_files_str}\n---\n**Setup/Run Instructions:**\n```\n{instr}\n```\n\n---\n*Please review the refined code. Choose 'Refine Further' or 'Approve & Proceed' below.*"
             else:
                 display_text = "Code refinement step completed, but no files were found in the result. This might indicate an error.\n\n*Choose 'Refine Further' to provide input or 'Approve & Proceed' if this is expected.*"
                 logger.warning("refine_code resulted in a valid GeneratedCode structure but with an empty file list.")
             next_display_stage = "collect_code_decision"

        elif func == SDLC.security_check: # Display after security check completes (code review ran just before)
             review_fb = updated_state.get('code_review_current_feedback', '*Code review feedback not available.*')
             security_fb = updated_state.get('security_current_feedback', '*Security check feedback not available.*')
             display_text = f"**Code Review Findings:**\n```\n{review_fb}\n```\n---\n**Security Check Findings:**\n```\n{security_fb}\n```\n---\n*Please provide your overall feedback on these reports below (e.g., prioritize fixes, accept risks).*";
             next_display_stage = "merge_review_security_feedback" # Stage to collect feedback on both reports

        elif func == SDLC.refine_code_with_reviews:
             code_data = updated_state.get("code_current", valid_default_code) # Use valid default
             files_display=[]; total_len, max_len=0, 4000
             num_files = len(code_data.files) if code_data else 0
             instr = code_data.instructions if code_data else "[Instructions not available]"
             if num_files > 0:
                 for f in code_data.files:
                     header = f"**File: {f.filename} (Post-Review/Security):**\n```\n"; footer = "\n```\n"
                     max_content = max(0, max_len - total_len - len(header) - len(footer) - 50)
                     content_preview = f.content[:max_content] if f.content else ""; is_truncated = len(f.content) > len(content_preview) if f.content else False
                     preview_str = f"{header}{content_preview}{'... (content truncated)' if is_truncated else ''}{footer}"
                     files_display.append(preview_str); total_len += len(preview_str)
                     if total_len >= max_len: files_display.append("\n*...(Code file display truncated)*"); break
                 code_files_str = "".join(files_display)
                 display_text = f"**Code Refined Post-Review & Security ({num_files} file{'s' if num_files != 1 else ''}):**\n{code_files_str}\n---\n**Setup/Run Instructions:**\n```\n{instr}\n```\n\n---\n*This code incorporates feedback from the review cycle. Review the final code and decide below.*"
             else:
                 display_text = "Code refinement post-review completed, but no files found. This likely indicates an error.\n\n*Choose 'Refine Further' (to restart review) or 'Approve & Proceed' if this was somehow expected.*"
                 logger.error("refine_code_with_reviews resulted in an empty file list.")
             next_display_stage = "collect_review_security_decision"

        elif func == SDLC.generate_initial_test_cases:
             tests = updated_state.get('test_cases_current', [])
             tests_display = "\n\n".join([f"**Test: {tc.description}**\n  - Input: `{tc.input_data}`\n  - Expected Output: `{tc.expected_output}`" for tc in tests]) if tests else "*No test cases generated.*"
             display_text=f"**Generated Initial Test Cases ({len(tests)}):**\n\n{tests_display}\n\n*Generating AI feedback on these test cases...*"

        elif func == SDLC.generate_test_cases_feedback:
             tests = updated_state.get('test_cases_current', [])
             ai_feedback = updated_state.get('test_cases_feedback', '*N/A*')
             tests_display = "\n\n".join([f"**Test: {tc.description}**\n  - Input: `{tc.input_data}`\n  - Expected Output: `{tc.expected_output}`" for tc in tests]) if tests else "*N/A*"
             display_text=f"**Current Test Cases ({len(tests)}):**\n{tests_display}\n---\n**AI Feedback on Tests:**\n\n{ai_feedback}\n\n---\n*Please execute these tests against the code and report the results/feedback below.*";
             next_display_stage = "collect_test_cases_human_feedback"

        elif func == SDLC.refine_test_cases_and_code:
             tests = updated_state.get('test_cases_current', [])
             code_data_after_test_refine = updated_state.get('code_current', valid_default_code) # Use valid default
             files_count = len(code_data_after_test_refine.files) if code_data_after_test_refine else 0
             code_update_msg = f"Code ({files_count} files) and {len(tests)} test case(s) were refined based on test failures." if files_count > 0 else f"{len(tests)} Test case(s) refined (code may not have changed)."
             tests_display = "\n\n".join([f"**Test: {tc.description}**:\n  - Input:`{tc.input_data}`\n  - Expected:`{tc.expected_output}`" for tc in tests]) if tests else "*N/A*"
             display_text = f"**Refinement After Test Failure:**\n*{code_update_msg}*\n\n**Refined Tests ({len(tests)}):**\n{tests_display}\n\n*Please execute the tests again using the refined code and provide results/feedback below.*";
             next_display_stage = "collect_test_cases_human_feedback" # Loop back to collect results again

        elif func == SDLC.save_testing_outputs:
            display_text = f"Testing cycle completed (PASS). Final tests and passed code snapshot saved.\n\n*Generating overall Quality Analysis report...*"

        elif func == SDLC.generate_initial_quality_analysis:
             report = updated_state.get('quality_current_analysis', '*N/A*')
             display_text=f"**Initial Quality Analysis Report Generated:**\n\n{report}\n\n*Generating AI feedback on this QA report...*"

        elif func == SDLC.generate_quality_feedback:
             current_report = updated_state.get('quality_current_analysis', '*N/A*')
             ai_feedback = updated_state.get('quality_feedback', '*N/A*')
             display_text=f"**Current QA Report:**\n```\n{current_report}\n```\n---\n**AI Feedback on QA Report:**\n\n{ai_feedback}\n\n---\n*Please provide your feedback on the QA report below.*";
             next_display_stage = "collect_quality_human_feedback"

        elif func == SDLC.refine_quality_and_code:
             report = updated_state.get('quality_current_analysis', '*N/A*')
             code_data_qa_refined = updated_state.get('code_current', valid_default_code) # Use valid default
             code_files_exist = bool(code_data_qa_refined and code_data_qa_refined.files)
             code_update_msg = "*Minor, non-functional code polish may have been applied based on QA feedback.*" if code_files_exist else "*QA report refined (code unchanged).*"
             display_text=f"**Refined Quality Analysis Report:**\n\n{report}\n\n{code_update_msg}\n\n*Please review the final QA report. Choose 'Refine Further', 'Approve & Proceed', or 'Regenerate Code' below.*";
             next_display_stage = "collect_quality_decision"

        elif func_name == "generate_initial_deployment": # Handle lambda name
             plan = updated_state.get('deployment_current_process', '*N/A*')
             # Retrieve prefs used from state if stored, otherwise use placeholder
             prefs_used = st.session_state.get('current_prefs', '[Preferences used previously, not displayed]')
             display_text = f"**Initial Deployment Plan Generated:**\n*Based on Preferences:*\n```\n{prefs_used}\n```\n*Generated Plan:*\n```markdown\n{plan}\n```\n\n*Generating AI feedback on this deployment plan...*";

        elif func == SDLC.generate_deployment_feedback:
             current_plan = updated_state.get('deployment_current_process', '*N/A*')
             ai_feedback = updated_state.get('deployment_feedback', '*N/A*')
             display_text=f"**Current Deployment Plan:**\n```markdown\n{current_plan}\n```\n---\n**AI Feedback on Plan:**\n\n{ai_feedback}\n\n---\n*Please provide your feedback or required changes for the deployment plan below.*";
             next_display_stage = "collect_deployment_human_feedback"

        elif func == SDLC.refine_deployment:
             plan = updated_state.get('deployment_current_process', '*N/A*')
             display_text = f"**Refined Deployment Plan:**\n```markdown\n{plan}\n```\n\n*Please review the refined deployment plan. Choose 'Refine Further' or 'Approve & Proceed' below.*";
             next_display_stage = "collect_deployment_decision"

        # Display logic for save functions
        elif func in [SDLC.save_final_user_story, SDLC.save_final_product_review, SDLC.save_final_design_doc, SDLC.save_final_uml_diagrams, SDLC.save_review_security_outputs, SDLC.save_testing_outputs, SDLC.save_final_quality_analysis, SDLC.save_final_deployment_plan]:
            # Determine artifact name from function name
            artifact_name = func.__name__.replace('save_final_','').replace('_',' ').title()
            # Determine next major action/cycle name
            next_action_stage = next_display_stage # The stage name provided to run_workflow_step
            next_action_cycle = STAGE_TO_CYCLE.get(next_action_stage, next_action_stage).replace('_',' ').title()
            # Special case names for clarity
            if next_action_stage == "generate_initial_deployment":
                next_action_name = "Deployment Preferences Input"
            elif next_action_stage == "END":
                next_action_name = "Workflow End"
            else:
                next_action_name = f"{next_action_cycle} Cycle"

            display_text = f"✅ **{artifact_name} saved successfully.**\n\n*Proceeding to: {next_action_name}...*"
            logger.info(f"Artifact saved: {artifact_name}. Next step starts stage: {next_action_stage}")

        # --- Update UI Display and Transition Stage ---
        update_display(display_text)
        st.session_state.stage = next_display_stage
        logger.info(f"Completed step '{func_name}'. UI transitioning to stage '{next_display_stage}'.")
        st.rerun() # Rerun Streamlit to reflect the changes

    # --- Error Handling ---
    except ConnectionError as ce:
        error_msg = f"Connection Error during step '{func_name}': {ce}. Please check your API keys, network connection, and service status."
        st.error(error_msg)
        logger.critical(error_msg, exc_info=False) # Log as critical, but maybe don't need full traceback always
        # Optionally add a retry button here specific to connection errors if desired
    except pydantic_core.ValidationError as pve:
        # Handle Pydantic errors (often from LLM structured output) gracefully
        error_details = str(pve)
        logger.error(f"Data Validation Error in step '{func_name}': {error_details}", exc_info=True)
        # Check if it's the specific error related to the default GeneratedCode
        if "GeneratedCode" in error_details and "instructions" in error_details and "Field required" in error_details:
             error_msg = f"Internal Application Error: Failed processing a code object during step '{func_name}', likely due to a missing default value in the application code. Please report this issue. Details: {error_details}"
             st.error(error_msg)
             # Halt here as it's an app logic issue needing a fix in app.py
             st.stop()
        else:
             # General Pydantic error
             error_msg = f"Data Validation Error during step '{func_name}': The AI's response did not match the expected format. Details: {error_details}"
             st.error(error_msg)
             # Offer retry for general validation errors
             retry_key_pve = f"retry_btn_pve_{func_name}_{int(time.time())}"
             if st.button("Retry Last Step", key=retry_key_pve):
                 logger.info(f"User initiated retry after Pydantic error in {func_name}.")
                 st.rerun()
    except TypeError as te:
        # TypeErrors often indicate programming errors (e.g., wrong argument types)
        error_msg = f"Type Error during step '{func_name}': {te}. This might indicate an internal application issue."
        st.error(error_msg)
        logger.error(f"TypeError executing step '{func_name}': {te}", exc_info=True)
        st.stop() # Halt on TypeErrors as they usually require code fixes
    except ValueError as ve:
        # ValueErrors can be raised by backend logic for specific input issues
        error_msg = f"Input Error during step '{func_name}': {ve}. Please check the inputs or previous steps."
        st.error(error_msg)
        logger.error(f"ValueError executing step '{func_name}': {ve}", exc_info=True)
        # Offer retry for ValueErrors as they might be transient or fixable by adjusting input
        retry_key_ve = f"retry_btn_ve_{func_name}_{int(time.time())}"
        if st.button("Retry Last Step", key=retry_key_ve):
            logger.info(f"User initiated retry after ValueError in {func_name}.")
            st.rerun()
    except Exception as e:
        # Catch-all for other unexpected errors
        error_msg = f"An unexpected error occurred during step '{func_name}': {e}"
        st.error(error_msg)
        logger.error(f"Unexpected error executing step '{func_name}': {e}", exc_info=True)
        # Offer retry for general exceptions
        retry_key_exc = f"retry_btn_exc_{func_name}_{int(time.time())}" # Ensure unique key
        if st.button("Retry Last Step", key=retry_key_exc):
            logger.info(f"User initiated retry after general exception in {func_name}.")
            st.rerun()


# ==============================================================================
# --- Workflow Map Definition ---
# Maps "run_*" stages to their backend function and the next UI stage
# ==============================================================================
workflow_map = {
    # Requirements Cycle
    "run_generate_questions": (SDLC.generate_questions, "collect_answers"),
    "run_refine_prompt": (SDLC.refine_prompt, "run_generate_initial_user_stories"), # End of Requirements
    # User Story Cycle
    "run_generate_initial_user_stories": (SDLC.generate_initial_user_stories, "run_generate_user_story_feedback"),
    "run_generate_user_story_feedback": (SDLC.generate_user_story_feedback, "collect_user_story_human_feedback"),
    "run_refine_user_stories": (SDLC.refine_user_stories, "collect_user_story_decision"),
    # Product Review Cycle
    "run_generate_initial_product_review": (SDLC.generate_initial_product_review, "run_generate_product_review_feedback"),
    "run_generate_product_review_feedback": (SDLC.generate_product_review_feedback, "collect_product_review_human_feedback"),
    "run_refine_product_review": (SDLC.refine_product_review, "collect_product_review_decision"),
    # Design Cycle
    "run_generate_initial_design_doc": (SDLC.generate_initial_design_doc, "run_generate_design_doc_feedback"),
    "run_generate_design_doc_feedback": (SDLC.generate_design_doc_feedback, "collect_design_doc_human_feedback"),
    "run_refine_design_doc": (SDLC.refine_design_doc, "collect_design_doc_decision"),
    # UML Cycle
    "run_select_uml_diagrams": (SDLC.select_uml_diagrams, "run_generate_initial_uml_codes"),
    "run_generate_initial_uml_codes": (SDLC.generate_initial_uml_codes, "run_generate_uml_feedback"),
    "run_generate_uml_feedback": (SDLC.generate_uml_feedback, "collect_uml_human_feedback"),
    "run_refine_uml_codes": (SDLC.refine_uml_codes, "collect_uml_decision"),
    # Code Generation Cycle
    "run_generate_initial_code": (SDLC.generate_initial_code, "collect_code_human_input"),
    "run_web_search_code": (SDLC.web_search_code, "run_generate_code_feedback"), # Handled specially in run_workflow_step if skipped
    "run_generate_code_feedback": (SDLC.generate_code_feedback, "collect_code_human_feedback"),
    "run_refine_code": (SDLC.refine_code, "collect_code_decision"),
    # Review & Security Cycle
    "run_code_review": (SDLC.code_review, "run_security_check"), # Special handling: runs review then triggers security check
    "run_security_check": (SDLC.security_check, "merge_review_security_feedback"), # Displays both reports, waits for feedback
    "run_refine_code_with_reviews": (SDLC.refine_code_with_reviews, "collect_review_security_decision"),
    # Testing Cycle
    "run_generate_initial_test_cases": (SDLC.generate_initial_test_cases, "run_generate_test_cases_feedback"),
    "run_generate_test_cases_feedback": (SDLC.generate_test_cases_feedback, "collect_test_cases_human_feedback"),
    "run_refine_test_cases_and_code": (SDLC.refine_test_cases_and_code, "collect_test_cases_human_feedback"), # Loop back to test execution
    "run_save_testing_outputs": (SDLC.save_testing_outputs, "run_generate_initial_quality_analysis"), # End of Testing
    # Quality Analysis Cycle
    "run_generate_initial_quality_analysis": (SDLC.generate_initial_quality_analysis, "run_generate_quality_feedback"),
    "run_generate_quality_feedback": (SDLC.generate_quality_feedback, "collect_quality_human_feedback"),
    "run_refine_quality_and_code": (SDLC.refine_quality_and_code, "collect_quality_decision"),
    # Deployment Cycle
    "run_generate_initial_deployment": (
        lambda state: SDLC.generate_initial_deployment(state, st.session_state.get('current_prefs', '')), # Pass prefs via lambda
        "run_generate_deployment_feedback"
    ),
    "run_generate_deployment_feedback": (SDLC.generate_deployment_feedback, "collect_deployment_human_feedback"),
    "run_refine_deployment": (SDLC.refine_deployment, "collect_deployment_decision"),
 }

# ==============================================================================
# --- Main Execution Logic ---
# Checks the current stage and runs the corresponding backend function if it's a "run_" stage.
# ==============================================================================
if st.session_state.get('config_applied', False):
    current_stage_to_run = st.session_state.stage # Get the current stage

    # Check if the stage indicates a background processing step
    if current_stage_to_run.startswith("run_"):
        if current_stage_to_run in workflow_map:
            # Retrieve the function and the next UI stage from the map
            func_to_execute, next_ui_stage = workflow_map[current_stage_to_run]
            # Call the central execution function
            run_workflow_step(func_to_execute, next_ui_stage)
        else:
            # This indicates a potential error in the workflow definition or state
            st.error(f"Internal Error: Unknown processing stage '{current_stage_to_run}' encountered. Workflow cannot proceed. Please restart.")
            logger.critical(f"Workflow halted at unknown 'run_' stage: {current_stage_to_run}. Check workflow_map definition.")
            # Optionally force a reset or stop execution
            # initialize_state()
            # st.rerun()
            st.stop()
    # elif current_stage_to_run == "END":
        # Handled within the main column display logic
    #    pass # No processing needed for END stage
    # else:
        # Stage is likely an input/decision stage, handled by the UI widgets above
    #    pass

# Display warning if configuration hasn't been applied, unless at the very start
elif st.session_state.stage != "initial_setup":
    logger.warning("Workflow cannot proceed because configuration has not been applied.")
    # Warning is already displayed in the main column section