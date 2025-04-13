import streamlit as st
from src.langgraph_agentic_ai.ui.uiconfigfile import Config
from PIL import Image


class LoadStreamlitUI:
    def __init__(self):
        self.config =  Config() # config
        self.user_controls = {}

    def initialize_session(self):
        return {
        "current_step": "requirements",
        "requirements": "",
        "user_stories": "",
        "po_feedback": "",
        "generated_code": "",
        "review_feedback": "",
        "decision": None
    }
  


    def load_streamlit_ui(self):
        st.set_page_config(page_title= self.config.get_page_title(), layout="wide")
        st.header(self.config.get_page_title())
        st.session_state.timeframe = ''
        st.session_state.IsFetchButtonClicked = False
        st.session_state.IsSDLC = False
        
        # Streamlit UI Title
        # Custom CSS for better spacing and visibility
        st.markdown(
            """
            <style>
                .main-container {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 2rem;
                    padding: 40px;
                }
                .text-box {
                    flex: 1;
                    padding: 20px;
                }
                .image-box img {
                    max-width: 100%;
                    height: auto;
                    border-radius: 10px;
                    box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
                }
                .centered-text {
                    text-align: center;
                    font-size: 18px;
                }
            </style>
            """,
            unsafe_allow_html=True
        )

        #st.title(self.config.get_page_title())

        # Load Image
        image_path = "src/langgraph_agentic_ai/ui/streamlit_ui/workflow_diagram.png"
        try:
            image = Image.open(image_path)
        except FileNotFoundError:
            st.error(f"Image not found at {image_path}. Please check the file path.")
            image = None

        # Container for flexible layout
        with st.container():
            col1, col2 = st.columns([1, 1.5])  # Adjust ratio

            with col1:
                st.markdown("### **SDLC Overview**")
                st.markdown("""
                    This AI-powered workflow automates the Software Development Life Cycle (SDLC) by guiding a requirement through various phases:

    1. **User Requirement** - Capturing the initial user requirement.
    2. **Generating User Stories** - Creating detailed user stories based on the user requirement.
    3. **Product Owner Review** - Validating and refining the requirement.
    4. **Design Document** – Developing a structured blueprint for implementation, with an option to **download it as a PDF**.
    5. **Code Generation** - Generating code based on the design, with an option to **download it as a .py file**.
    6. **Code Review** - Reviewing the generated code for quality and best practices.
    7. **Security Review** - Checking for vulnerabilities.
    8. **Test Cases** - Generating test cases to ensure functionality.
    9. **QA Review** - Verifying the final product before deployment.  

    Each step ensures the software meets quality, security, and functional requirements efficiently.
               """ )
            
            with col2:
                st.markdown("### **Workflow Diagram**")
                if image:
                    st.image(image, caption="Workflow Diagram", use_container_width=True)

        
        
        with st.sidebar:
            # Get options from config
            llm_options = self.config.get_llm_options()
            usecase_options = self.config.get_usecase_options()

            # LLM selection
            self.user_controls["selected_llm"] = st.selectbox("Select LLM", llm_options)

            if self.user_controls["selected_llm"] == 'Groq':
                # Model selection
                model_options = self.config.get_groq_model_options()
                self.user_controls["selected_groq_model"] = st.selectbox("Select Model", model_options)
                # API key input
                self.user_controls["GROQ_API_KEY"] = st.session_state["GROQ_API_KEY"] = st.text_input("API Key",
                                                                                                      type="password")
                # Validate API key
                if not self.user_controls["GROQ_API_KEY"]:
                    st.warning("Please enter your GROQ API key to proceed. Don't have? refer : https://console.groq.com/keys ")
                   
            
            # Use case selection
            self.user_controls["selected_usecase"] = st.selectbox("Select Usecases", usecase_options)

            
            if "state" not in st.session_state:
                st.session_state.state = self.initialize_session()
            
            st.sidebar.markdown(
    """
    <hr style="margin-top:20px; margin-bottom:5px; border:0.5px solid gray;">
    <p style="text-align:center; font-size:12px; color:gray;">
        © Darshita Jain 2025
    </p>
    """,
    unsafe_allow_html=True
)
        
        return self.user_controls
    
     