# app.py
"""
Streamlit frontend application for orchestrating an AI-driven SDLC workflow.

This application manages the user interface, state transitions, and calls
backend logic functions defined in SDLC.py to generate project artifacts.
"""



import streamlit as st
import os
import shutil
import logging
from datetime import datetime
import time
import zipfile # Standard library zipfile

# --- Import core logic from SDLC.py ---
try:
    import SDLC
    from SDLC import (
        # State and Models
        MainState, GeneratedCode, PlantUMLCode, TestCase, CodeFile, TestCases,
        # NEW: Initialization function
        initialize_llm_clients,
        # Workflow Functions
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
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Streamlit app logger configured.")

# --- Constants for Configuration ---
# Define available providers and their models
AVAILABLE_MODELS = {
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
    "Google": [
        "gemini-1.5-pro-latest", "gemini-1.5-flash-latest",
        "gemini-1.0-pro", "gemini-1.0-flash", "gemini-2.5-pro-exp-03-25", "gemini-2.0-flash", 
    ],
    "Anthropic": [
        # Use API Identifiers (usually include date)
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-5-haiku-latest", 
        "claude-3-5-sonnet-latest", 
        "claude-3-7-sonnet-latest"
    ],
    "xAI": [
        "grok-1", # Primary model available via API
         "grok-2-latest",
        "grok-3", 
        "grok-3-mini"
    ]
}
LLM_PROVIDERS = list(AVAILABLE_MODELS.keys())

# --- Define Cycle Order and Stage-to-Cycle Mapping ---
CYCLE_ORDER = [ "Requirements", "User Story", "Product Review", "Design", "UML", "Code Generation", "Review & Security", "Testing", "Quality Analysis", "Deployment" ]
STAGE_TO_CYCLE = { "initial_setup": "Requirements", "run_generate_questions": "Requirements", "collect_answers": "Requirements", "run_refine_prompt": "Requirements", "run_generate_initial_user_stories": "User Story", "run_generate_user_story_feedback": "User Story", "collect_user_story_human_feedback": "User Story", "run_refine_user_stories": "User Story", "collect_user_story_decision": "User Story", "run_generate_initial_product_review": "Product Review", "run_generate_product_review_feedback": "Product Review", "collect_product_review_human_feedback": "Product Review", "run_refine_product_review": "Product Review", "collect_product_review_decision": "Product Review", "run_generate_initial_design_doc": "Design", "run_generate_design_doc_feedback": "Design", "collect_design_doc_human_feedback": "Design", "run_refine_design_doc": "Design", "collect_design_doc_decision": "Design", "run_select_uml_diagrams": "UML", "run_generate_initial_uml_codes": "UML", "run_generate_uml_feedback": "UML", "collect_uml_human_feedback": "UML", "run_refine_uml_codes": "UML", "collect_uml_decision": "UML", "run_generate_initial_code": "Code Generation", "collect_code_human_input": "Code Generation", "run_web_search_code": "Code Generation", "run_generate_code_feedback": "Code Generation", "collect_code_human_feedback": "Code Generation", "run_refine_code": "Code Generation", "collect_code_decision": "Code Generation", "run_code_review": "Review & Security", "run_security_check": "Review & Security", "merge_review_security_feedback": "Review & Security", "run_refine_code_with_reviews": "Review & Security", "collect_review_security_decision": "Review & Security", "run_generate_initial_test_cases": "Testing", "run_generate_test_cases_feedback": "Testing", "collect_test_cases_human_feedback": "Testing", "run_refine_test_cases_and_code": "Testing", "run_save_testing_outputs": "Testing", "run_generate_initial_quality_analysis": "Quality Analysis", "run_generate_quality_feedback": "Quality Analysis", "collect_quality_human_feedback": "Quality Analysis", "run_refine_quality_and_code": "Quality Analysis", "collect_quality_decision": "Quality Analysis", "generate_initial_deployment": "Deployment", "run_generate_initial_deployment": "Deployment", "run_generate_deployment_feedback": "Deployment", "collect_deployment_human_feedback": "Deployment", "run_refine_deployment": "Deployment", "collect_deployment_decision": "Deployment", "END": "END" }

# --- Helper Functions ---
def initialize_state():
    """Initializes or resets the Streamlit session state."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_project_folder = f"ai_sdlc_project_{timestamp}"
    st.session_state.clear()
    st.session_state.stage = "initial_setup"
    st.session_state.workflow_state = {}
    st.session_state.user_input = ""
    st.session_state.display_content = "Welcome! Please configure API keys and project details to start."
    st.session_state.project_folder_base = default_project_folder
    st.session_state.current_prefs = ""
    st.session_state.zip_path = None; st.session_state.review_code_zip_path = None; st.session_state.testing_code_zip_path = None; st.session_state.final_code_zip_path = None
    # Configuration state
    st.session_state.config_applied = False
    st.session_state.selected_provider = LLM_PROVIDERS[0]
    st.session_state.selected_model = AVAILABLE_MODELS[LLM_PROVIDERS[0]][0]
    st.session_state.llm_api_key = ""
    st.session_state.tavily_api_key = ""
    st.session_state.llm_instance = None
    st.session_state.tavily_instance = None
    logger.info("Streamlit session state initialized.")

def update_display(new_content: str):
    st.session_state.display_content = new_content; logger.debug("Main display updated.")

def create_download_button(file_path: str, label: str, mime: str, key_suffix: str, help_text: str = ""):
    if not file_path or not isinstance(file_path, str): return
    abs_file_path = os.path.abspath(file_path)
    if os.path.exists(abs_file_path) and os.path.isfile(abs_file_path):
        try:
            with open(abs_file_path, "rb") as fp:
                safe_label = "".join(c for c in label if c.isalnum())[:10]
                button_key = f"dl_{key_suffix}_{safe_label}"
                st.download_button(label=f"Download {label}", data=fp, file_name=os.path.basename(abs_file_path), mime=mime, key=button_key, help=help_text or f"Download {label}")
        except FileNotFoundError: logger.warning(f"FileNotFound after check: {abs_file_path}")
        except Exception as e: logger.error(f"Error prepping download btn for {abs_file_path}: {e}", exc_info=True); st.warning(f"DL Button error for {label}: {e}")

def create_zip_and_download_button(folder_path_key: str, zip_path_key: str, zip_basename: str, button_label_prefix: str, sidebar_context):
    folder_path = st.session_state.workflow_state.get(folder_path_key)
    abs_folder_path = os.path.abspath(folder_path) if folder_path and isinstance(folder_path, str) else None
    if abs_folder_path and os.path.exists(abs_folder_path) and os.path.isdir(abs_folder_path):
        zip_label = f"Generate & Download {button_label_prefix} ZIP"
        existing_zip = st.session_state.get(zip_path_key)
        if existing_zip and os.path.exists(existing_zip): zip_label = f"Download {button_label_prefix} ZIP"
        zip_gen_key = f"zip_gen_{zip_path_key}"
        if sidebar_context.button(zip_label, key=zip_gen_key):
            with st.spinner(f"Creating {button_label_prefix} archive..."):
                try:
                    out_dir = os.path.dirname(abs_folder_path); archive_base = os.path.join(out_dir, zip_basename)
                    root_dir = os.path.dirname(abs_folder_path); base_dir = os.path.basename(abs_folder_path)
                    logger.info(f"Zipping: base='{archive_base}', root='{root_dir}', dir='{base_dir}'")
                    zip_file = archive_base + ".zip"
                    if os.path.exists(zip_file): 
                        try: os.remove(zip_file); logger.info(f"Removed old ZIP: {zip_file}") 
                        except Exception as del_e: logger.warning(f"Could not remove old ZIP {zip_file}: {del_e}")
                    archive_path = shutil.make_archive(base_name=archive_base, format='zip', root_dir=root_dir, base_dir=base_dir)
                    if not os.path.exists(archive_path): raise OSError(f"ZIP not found after make_archive: {archive_path}")
                    st.session_state[zip_path_key] = archive_path; st.success(f"{button_label_prefix} ZIP created!"); st.rerun()
                except Exception as e: sidebar_context.error(f"ZIP Error: {e}"); logger.error(f"ZIP failed for '{abs_folder_path}': {e}", exc_info=True)
        generated_zip = st.session_state.get(zip_path_key)
        if generated_zip and os.path.exists(generated_zip):
             try:
                 with open(generated_zip, "rb") as fp:
                     safe_prefix = "".join(c for c in button_label_prefix if c.isalnum())[:10]
                     dl_key = f"dl_zip_{zip_path_key}_{safe_prefix}"
                     sidebar_context.download_button(label=f"Download {button_label_prefix} ZIP", data=fp, file_name=os.path.basename(generated_zip), mime="application/zip", key=dl_key)
             except Exception as e: sidebar_context.warning(f"Error reading ZIP: {e}"); logger.error(f"Error reading ZIP {generated_zip}: {e}", exc_info=True)

# --- Initialization ---
if 'stage' not in st.session_state:
    initialize_state()

# --- Sidebar UI ---
with st.sidebar:
    st.header("AI SDLC Orchestrator")
    st.divider()

    # --- Configuration Section ---
    with st.expander("Configuration", expanded=not st.session_state.get('config_applied', False)):
        st.subheader("LLM & API Keys")
        selected_provider = st.selectbox("Select LLM Provider", options=LLM_PROVIDERS, key="selected_provider", help="Choose primary LLM provider.")
        available_models = AVAILABLE_MODELS.get(selected_provider, ["N/A"])
        selected_model = st.selectbox(f"Select Model ({selected_provider})", options=available_models, key="selected_model", help=f"Choose model from {selected_provider}.")
        llm_api_key_input = st.text_input(f"{selected_provider} API Key", type="password", key="llm_api_key_input", help=f"Enter API key for {selected_provider}.", value=st.session_state.get("llm_api_key",""))
        tavily_api_key_input = st.text_input("Tavily API Key (Optional)", type="password", key="tavily_api_key_input", help="Enter Tavily key for web search.", value=st.session_state.get("tavily_api_key",""))

        if st.button("Apply Configuration", key="apply_config"):
            with st.spinner("Initializing..."):
                st.session_state.llm_api_key = llm_api_key_input # Update actual keys used
                st.session_state.tavily_api_key = tavily_api_key_input
                llm_inst, tav_inst, error_msg = SDLC.initialize_llm_clients(
                    provider=st.session_state.selected_provider, model_name=st.session_state.selected_model,
                    llm_api_key=st.session_state.llm_api_key, tavily_api_key=st.session_state.tavily_api_key
                )
                if llm_inst:
                    st.session_state.llm_instance = llm_inst; st.session_state.tavily_instance = tav_inst; st.session_state.config_applied = True
                    st.success("Configuration Applied!"); logger.info("LLM/Tavily configured via UI.")
                    time.sleep(1); st.rerun() # Give time to see success, then rerun to potentially hide expander
                else:
                    st.session_state.config_applied = False; st.session_state.llm_instance = None; st.session_state.tavily_instance = None
                    error_display = f"Config Failed: {error_msg or 'Unknown error.'}"; st.error(error_display); logger.error(error_display)
    # --- END Configuration Section ---

    st.divider()
    st.header("Downloads"); st.caption("Generated artifacts and code snapshots.")
    # Documents
    st.markdown("---"); st.subheader("Documents")
    create_download_button(st.session_state.workflow_state.get("final_user_story_path"), "User Story", "text/markdown", "us")
    create_download_button(st.session_state.workflow_state.get("final_product_review_path"), "Product Review", "text/markdown", "pr")
    create_download_button(st.session_state.workflow_state.get("final_design_document_path"), "Design Document", "text/markdown", "dd")
    create_download_button(st.session_state.workflow_state.get("final_quality_analysis_path"), "QA Report", "text/markdown", "qa")
    create_download_button(st.session_state.workflow_state.get("final_deployment_path"), "Deployment Plan", "text/markdown", "deploy")
    # UML
    st.markdown("---"); st.subheader("UML Diagrams")
    uml_png_paths = st.session_state.workflow_state.get("final_uml_png_paths", []); uml_folder = st.session_state.workflow_state.get("final_uml_diagram_folder")
    if uml_png_paths:
        st.caption("Download PNG images:"); [create_download_button(p, f"UML: {'_'.join(os.path.basename(p).split('_')[2:]).replace('.png', '').replace('_', ' ').title() or f'Diagram {i+1}'}", "image/png", f"uml_{i}") for i, p in enumerate(uml_png_paths)]
    elif uml_folder and os.path.exists(uml_folder): st.caption("*No PNGs generated/found.*")
    else: st.caption("*UML diagrams not generated.*")
    # Code Snapshots
    st.markdown("---"); st.subheader("Code Snapshots (ZIP)"); st.caption("Code versions from key stages.")
    create_zip_and_download_button("review_code_snapshot_folder", "review_code_zip_path", "code_snapshot_review", "Review Stage Code", st.sidebar)
    create_zip_and_download_button("testing_passed_code_folder", "testing_code_zip_path", "code_snapshot_testing", "Testing Stage Code", st.sidebar)
    create_zip_and_download_button("final_code_folder", "final_code_zip_path", "code_snapshot_final", "Final Code", st.sidebar)
    st.divider()
    # Final Project ZIP
    if st.session_state.stage == "END":
        st.markdown("**Full Project Archive**"); proj_folder = st.session_state.workflow_state.get("project_folder"); abs_proj = os.path.abspath(proj_folder) if proj_folder and isinstance(proj_folder, str) else None
        if abs_proj and os.path.isdir(abs_proj):
            zip_label = "Generate & Download Full Project ZIP";
            if st.session_state.get("zip_path") and os.path.exists(st.session_state.zip_path): zip_label = "Download Full Project ZIP"
            if st.sidebar.button(zip_label, key="zip_gen_final"):
                with st.spinner("Creating full project archive..."):
                    try:
                        zip_base = os.path.abspath(st.session_state.project_folder_base); out_dir = os.path.dirname(zip_base); os.makedirs(out_dir, exist_ok=True)
                        root_dir = os.path.dirname(abs_proj); base_dir = os.path.basename(abs_proj)
                        logger.info(f"Zipping full project: base='{zip_base}', root='{root_dir}', dir='{base_dir}'")
                        zip_file = zip_base + ".zip";
                        if os.path.exists(zip_file): 
                            try: os.remove(zip_file); logger.info(f"Removed old final ZIP: {zip_file}") 
                            except Exception as del_e: logger.warning(f"Could not remove old final ZIP {zip_file}: {del_e}")
                        archive_path = shutil.make_archive(base_name=zip_base, format='zip', root_dir=root_dir, base_dir=base_dir)
                        if not os.path.exists(archive_path): raise OSError(f"Final ZIP failed: {archive_path} not found.")
                        st.session_state.zip_path = archive_path; st.success(f"Full project ZIP created: {os.path.basename(archive_path)}"); st.rerun()
                    except Exception as e: st.sidebar.error(f"Final ZIP Error: {e}"); logger.error(f"Final ZIP creation failed: {e}", exc_info=True)
            if st.session_state.get("zip_path") and os.path.exists(st.session_state.zip_path):
                 try:
                     with open(st.session_state.zip_path, "rb") as fp: st.sidebar.download_button(label="Download Full Project ZIP", data=fp, file_name=os.path.basename(st.session_state.zip_path), mime="application/zip", key="dl_zip_final")
                 except Exception as read_e: st.sidebar.warning(f"Error reading final ZIP: {read_e}"); logger.error(f"Error reading final ZIP {st.session_state.zip_path}: {read_e}", exc_info=True)
        elif proj_folder: st.sidebar.warning(f"Project folder '{proj_folder}' not found.")
        else: st.sidebar.caption("*Project folder undefined.*")
    st.divider()
    if st.sidebar.button("Restart Workflow", key="restart_sb", help="Clear progress and start over."):
        logger.info("Workflow restart requested."); initialize_state(); st.rerun()

# --- Main Layout & Controls ---
main_col, indicator_col = st.columns([4, 1])
input_needed = {"collect_answers", "collect_user_story_human_feedback", "collect_product_review_human_feedback", "collect_design_doc_human_feedback", "collect_uml_human_feedback", "collect_code_human_input", "collect_code_human_feedback", "merge_review_security_feedback", "collect_quality_human_feedback", "collect_deployment_human_feedback"}
decision_needed = {"collect_user_story_decision", "collect_product_review_decision", "collect_design_doc_decision", "collect_uml_decision", "collect_code_decision", "collect_review_security_decision", "collect_quality_decision", "collect_deployment_decision"}
current_stage = st.session_state.stage
show_input_box = current_stage in input_needed; show_decision_btns = current_stage in decision_needed; show_test_fb = current_stage == "collect_test_cases_human_feedback"; show_setup_form = current_stage == "initial_setup"; show_deploy_prefs = current_stage == "generate_initial_deployment"

with main_col:
    st.header(f"Stage: {current_stage.replace('_', ' ').title()}")
    st.markdown("### AI Output / Current Task:")
    display_area = st.container(height=400, border=False)
    with display_area: st.markdown(str(st.session_state.get("display_content", "Initializing...")), unsafe_allow_html=False)
    st.divider()

    # --- GATING ---
    if not st.session_state.get('config_applied', False):
        st.warning("👈 Please configure LLM Provider & API Keys in the sidebar first.")
    else:
        # --- Workflow UI ---
        if show_setup_form:
            with st.form("setup_form"):
                st.markdown("### Project Configuration")
                proj_folder = st.text_input("Project Folder Name", value=st.session_state.project_folder_base, help="Directory name. No spaces/special chars.")
                proj_name = st.text_input("Project Description", value="Web Task Manager Example")
                proj_cat = st.text_input("Category", value="Web Development")
                proj_subcat = st.text_input("Subcategory", value="Productivity Tool")
                proj_lang = st.text_input("Coding Language", value="Python")
                min_iter = st.number_input("Min Q&A Rounds", 1, 5, 2)
                submitted = st.form_submit_button("Start Workflow")
                if submitted:
                    if not all([proj_folder, proj_name, proj_cat, proj_subcat, proj_lang]): st.error("Fill all fields.")
                    elif any(c in proj_folder for c in r'/\:*?"<>| '): st.error("Invalid chars in folder name.")
                    else:
                        try:
                            abs_proj = os.path.abspath(proj_folder)
                            if os.path.exists(abs_proj) and not os.path.isdir(abs_proj): st.error(f"File exists: '{proj_folder}'.")
                            else:
                                if os.path.exists(abs_proj): st.warning(f"Folder exists: '{abs_proj}'.")
                                else: os.makedirs(abs_proj, exist_ok=True); st.success(f"Folder ready: '{abs_proj}'")
                                # Initialize state including LLM/Tavily instances
                                initial_workflow_state = { "llm_instance": st.session_state.llm_instance, "tavily_instance": st.session_state.tavily_instance, "messages": [SDLC.HumanMessage(content=f"Setup:\nProject:{proj_name}\nCat:{proj_cat}\nSub:{proj_subcat}\nLang:{proj_lang}")], "project_folder": proj_folder, "project": proj_name, "category": proj_cat, "subcategory": proj_subcat, "coding_language": proj_lang, "user_input_iteration": 0, "user_input_min_iterations": min_iter, **{k: None for k in SDLC.MainState.__annotations__ if k not in ["llm_instance", "tavily_instance", "messages", "project_folder", "project", "category", "subcategory", "coding_language", "user_input_iteration", "user_input_min_iterations"]}, "user_input_questions": [], "user_input_answers": [], "user_input_done": False, "final_uml_codes": [], "final_code_files": [], "final_test_code_files": [], "test_cases_current": [], "uml_selected_diagrams": [], "uml_current_codes": [], "uml_feedback": {}, "uml_human_feedback": {}, "final_uml_png_paths": [], "code_current": SDLC.GeneratedCode(files=[], instructions=""), "user_story_done": False, "product_review_done": False, "design_doc_done": False, "uml_done": False, "code_done": False, "review_security_done": False, "test_cases_passed": False, "quality_done": False, "deployment_done": False }
                                st.session_state.workflow_state = initial_workflow_state; st.session_state.project_folder_base = proj_folder; st.session_state.stage = "run_generate_questions"; logger.info(f"Setup complete. Starting workflow for '{proj_name}'."); st.rerun()
                        except OSError as oe: st.error(f"Folder error '{proj_folder}': {oe}."); logger.error(f"OSError creating folder: {oe}", exc_info=True)
                        except Exception as e: st.error(f"Setup error: {e}"); logger.error(f"Setup error: {e}", exc_info=True)

        elif show_deploy_prefs:
             with st.form("deploy_prefs_form"):
                 st.markdown("### Deployment Preferences"); st.info("Specify target environment.")
                 deploy_target = st.selectbox("Target", ["Localhost", "Docker", "AWS EC2", "AWS Lambda", "GCP Run", "Azure App Service", "Other"], key="deploy_target")
                 deploy_details = st.text_area("Details:", height=100, key="deploy_details", placeholder="e.g., AWS region, Nginx, DB connection")
                 submitted = st.form_submit_button("Generate Plan")
                 if submitted: prefs = f"Target: {deploy_target}\nDetails: {deploy_details}"; st.session_state.current_prefs = prefs; st.session_state.stage = "run_generate_initial_deployment"; logger.info(f"Deploy prefs: {deploy_target}"); st.rerun()

        elif show_input_box:
            input_key = f"input_{current_stage}"; user_val = st.text_area("Input / Feedback:", height=150, key=input_key, value=st.session_state.get('user_input', ''), help="Provide feedback/answers. For Q&A, use #DONE when finished.")
            submit_key = f"submit_{current_stage}"
            if st.button("Submit", key=submit_key):
                user_text = user_val.strip(); state = st.session_state.workflow_state
                if not isinstance(state, dict): st.error("State invalid."); logger.critical("workflow_state invalid."); initialize_state(); st.rerun()
                try:
                    next_stage = None; state['messages'] = state.get('messages', [])
                    map = { "collect_answers": ("user_input_answers", "run_generate_questions", True), "collect_user_story_human_feedback": ("user_story_human_feedback", "run_refine_user_stories", False), "collect_product_review_human_feedback": ("product_review_human_feedback", "run_refine_product_review", False), "collect_design_doc_human_feedback": ("design_doc_human_feedback", "run_refine_design_doc", False), "collect_uml_human_feedback": ("uml_human_feedback", "run_refine_uml_codes", False), "collect_code_human_input": ("code_human_input", "run_web_search_code", False), "collect_code_human_feedback": ("code_human_feedback", "run_refine_code", False), "merge_review_security_feedback": ("review_security_human_feedback", "run_refine_code_with_reviews", False), "collect_quality_human_feedback": ("quality_human_feedback", "run_refine_quality_and_code", False), "collect_deployment_human_feedback": ("deployment_human_feedback", "run_refine_deployment", False) }
                    if current_stage in map:
                        key, next_run, is_list = map[current_stage]
                        if is_list: state[key] = state.get(key, []) + [user_text]
                        elif key == "uml_human_feedback": state[key] = {"all": user_text}
                        else: state[key] = user_text
                        state["messages"].append(SDLC.HumanMessage(content=user_text)); next_stage = next_run
                        if current_stage == "collect_answers":
                            state["user_input_iteration"] = state.get("user_input_iteration", 0) + 1; min_i = state.get("user_input_min_iterations", 1)
                            lines = [l for l in user_text.splitlines() if l.strip()]; last = lines[-1].strip().upper() if lines else ""; done = "#DONE" in last
                            logger.debug(f"Q&A Iter:{state['user_input_iteration']}/{min_i}. Done:{done}")
                            if state["user_input_iteration"] >= min_i and done: state["user_input_done"] = True; next_stage = "run_refine_prompt"; logger.info("Q&A done.")
                            else: state["user_input_done"] = False; logger.info("Continuing Q&A.")
                        if current_stage == "collect_code_human_input" and not state.get('tavily_instance'): state["code_web_search_results"] = "Skipped (Tavily N/A)"; next_stage = "run_generate_code_feedback"; logger.info("Skipping web search.")
                    else: st.error(f"Input logic undefined: {current_stage}"); logger.error(f"Input logic missing: {current_stage}")
                    if next_stage: st.session_state.workflow_state = state; st.session_state.user_input = ""; st.session_state.stage = next_stage; logger.info(f"Input '{current_stage}'. -> '{next_stage}'."); st.rerun()
                except Exception as e: st.error(f"Input error: {e}"); logger.error(f"Input error {current_stage}: {e}", exc_info=True)

        elif show_test_fb:
            st.markdown("### Test Execution & Feedback"); st.info("Execute tests, provide feedback & outcome.")
            ai_fb = st.session_state.workflow_state.get("test_cases_feedback", "*N/A*")
            with st.expander("AI Feedback on Tests"): st.markdown(ai_fb)
            human_fb = st.text_area("Feedback & Results:", height=150, key="tc_fb")
            pf_status = st.radio("Core Tests Passed?", ("PASS", "FAIL"), index=1, key="tc_pf", horizontal=True)
            c1, c2 = st.columns(2)
            with c1: # Submit Results
                if st.button("Submit Results", key="submit_test"):
                    state = st.session_state.workflow_state; state['messages'] = state.get('messages', [])
                    fb = f"Res: {pf_status}\nFB:{human_fb}"; state["test_cases_human_feedback"] = fb; state["test_cases_passed"] = (pf_status == "PASS")
                    state["messages"].append(SDLC.HumanMessage(content=fb)); logger.info(f"Test res: {pf_status}.")
                    next_s = "run_save_testing_outputs" if state["test_cases_passed"] else "run_refine_test_cases_and_code"
                    st.session_state.stage = next_s; st.session_state.workflow_state = state; st.rerun()
            with c2: # Regen Code
                if st.button("Submit & Regenerate Code", key="regen_test"):
                    state = st.session_state.workflow_state; state['messages'] = state.get('messages', [])
                    fb = f"Res: {pf_status}\nFB:{human_fb}\nDecision: Regen Code."; state["test_cases_human_feedback"] = fb; state["test_cases_passed"] = False
                    state["messages"].append(SDLC.HumanMessage(content=fb)); logger.info(f"Test FB ({pf_status}), regen code.")
                    ctx = f"From Testing:\nRes:{pf_status}\nFB:{human_fb}\nAI Test FB:{ai_fb}\nRegen code.";
                    state["code_human_input"] = ctx; state["messages"].append(SDLC.HumanMessage(content=f"Regen Context: {ctx[:200]}..."))
                    st.session_state.stage = "collect_code_human_input"; st.session_state.workflow_state = state; st.rerun()

        elif show_decision_btns:
            st.markdown("### Decision Point"); st.info("Review output. Refine or proceed.")
            refine_map = { "collect_user_story_decision": "run_generate_user_story_feedback", "collect_product_review_decision": "run_generate_product_review_feedback", "collect_design_doc_decision": "run_generate_design_doc_feedback", "collect_uml_decision": "run_generate_uml_feedback", "collect_code_decision": "collect_code_human_input", "collect_review_security_decision": "run_code_review", "collect_quality_decision": "run_generate_quality_feedback", "collect_deployment_decision": "run_generate_deployment_feedback", }
            proceed_map = { "collect_user_story_decision": ("user_story_done", SDLC.save_final_user_story, "run_generate_initial_product_review"), "collect_product_review_decision": ("product_review_done", SDLC.save_final_product_review, "run_generate_initial_design_doc"), "collect_design_doc_decision": ("design_doc_done", SDLC.save_final_design_doc, "run_select_uml_diagrams"), "collect_uml_decision": ("uml_done", SDLC.save_final_uml_diagrams, "run_generate_initial_code"), "collect_code_decision": ("code_done", None, "run_code_review"), "collect_review_security_decision": ("review_security_done", SDLC.save_review_security_outputs, "run_generate_initial_test_cases"), "collect_quality_decision": ("quality_done", SDLC.save_final_quality_analysis, "generate_initial_deployment"), "collect_deployment_decision": ("deployment_done", SDLC.save_final_deployment_plan, "END"), }
            cols = st.columns(3 if current_stage == "collect_quality_decision" else 2)
            with cols[0]: # Refine
                if st.button("Refine", key=f"refine_{current_stage}"):
                    if current_stage in refine_map: state = st.session_state.workflow_state; done_key = current_stage.replace("collect_", "").replace("_decision", "_done"); state[done_key]=False; next_refine = refine_map[current_stage]; st.session_state.stage = next_refine; st.session_state.workflow_state = state; logger.info(f"Decision: Refine '{current_stage}'. -> '{next_refine}'."); st.rerun()
                    else: st.warning("Refine undefined."); logger.warning(f"Refine undefined for {current_stage}")
            with cols[1]: # Proceed
                if st.button("Proceed", key=f"proceed_{current_stage}"):
                    if current_stage in proceed_map:
                        state = st.session_state.workflow_state; done_key, save_func, next_stage = proceed_map[current_stage]; err = False
                        try:
                            state[done_key] = True; logger.info(f"Decision: Proceed from '{current_stage}'. Marked '{done_key}'=True.")
                            if current_stage == "collect_code_decision": # Promote code
                                 code_obj = state.get("code_current");
                                 if code_obj and isinstance(code_obj, SDLC.GeneratedCode) and code_obj.files: state["final_code_files"] = code_obj.files; logger.info(f"Promoted {len(code_obj.files)} files.")
                                 else: st.warning("Proceed code gen, but 'code_current' invalid."); logger.warning("Proceed code gen, invalid."); state["final_code_files"] = []
                            if save_func: # Save artifact
                                fn = getattr(save_func, '__name__', 'save_func'); logger.info(f"Saving: {fn}")
                                with st.spinner(f"Saving..."): state = save_func(state); st.session_state.workflow_state = state
                                # Post-save check (basic)
                                map_paths = { SDLC.save_final_user_story: "final_user_story_path", SDLC.save_final_product_review: "final_product_review_path", SDLC.save_final_design_doc: "final_design_document_path", SDLC.save_final_uml_diagrams: "final_uml_diagram_folder", SDLC.save_review_security_outputs: "final_review_security_folder", SDLC.save_testing_outputs: "final_testing_folder", SDLC.save_final_quality_analysis: "final_quality_analysis_path", SDLC.save_final_deployment_plan: "final_deployment_path", }; path_key = map_paths.get(save_func); path_val = state.get(path_key) if path_key else True; qa_ok = True if save_func != SDLC.save_final_quality_analysis else bool(state.get("final_code_folder"))
                                if (path_key and not path_val) or not qa_ok: st.warning(f"Saving for '{current_stage}' may have failed."); logger.warning(f"Save check failed for {fn}.")
                                else: logger.info(f"Save {fn} ok.")
                        except Exception as e: st.error(f"Finalize error '{current_stage}': {e}"); logger.error(f"Proceed error {current_stage}: {e}", exc_info=True); err = True
                        if not err: st.session_state.stage = next_stage; logger.info(f"-> {next_stage}"); st.rerun()
                    else: st.warning("Proceed undefined."); logger.warning(f"Proceed undefined for {current_stage}")
            if current_stage == "collect_quality_decision": # QA Regen
                with cols[2]:
                    if st.button("Regen Code", key="regen_qa"):
                        state = st.session_state.workflow_state; state['messages'] = state.get('messages', []); logger.info("Decision: Regen Code from QA.")
                        qa_sum = state.get('quality_current_analysis', 'N/A')[:1000]
                        ctx = f"From QA:\nFindings:\n{qa_sum}...\nRegen code."; state["code_human_input"] = ctx; state["messages"].append(SDLC.HumanMessage(content=f"Regen Context: {ctx[:200]}..."))
                        st.session_state.stage = "collect_code_human_input"; st.session_state.workflow_state = state; st.rerun()

        elif current_stage == "END":
            st.balloons(); final_msg = "## Workflow Completed!\n\nUse sidebar downloads or restart."; update_display(final_msg); st.markdown(final_msg); logger.info("Workflow END.")
        elif not current_stage.startswith("run_"): st.error(f"Unknown UI stage: '{current_stage}'. Restart?"); logger.error(f"Unknown UI stage: {current_stage}")

# --- Cycle Indicator ---
with indicator_col:
    st.subheader("Workflow Cycles")
    current_major = STAGE_TO_CYCLE.get(current_stage, "Unknown"); current_idx = -1
    if current_major in CYCLE_ORDER: current_idx = CYCLE_ORDER.index(current_major)
    elif current_major == "END": current_idx = len(CYCLE_ORDER)
    st.markdown("""<style>.cycle-item { margin-bottom: 0.75em; transition: all 0.3s ease-in-out; padding: 4px 0; } .cycle-past { opacity: 0.4; font-size: 0.9em; padding-left: 15px; border-left: 4px solid #ccc; } .cycle-current { font-weight: bold; font-size: 1.1em; color: #008080; border-left: 4px solid #008080; padding-left: 11px;} .cycle-future { opacity: 0.7; font-size: 0.95em; padding-left: 15px; border-left: 4px solid #eee; } .cycle-end { font-weight: bold; font-size: 1.0em; color: #4CAF50; border-left: 4px solid #4CAF50; padding-left: 11px; }</style>""", unsafe_allow_html=True)
    win_before, win_after = 2, 4; start = max(0, current_idx - win_before); end = min(len(CYCLE_ORDER), start + win_before + win_after); start = max(0, end - (win_before + win_after))
    for i, name in enumerate(CYCLE_ORDER):
        if start <= i < end :
            css = "cycle-item"; display = name
            if i < current_idx: css += " cycle-past"
            elif i == current_idx and current_major != "END": css += " cycle-current"; display = f"➡️ {name}"
            else: css += " cycle-future"
            st.markdown(f'<div class="{css}">{display}</div>', unsafe_allow_html=True)
    if current_major == "END": st.markdown(f'<div class="cycle-item cycle-end">✅ Workflow End</div>', unsafe_allow_html=True)

# --- Invisible Stages Logic ---
# --- CORRECTED run_workflow_step function for app.py ---

def run_workflow_step(func, next_display_stage, *args):
    """
    Executes a backend workflow function, updates state and display content,
    and transitions to the next appropriate UI stage.
    """
    state = st.session_state.workflow_state
    # Ensure state is a dictionary before proceeding
    if not isinstance(state, dict):
        st.error("Critical Error: workflow_state is invalid. Restarting.")
        logger.critical("run_workflow_step called with invalid state type. Forcing restart.")
        initialize_state(); st.rerun(); return

    func_name = getattr(func, '__name__', repr(func))
    # Handle specific case for lambda function name used in deployment
    if func_name == '<lambda>' and next_display_stage == "run_generate_deployment_feedback":
        func_name = "generate_initial_deployment"

    logger.info(f"Attempting to run workflow function: {func_name}")

    try:
        # Show spinner during execution
        spinner_message = f"Running: {func_name.replace('_',' ').title()}..."
        with st.spinner(spinner_message):
            # --- Check for LLM instance before calling ---
            # List of functions that DON'T require an LLM instance
            non_llm_funcs = {
                SDLC.save_final_user_story, SDLC.save_final_product_review,
                SDLC.save_final_design_doc, SDLC.save_final_uml_diagrams,
                SDLC.save_review_security_outputs, SDLC.save_testing_outputs,
                SDLC.save_final_quality_analysis, SDLC.save_final_deployment_plan,
                SDLC.web_search_code # web_search_code checks internally for tavily instance
            }
            if func not in non_llm_funcs and not state.get('llm_instance'):
                raise ConnectionError("LLM is not configured or initialized in the current state.")

            # --- Check for Tavily if function needs it ---
            if func == SDLC.web_search_code and not state.get('tavily_instance'):
                 logger.warning("Web search called but Tavily instance not found in state. Skipping.")
                 # Update state to reflect skipped search and proceed
                 state["code_web_search_results"] = "Skipped (Tavily client not configured/initialized in state)"
                 if 'messages' not in state: state['messages'] = []
                 state["messages"].append(AIMessage(content="Web Search: Skipped (Tavily not available in state)"))
                 st.session_state.workflow_state = state
                 # IMPORTANT: Determine the correct next stage if web search is skipped
                 # In the map, run_web_search_code -> run_generate_code_feedback
                 # So, we directly set the next_display_stage to that
                 st.session_state.stage = "run_generate_code_feedback"
                 logger.info("Skipping web search, directly transitioning to 'run_generate_code_feedback'")
                 st.rerun()
                 return # Stop this execution

            # Special handling for review -> security chain
            if func == SDLC.code_review:
                 logger.info("Executing code review step...")
                 state = SDLC.code_review(state) # Call the review function
                 st.session_state.workflow_state = state # Update state immediately
                 st.session_state.stage = "run_security_check" # Set next internal stage
                 logger.info("Code review complete, triggering security check immediately.")
                 st.rerun() # Rerun to execute the security check step defined in workflow_map
                 return # Stop current function execution here

            # Normal execution
            updated_state = func(state, *args)

        # Ensure the function returned a dictionary (the updated state)
        if not isinstance(updated_state, dict):
             logger.error(f"Function {func_name} did not return a dictionary state. Returned type: {type(updated_state)}")
             st.error(f"Workflow Error: Step '{func_name}' failed internally (invalid return type).")
             return # Avoid proceeding with invalid state

        st.session_state.workflow_state = updated_state; logger.debug(f"State updated after {func_name}.")

        # --- Determine Display Content based on the completed step ---
        # Default fallback message
        display_text = f"Completed: {func_name}. Preparing next step..."

        # --- FULL if/elif block for customizing display_text ---
        if func == SDLC.generate_questions:
            questions = updated_state.get("user_input_questions", [])
            num_q = len(questions); start_index = max(0, num_q - 5)
            latest_questions = questions[start_index:]
            if latest_questions:
                min_iter = updated_state.get('user_input_min_iterations', 1)
                current_iter = updated_state.get("user_input_iteration", 0) # Iteration count is updated *after* answer submission
                min_iter_msg = f"(Minimum {min_iter} rounds required)" if current_iter < min_iter else ""
                display_text = f"Please answer the following questions {min_iter_msg}:\n\n" + "\n".join(f"- {q}" for q in latest_questions)
                if current_iter + 1 >= min_iter: # Check if *next* iteration meets minimum
                     display_text += "\n\n*Type '#DONE' on the last line when finished.*"
            else:
                # Handle case where LLM returns no questions (e.g., if requirements clear)
                display_text = "AI indicates requirements may be clear. Proceeding to refine prompt..."
                # Force transition if no questions were generated unexpectedly
                next_display_stage = "run_refine_prompt"

        elif func == SDLC.refine_prompt:
            display_text = "**Refined Project Prompt:**\n\n```\n{}\n```\n\n*Proceeding to generate User Stories...*".format(updated_state.get('refined_prompt', 'N/A'))

        elif func in [SDLC.generate_initial_user_stories, SDLC.refine_user_stories]:
            us_current = updated_state.get('user_story_current', 'N/A')
            display_text = f"**Current User Stories:**\n\n{us_current}" # Use markdown directly if it contains formatting
            if func == SDLC.refine_user_stories:
                 display_text += "\n\n*Please review the refined stories and decide whether to refine further or proceed.*"
                 next_display_stage = "collect_user_story_decision" # Correct next stage after refinement
            else:
                 display_text += "\n\n*Generating AI feedback on these stories...*"
                 # next_display_stage remains as passed ("run_generate_user_story_feedback")

        elif func == SDLC.generate_user_story_feedback:
            feedback = updated_state.get('user_story_feedback', 'N/A')
            display_text = f"**AI Feedback (User Stories):**\n\n{feedback}\n\n*Please provide your feedback on the stories and the AI's assessment.*"

        elif func in [SDLC.generate_initial_product_review, SDLC.refine_product_review]:
            review_current = updated_state.get('product_review_current', 'N/A')
            display_text = f"**Current Product Review:**\n\n{review_current}"
            if func == SDLC.refine_product_review:
                 display_text += "\n\n*Please review the refined PO review and decide whether to refine further or proceed.*"
                 next_display_stage = "collect_product_review_decision"
            else:
                 display_text += "\n\n*Generating AI feedback on this review...*"

        elif func == SDLC.generate_product_review_feedback:
            feedback = updated_state.get('product_review_feedback', 'N/A')
            display_text = f"**AI Feedback (Product Review):**\n\n{feedback}\n\n*Please provide your feedback on the review and the AI's assessment.*"

        elif func in [SDLC.generate_initial_design_doc, SDLC.refine_design_doc]:
            doc_current = updated_state.get('design_doc_current', 'N/A')
            display_text = f"**Current Design Document:**\n\n{doc_current}"
            if func == SDLC.refine_design_doc:
                 display_text += "\n\n*Please review the refined design document and decide whether to refine further or proceed.*"
                 next_display_stage = "collect_design_doc_decision"
            else:
                 display_text += "\n\n*Generating AI feedback on this design...*"

        elif func == SDLC.generate_design_doc_feedback:
            feedback = updated_state.get('design_doc_feedback', 'N/A')
            display_text = f"**AI Feedback (Design Doc):**\n\n{feedback}\n\n*Please provide your feedback on the design and the AI's assessment.*"

        elif func == SDLC.select_uml_diagrams:
            selected = updated_state.get('uml_selected_diagrams', [])
            messages = updated_state.get('messages', [])
            justification_msg = messages[-1].content if messages else "Selection complete." # Try to get justification from last msg
            display_text = f"**Selected UML Diagram Types:**\n\n{justification_msg}\n\n*Generating initial diagrams...*"

        elif func in [SDLC.generate_initial_uml_codes, SDLC.refine_uml_codes]:
            codes = updated_state.get('uml_current_codes', [])
            codes_display = "\n\n".join([f"**{c.diagram_type}**:\n```plantuml\n{c.code}\n```" for c in codes])
            status = "Refined" if func == SDLC.refine_uml_codes else "Generated"
            display_text = f"**{status} UML Codes:**\n\n{codes_display}"
            if func == SDLC.refine_uml_codes:
                 display_text += "\n\n*Please review the refined diagrams and decide whether to refine further or proceed.*"
                 next_display_stage = "collect_uml_decision"
            else:
                 display_text += "\n\n*Generating AI feedback on these diagrams...*"

        elif func == SDLC.generate_uml_feedback:
            feedback_dict = updated_state.get('uml_feedback', {})
            feedback_display = "\n\n".join([f"**Feedback for {dt}:**\n{fb}" for dt, fb in feedback_dict.items()])
            display_text = f"**AI Feedback on UML Diagrams:**\n\n{feedback_display}\n\n*Please provide your overall feedback on the diagrams and the AI assessment.*"

        elif func in [SDLC.generate_initial_code, SDLC.refine_code, SDLC.refine_code_with_reviews]:
             code_data = updated_state.get("code_current")
             stage_desc = "Initial" if func == SDLC.generate_initial_code else "Refined"
             if code_data and isinstance(code_data, SDLC.GeneratedCode):
                 files_display=[]; total_len, max_len = 0, 3000
                 for f in code_data.files:
                     s=f.content[:max_len-total_len]; file_disp = f"**{f.filename}**:\n```\n{s}{'...' if len(f.content) > len(s) else ''}\n```"
                     files_display.append(file_disp); total_len += len(s) + len(f.filename)
                     if total_len >= max_len: files_display.append("\n*... (Code truncated)*"); break
                 num_files = len(code_data.files); instr = code_data.instructions
                 display_text = f"**{stage_desc} Code ({num_files} files):**\n{''.join(files_display)}\n\n**Setup/Run:**\n```\n{instr}\n```"
                 if func == SDLC.generate_initial_code: display_text += "\n\n*Attempt run & provide feedback.*"; next_display_stage = "collect_code_human_input"
                 elif func == SDLC.refine_code: display_text += "\n\n*Review refined code.*"; next_display_stage = "collect_code_decision"
                 elif func == SDLC.refine_code_with_reviews: display_text += "\n\n*Review code refined post-review.*"; next_display_stage = "collect_review_security_decision"
             else: display_text = f"{stage_desc} code step done, but no valid code data."; logger.error(f"{func_name} invalid code data.")

        elif func == SDLC.web_search_code:
            results = updated_state.get('code_web_search_results', 'N/A')
            display_text = f"**Web Search Results:**\n\n{results}\n\n*Generating AI feedback...*"

        elif func == SDLC.generate_code_feedback:
            feedback = updated_state.get('code_feedback', 'N/A')
            display_text = f"**AI Code Feedback:**\n\n{feedback}\n\n*Please provide your comments.*"

        elif func == SDLC.security_check: # Display after review->sec chain
             review_fb = updated_state.get('code_review_current_feedback', 'N/A'); security_fb = updated_state.get('security_current_feedback', 'N/A')
             display_text=f"**Code Review:**\n```\n{review_fb}\n```\n\n**Security Check:**\n```\n{security_fb}\n```\n\n*Provide overall feedback.*"

        elif func == SDLC.generate_initial_test_cases:
             tests = updated_state.get('test_cases_current', [])
             tests_d = "\n\n".join([f"**{tc.description}**:\n  - In:`{tc.input_data}`\n  - Exp:`{tc.expected_output}`" for tc in tests])
             display_text=f"**Generated Tests ({len(tests)}):**\n\n{tests_d}\n\n*Generating AI feedback...*"

        elif func == SDLC.generate_test_cases_feedback:
            feedback = updated_state.get('test_cases_feedback', 'N/A')
            display_text=f"**AI Test Case Feedback:**\n\n{feedback}\n\n*Execute tests & provide results.*"

        elif func == SDLC.refine_test_cases_and_code:
            tests = updated_state.get('test_cases_current', []); files_count = len(updated_state.get('final_code_files', []))
            tests_d = "\n\n".join([f"**{tc.description}**:\n  - In:`{tc.input_data}`\n  - Exp:`{tc.expected_output}`" for tc in tests])
            display_text = f"**Refined Tests & Code ({files_count} files):**\n\n*Code/tests updated.*\n\n**Refined Tests ({len(tests)}):**\n{tests_d}\n\n*Execute tests again.*"
            next_display_stage = "collect_test_cases_human_feedback" # Always collect feedback after refine

        elif func == SDLC.save_testing_outputs:
             display_text = f"Test results saved (PASS). Generating QA report..."
             # next_display_stage remains as passed ("run_generate_initial_quality_analysis")

        elif func in [SDLC.generate_initial_quality_analysis, SDLC.refine_quality_and_code]:
            report = updated_state.get('quality_current_analysis', 'N/A')
            display_text=f"**Quality Analysis Report:**\n\n{report}"
            if func == SDLC.refine_quality_and_code: display_text += "\n\n*Review refined QA report.*"; next_display_stage = "collect_quality_decision"
            else: display_text += "\n\n*Generating AI feedback...*"

        elif func == SDLC.generate_quality_feedback:
            feedback = updated_state.get('quality_feedback', 'N/A')
            display_text=f"**AI Feedback on QA Report:**\n\n{feedback}\n\n*Provide your feedback.*"

        elif func_name == "generate_initial_deployment": # Handle lambda
             plan = updated_state.get('deployment_current_process', 'N/A')
             display_text = f"**Initial Deployment Plan:**\n```\n{plan}\n```\n\n*Generating AI feedback...*"
             # next_display_stage remains as passed ("run_generate_deployment_feedback")

        elif func == SDLC.refine_deployment:
             plan = updated_state.get('deployment_current_process', 'N/A')
             display_text = f"**Refined Deployment Plan:**\n```\n{plan}\n```\n\n*Review refined plan.*"
             next_display_stage = "collect_deployment_decision"

        elif func == SDLC.generate_deployment_feedback:
            feedback = updated_state.get('deployment_feedback', 'N/A')
            display_text=f"**AI Feedback on Deployment Plan:**\n\n{feedback}\n\n*Provide your feedback.*"

        # Handle Save Functions (Generic Message)
        elif func in [SDLC.save_final_user_story, SDLC.save_final_product_review, SDLC.save_final_design_doc, SDLC.save_final_uml_diagrams, SDLC.save_review_security_outputs, SDLC.save_testing_outputs, SDLC.save_final_quality_analysis, SDLC.save_final_deployment_plan]:
            artifact_name = func.__name__.replace('save_final_','').replace('_',' ')
            # Use the next_display_stage passed into the function
            next_action_stage_name = next_display_stage
            next_action_desc = STAGE_TO_CYCLE.get(next_action_stage_name, next_action_stage_name).replace('_',' ').title()
            if next_action_stage_name == "generate_initial_deployment": next_action_desc = "Deployment Preferences"
            elif next_action_stage_name == "END": next_action_desc = "Workflow Completion"
            display_text = f"Saved {artifact_name}. Starting next: {next_action_desc}..."
            logger.info(f"Artifact saved: {artifact_name}. Next: {next_action_desc}")
        # --- END FULL DISPLAY MAPPING ---

        # --- Update display content and transition ---
        update_display(display_text)
        st.session_state.stage = next_display_stage
        logger.info(f"Workflow function '{func_name}' completed. Transitioning UI to stage: '{next_display_stage}'")
        st.rerun() # Refresh the UI

    except ConnectionError as ce:
        error_msg = f"Connection Error during '{func_name}': {ce}. Check API keys/network. Workflow stopped."
        st.error(error_msg); logger.critical(error_msg, exc_info=True); st.stop()
    except Exception as e:
        error_msg = f"Error during step '{func_name}': {e}"
        st.error(error_msg); logger.error(f"Error executing {func_name}: {e}", exc_info=True)
        retry_key = f"retry_{func_name}_{int(time.time())}"
        if st.button("Retry Last Step", key=retry_key): logger.info(f"User retry: {func_name}"); st.rerun()

# --- Workflow Map Definition (No change) ---
workflow_map = { "run_generate_questions": (SDLC.generate_questions, "collect_answers"), "run_refine_prompt": (SDLC.refine_prompt, "run_generate_initial_user_stories"), "run_generate_initial_user_stories": (SDLC.generate_initial_user_stories, "run_generate_user_story_feedback"), "run_generate_user_story_feedback": (SDLC.generate_user_story_feedback, "collect_user_story_human_feedback"), "run_refine_user_stories": (SDLC.refine_user_stories, "collect_user_story_decision"), "run_generate_initial_product_review": (SDLC.generate_initial_product_review, "run_generate_product_review_feedback"), "run_generate_product_review_feedback": (SDLC.generate_product_review_feedback, "collect_product_review_human_feedback"), "run_refine_product_review": (SDLC.refine_product_review, "collect_product_review_decision"), "run_generate_initial_design_doc": (SDLC.generate_initial_design_doc, "run_generate_design_doc_feedback"), "run_generate_design_doc_feedback": (SDLC.generate_design_doc_feedback, "collect_design_doc_human_feedback"), "run_refine_design_doc": (SDLC.refine_design_doc, "collect_design_doc_decision"), "run_select_uml_diagrams": (SDLC.select_uml_diagrams, "run_generate_initial_uml_codes"), "run_generate_initial_uml_codes": (SDLC.generate_initial_uml_codes, "run_generate_uml_feedback"), "run_generate_uml_feedback": (SDLC.generate_uml_feedback, "collect_uml_human_feedback"), "run_refine_uml_codes": (SDLC.refine_uml_codes, "collect_uml_decision"), "run_generate_initial_code": (SDLC.generate_initial_code, "collect_code_human_input"), "run_web_search_code": (SDLC.web_search_code, "run_generate_code_feedback"), "run_generate_code_feedback": (SDLC.generate_code_feedback, "collect_code_human_feedback"), "run_refine_code": (SDLC.refine_code, "collect_code_decision"), "run_code_review": (SDLC.code_review, "run_security_check"), "run_security_check": (SDLC.security_check, "merge_review_security_feedback"), "run_refine_code_with_reviews": (SDLC.refine_code_with_reviews, "collect_review_security_decision"), "run_generate_initial_test_cases": (SDLC.generate_initial_test_cases, "run_generate_test_cases_feedback"), "run_generate_test_cases_feedback": (SDLC.generate_test_cases_feedback, "collect_test_cases_human_feedback"), "run_refine_test_cases_and_code": (SDLC.refine_test_cases_and_code, "collect_test_cases_human_feedback"), "run_save_testing_outputs": (SDLC.save_testing_outputs, "run_generate_initial_quality_analysis"), "run_generate_initial_quality_analysis": (SDLC.generate_initial_quality_analysis, "run_generate_quality_feedback"), "run_generate_quality_feedback": (SDLC.generate_quality_feedback, "collect_quality_human_feedback"), "run_refine_quality_and_code": (SDLC.refine_quality_and_code, "collect_quality_decision"), "run_generate_initial_deployment": (lambda state: SDLC.generate_initial_deployment(state, st.session_state.current_prefs), "run_generate_deployment_feedback"), "run_generate_deployment_feedback": (SDLC.generate_deployment_feedback, "collect_deployment_human_feedback"), "run_refine_deployment": (SDLC.refine_deployment, "collect_deployment_decision"), }

# --- Main Execution Logic ---
if st.session_state.get('config_applied', False):
    current_stage = st.session_state.stage
    if current_stage.startswith("run_"):
        if current_stage in workflow_map: func, next_stage = workflow_map[current_stage]; run_workflow_step(func, next_stage)
        else: st.error(f"Unknown processing stage '{current_stage}'. Resetting."); logger.critical(f"Halted at unknown stage: {current_stage}."); initialize_state(); st.rerun()
# --- END OF app.py ---