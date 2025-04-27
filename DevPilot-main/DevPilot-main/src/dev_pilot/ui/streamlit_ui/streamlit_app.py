import streamlit as st
from src.dev_pilot.LLMS.groqllm import GroqLLM
from src.dev_pilot.LLMS.geminillm import GeminiLLM
from src.dev_pilot.LLMS.openai_llm import OpenAILLM
from src.dev_pilot.graph.graph_builder import GraphBuilder
from src.dev_pilot.ui.uiconfigfile import Config
import src.dev_pilot.utils.constants as const
from src.dev_pilot.graph.graph_executor import GraphExecutor
from src.dev_pilot.state.sdlc_state import UserStoryList
import os

def initialize_session():
    st.session_state.stage = const.PROJECT_INITILIZATION
    st.session_state.project_name = ""
    st.session_state.requirements = ""
    st.session_state.task_id = ""
    st.session_state.state = {}


def load_sidebar_ui(config):
    user_controls = {}
    
    with st.sidebar:
        # Get options from config
        llm_options = config.get_llm_options()

        # LLM selection
        user_controls["selected_llm"] = st.selectbox("Select LLM", llm_options)

        if user_controls["selected_llm"] == 'Groq':
            # Model selection
            model_options = config.get_groq_model_options()
            user_controls["selected_groq_model"] = st.selectbox("Select Model", model_options)
            # API key input
            os.environ["GROQ_API_KEY"] = user_controls["GROQ_API_KEY"] = st.session_state["GROQ_API_KEY"] = st.text_input("API Key",
                                                                                                    type="password",
                                                                                                    value=os.getenv("GROQ_API_KEY", ""))
            # Validate API key
            if not user_controls["GROQ_API_KEY"]:
                st.warning("⚠️ Please enter your GROQ API key to proceed. Don't have? refer : https://console.groq.com/keys ")
                
        if user_controls["selected_llm"] == 'Gemini':
            # Model selection
            model_options = config.get_gemini_model_options()
            user_controls["selected_gemini_model"] = st.selectbox("Select Model", model_options)
            # API key input
            os.environ["GEMINI_API_KEY"] = user_controls["GEMINI_API_KEY"] = st.session_state["GEMINI_API_KEY"] = st.text_input("API Key",
                                                                                                    type="password",
                                                                                                    value=os.getenv("GEMINI_API_KEY", "")) 
            # Validate API key
            if not user_controls["GEMINI_API_KEY"]:
                st.warning("⚠️ Please enter your GEMINI API key to proceed. Don't have? refer : https://ai.google.dev/gemini-api/docs/api-key ")
                
                
        if user_controls["selected_llm"] == 'OpenAI':
            # Model selection
            model_options = config.get_openai_model_options()
            user_controls["selected_openai_model"] = st.selectbox("Select Model", model_options)
            # API key input
            os.environ["OPENAI_API_KEY"] = user_controls["OPENAI_API_KEY"] = st.session_state["OPENAI_API_KEY"] = st.text_input("API Key",
                                                                                                    type="password",
                                                                                                    value=os.getenv("OPENAI_API_KEY", "")) 
            # Validate API key
            if not user_controls["OPENAI_API_KEY"]:
                st.warning("⚠️ Please enter your OPENAI API key to proceed. Don't have? refer : https://platform.openai.com/api-keys ")
    
        if st.button("Reset Session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            initialize_session()
            st.rerun()
            
        st.subheader("Workflow Overview")
        st.image("workflow_graph.png")
            
    return user_controls


def load_streamlit_ui(config):
    st.set_page_config(page_title=config.get_page_title(), layout="wide")
    st.header(config.get_page_title())
    st.subheader("Let AI agents plan your SDLC journey", divider="rainbow", anchor=False)
    user_controls = load_sidebar_ui(config)
    return user_controls


## Main Entry Point    
def load_app():
    """
    Main entry point for the Streamlit app using tab-based UI.
    """
    config = Config()
    if 'stage' not in st.session_state:
        initialize_session()

    user_input = load_streamlit_ui(config)
    if not user_input:
        st.error("Error: Failed to load user input from the UI.")
        return

    try:
        # Configure LLM 
        selectedLLM = user_input.get("selected_llm")
        model = None
        if selectedLLM == "Gemini":
            obj_llm_config = GeminiLLM(user_controls_input=user_input)
            model = obj_llm_config.get_llm_model()
        elif selectedLLM == "Groq":
            obj_llm_config = GroqLLM(user_controls_input=user_input)
            model = obj_llm_config.get_llm_model()
        elif selectedLLM == "OpenAI":
            obj_llm_config = OpenAILLM(user_controls_input=user_input)
            model = obj_llm_config.get_llm_model()
        if not model:
            st.error("Error: LLM model could not be initialized.")
            return

        ## Graph Builder
        graph_builder = GraphBuilder(model)
        try:
            graph = graph_builder.setup_graph()
            graph_executor = GraphExecutor(graph)
        except Exception as e:
            st.error(f"Error: Graph setup failed - {e}")
            return

        # Create tabs for different stages
        tabs = st.tabs(["Project Requirement", "User Stories", "Design Documents", "Code Generation", "Test Cases", "QA Testing", "Deployment", "Download Artifacts"])

        # ---------------- Tab 1: Project Requirement ----------------
        with tabs[0]:
            st.header("Project Requirement")
            project_name = st.text_input("Enter the project name:", value=st.session_state.get("project_name", ""))
            st.session_state.project_name = project_name

            if st.session_state.stage == const.PROJECT_INITILIZATION:
                if st.button("🚀 Let's Start"):
                    if not project_name:
                        st.error("Please enter a project name.")
                        st.stop()
                    graph_response = graph_executor.start_workflow(project_name)
                    st.session_state.task_id = graph_response["task_id"]
                    st.session_state.state = graph_response["state"]
                    st.session_state.project_name = project_name
                    st.session_state.stage = const.REQUIREMENT_COLLECTION
                    st.rerun()

            # If stage has progressed beyond initialization, show requirements input and details.
            if st.session_state.stage in [const.REQUIREMENT_COLLECTION, const.GENERATE_USER_STORIES]:
                requirements_input = st.text_area(
                    "Enter the requirements. Write each requirement on a new line:",
                    value="\n".join(st.session_state.get("requirements", []))
                )
                if st.button("Submit Requirements"):
                    requirements = [req.strip() for req in requirements_input.split("\n") if req.strip()]
                    st.session_state.requirements = requirements
                    if not requirements:
                        st.error("Please enter at least one requirement.")
                    else:
                        st.success("Project details saved successfully!")
                        st.subheader("Project Details:")
                        st.write(f"**Project Name:** {st.session_state.project_name}")
                        st.subheader("Requirements:")
                        for req in requirements:
                            st.write(req)
                        graph_response = graph_executor.generate_stories(st.session_state.task_id, requirements)
                        st.session_state.state = graph_response["state"]
                        st.session_state.stage = const.GENERATE_USER_STORIES
                        st.rerun()

        # ---------------- Tab 2: User Stories ----------------
        with tabs[1]:
            st.header("User Stories")
            if "user_stories" in st.session_state.state:
                user_story_list = st.session_state.state["user_stories"]
                st.divider()
                st.subheader("Generated User Stories")
                if isinstance(user_story_list, UserStoryList):
                    for story in user_story_list.user_stories:
                        unique_id = f"US-{story.id:03}"
                        with st.container():
                            st.markdown(f"#### {story.title} ({unique_id})")
                            st.write(f"**Priority:** {story.priority}")
                            st.write(f"**Description:** {story.description}")
                            st.write(f"**Acceptance Criteria:**")
                            st.markdown(story.acceptance_criteria.replace("\n", "<br>"), unsafe_allow_html=True)
                            st.divider()

            # User Story Review Stage.
            if st.session_state.stage == const.GENERATE_USER_STORIES:
                st.subheader("Review User Stories")
                feedback_text = st.text_area("Provide feedback for improving the user stories (optional):")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve User Stories"):
                        st.success("✅ User stories approved.")
                        graph_response = graph_executor.graph_review_flow(
                            st.session_state.task_id, status="approved", feedback=None,  review_type=const.REVIEW_USER_STORIES
                        )
                        st.session_state.state = graph_response["state"]
                        st.session_state.stage = const.CREATE_DESIGN_DOC
                        
                        ## For Testing
                        # st.session_state.stage = const.CODE_GENERATION
                        
                        
                with col2:
                    if st.button("✍️ Give User Stories Feedback"):
                        if not feedback_text.strip():
                            st.warning("⚠️ Please enter feedback before submitting.")
                        else:
                            st.info("🔄 Sending feedback to revise user stories.")
                            graph_response = graph_executor.graph_review_flow(
                                st.session_state.task_id, status="feedback", feedback=feedback_text.strip(),review_type=const.REVIEW_USER_STORIES
                            )
                            st.session_state.state = graph_response["state"]
                            st.session_state.stage = const.GENERATE_USER_STORIES
                            st.rerun()
            else:
                st.info("User stories generation pending or not reached yet.")

        # ---------------- Tab 3: Design Documents ----------------
        with tabs[2]:
            st.header("Design Documents")
            if st.session_state.stage == const.CREATE_DESIGN_DOC:
                
                graph_response = graph_executor.get_updated_state(st.session_state.task_id)
                st.session_state.state = graph_response["state"]
                
                if "design_documents" in st.session_state.state:
                    design_doc = st.session_state.state["design_documents"]        
                    st.subheader("Functional Design Document")
                    st.markdown(design_doc.get("functional", "No functional design document available."))
                    st.subheader("Technical Design Document")
                    st.markdown(design_doc.get("technical", "No technical design document available."))
                
                # Design Document Review Stage.
                st.divider()
                st.subheader("Review Design Documents")
                feedback_text = st.text_area("Provide feedback for improving the design documents (optional):")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve Design Documents"):
                        st.success("✅ Design documents approved.")
                        graph_response = graph_executor.graph_review_flow(
                            st.session_state.task_id, status="approved", feedback=None,  review_type=const.REVIEW_DESIGN_DOCUMENTS
                        )
                        st.session_state.state = graph_response["state"]
                        st.session_state.stage = const.CODE_GENERATION
                        
                with col2:
                    if st.button("✍️ Give Design Documents Feedback"):
                        if not feedback_text.strip():
                            st.warning("⚠️ Please enter feedback before submitting.")
                        else:
                            st.info("🔄 Sending feedback to revise design documents.")
                            graph_response = graph_executor.graph_review_flow(
                                st.session_state.task_id, status="feedback", feedback=feedback_text.strip(),review_type=const.REVIEW_DESIGN_DOCUMENTS
                            )
                            st.session_state.state = graph_response["state"]
                            st.session_state.stage = const.CREATE_DESIGN_DOC
                            st.rerun()
                    
            else:
                st.info("Design document generation pending or not reached yet.")

        # ---------------- Tab 4: Coding ----------------
        with tabs[3]:
            st.header("Code Genearation")
            if st.session_state.stage in [const.CODE_GENERATION, const.SECURITY_REVIEW]:
                
                graph_response = graph_executor.get_updated_state(st.session_state.task_id)
                st.session_state.state = graph_response["state"]
                        
                if "code_generated" in st.session_state.state:
                    code_generated = st.session_state.state["code_generated"]        
                    st.subheader("Code Files")
                    st.markdown(code_generated)
                    st.divider()
                    
                if st.session_state.stage == const.CODE_GENERATION:  
                        review_type = const.REVIEW_CODE
                elif st.session_state.stage == const.SECURITY_REVIEW:
                      if "security_recommendations" in st.session_state.state:
                        security_recommendations = st.session_state.state["security_recommendations"]        
                        st.subheader("Security Recommendations")
                        st.markdown(security_recommendations)
                        review_type = const.REVIEW_SECURITY_RECOMMENDATIONS
                
                # Code Review Stage.
                st.divider()
                st.subheader("Review Details")
                
                if st.session_state.stage == const.CODE_GENERATION:
                    feedback_text = st.text_area("Provide feedback (optional):")
                    
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve Code"):
                        graph_response = graph_executor.graph_review_flow(
                            st.session_state.task_id, status="approved", feedback=None, review_type=review_type
                        )
                        st.session_state.state = graph_response["state"]
                        if st.session_state.stage == const.CODE_GENERATION:
                            st.session_state.stage = const.SECURITY_REVIEW
                            st.rerun()
                        elif st.session_state.stage == const.SECURITY_REVIEW:
                            st.session_state.stage = const.WRITE_TEST_CASES
                            
                with col2:
                    if st.session_state.stage == const.SECURITY_REVIEW:
                        if st.button("✍️ Implment Security Recommendations"):
                            st.info("🔄 Sending feedback to revise code generation.")
                            graph_response = graph_executor.graph_review_flow(
                                st.session_state.task_id, status="feedback", feedback=None, review_type=review_type
                            )
                            st.session_state.state = graph_response["state"]
                            st.session_state.stage = const.CODE_GENERATION
                            st.rerun()
                    else:
                        if st.button("✍️ Give Feedback"):
                            if not feedback_text.strip():
                                st.warning("⚠️ Please enter feedback before submitting.")
                            else:
                                st.info("🔄 Sending feedback to revise code generation.")
                                graph_response = graph_executor.graph_review_flow(
                                    st.session_state.task_id, status="feedback", feedback=feedback_text.strip(),review_type=review_type
                                )
                                st.session_state.state = graph_response["state"]
                                st.session_state.stage = const.CODE_GENERATION
                                st.rerun()
                    
            else:
                st.info("Code generation pending or not reached yet.")
                
        # ---------------- Tab 5: Test Cases ----------------
        with tabs[4]:
            st.header("Test Cases")
            if st.session_state.stage == const.WRITE_TEST_CASES:
                
                graph_response = graph_executor.get_updated_state(st.session_state.task_id)
                st.session_state.state = graph_response["state"]
                
                if "test_cases" in st.session_state.state:
                    test_cases = st.session_state.state["test_cases"]        
                    st.markdown(test_cases)
                
                # Test Cases Review Stage.
                st.divider()
                st.subheader("Review Test Cases")
                feedback_text = st.text_area("Provide feedback for improving the test cases (optional):")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Approve Test Cases"):
                        st.success("✅ Test cases approved.")
                        graph_response = graph_executor.graph_review_flow(
                            st.session_state.task_id, status="approved", feedback=None,  review_type=const.REVIEW_TEST_CASES
                        )
                        st.session_state.state = graph_response["state"]
                        st.session_state.stage = const.QA_TESTING
                        
                with col2:
                    if st.button("✍️ Give Test Cases Feedback"):
                        if not feedback_text.strip():
                            st.warning("⚠️ Please enter feedback before submitting.")
                        else:
                            st.info("🔄 Sending feedback to revise test cases.")
                            graph_response = graph_executor.graph_review_flow(
                                st.session_state.task_id, status="feedback", feedback=feedback_text.strip(),review_type=const.REVIEW_TEST_CASES
                            )
                            st.session_state.state = graph_response["state"]
                            st.session_state.stage = const.WRITE_TEST_CASES
                            st.rerun()
                    
            else:
                st.info("Test Cases generation pending or not reached yet.")
                
        # ---------------- Tab 6: QA Testing ----------------
        with tabs[5]:
            st.header("QA Testing")
            if st.session_state.stage == const.QA_TESTING:
                
                graph_response = graph_executor.get_updated_state(st.session_state.task_id)
                st.session_state.state = graph_response["state"]
                
                if "qa_testing_comments" in st.session_state.state:
                    qa_testing = st.session_state.state["qa_testing_comments"]        
                    st.markdown(qa_testing)
                
                # QA Testing Review Stage.
                st.divider()
                st.subheader("Review QA Testing Comments")
                col1, col2 = st.columns(2)
                with col1:
                    if  st.button("✅ Approve Testing"):
                        st.success("✅ QA Testing approved.")
                        graph_response = graph_executor.graph_review_flow(
                            st.session_state.task_id, status="approved", feedback=None,  review_type=const.REVIEW_QA_TESTING
                        )
                        st.session_state.state = graph_response["state"]
                        st.session_state.stage = const.DEPLOYMENT
                        
                with col2:
                    if  st.button("✍️ Fix testing issues"):
                        st.info("🔄 Sending feedback to revise code.")
                        graph_response = graph_executor.graph_review_flow(
                            st.session_state.task_id, status="feedback", feedback=feedback_text.strip(),review_type=const.REVIEW_QA_TESTING
                        )
                        st.session_state.state = graph_response["state"]
                        st.session_state.stage = const.CODE_GENERATION
                        st.rerun()
                    
            else:
                st.info("QA Testing Report generation pending or not reached yet.")
                
        # ---------------- Tab 7: Deployment ----------------
        with tabs[6]:
            st.header("Deployment")
            if st.session_state.stage == const.DEPLOYMENT:
                
                graph_response = graph_executor.get_updated_state(st.session_state.task_id)
                st.session_state.state = graph_response["state"]
                
                if "deployment_feedback" in st.session_state.state:
                    deployment_feedback = st.session_state.state["deployment_feedback"]        
                    st.markdown(deployment_feedback)
                    st.session_state.stage = const.ARTIFACTS
                                
            else:
                st.info("Deplopment verification pending or not reached yet.")
                
        # ---------------- Tab 8: Artifacts ----------------
        with tabs[7]:
            st.header("Artifacts")
            if "artifacts" in st.session_state.state and st.session_state.state["artifacts"]:
                st.subheader("Download Artifacts")
                for artifact_name, artifact_path in st.session_state.state["artifacts"].items():
                    if artifact_path:
                        try:
                            with open(artifact_path, "rb") as f:
                                file_bytes = f.read()
                            st.download_button(
                                label=f"Download {artifact_name}",
                                data=file_bytes,
                                file_name=os.path.basename(artifact_path),
                                mime="application/octet-stream"
                            )
                        except Exception as e:
                            st.error(f"Error reading {artifact_name}: {e}")
                    else:
                        st.info(f"{artifact_name} not available.")
            else:
                st.info("No artifacts generated yet.")

    except Exception as e:
        raise ValueError(f"Error occured with Exception : {e}")
    