import streamlit as st
import traceback
from fpdf import FPDF
from unidecode import unidecode
import streamlit_ext as ste


class DisplayResultStreamlit:
    def __init__(self,usecase,graph,user_message):
        self.usecase= usecase
        self.graph = graph
        self.user_requirement = user_message
        
    def display_result_on_ui(self):
        usecase= self.usecase
        workflow = self.graph
        #user_requirement = self.user_requirement
        result = {}
           
        if usecase=="SDLC":
            #user_requirement = st.text_area("Enter User Requirement:", height=200)
            initial_state = {"requirement": self.user_requirement}

            ## testing the streamlit session state
            # Initialize session state for result
            if "result" not in st.session_state:
                st.session_state["result"] = None
            if "user_input" not in st.session_state:
                st.session_state["user_input"] = ""


            # Run Workflow Button
            #if st.session_state.get("button_clicked", False): 
            if not self.user_requirement.strip():
                st.warning("Please enter a user requirement.")
            else:
                with st.spinner("Processing... Please wait"):
                    try:
                        initial_state["user_requirement"] = self.user_requirement
                        result = workflow.invoke(initial_state, {"recursion_limit": 100})

                        st.session_state["result"] = result
                        st.session_state["user_input"] = self.user_requirement

                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                        st.text(traceback.format_exc())

            # Tabs Display if result exists
            if st.session_state["result"]:
                result = st.session_state["result"]
                user_input = st.session_state["user_input"]

                tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "User Requirement","Generated User Story", "Product Owner Review", "Design Document",
                "Code", "Security Review", "Test Cases", " QA Review"
            ])

            with tab0:
                st.markdown("### User Requirement Entered as Input")
                st.markdown(user_input)
    
            with tab1:
                st.markdown("### User Story")
                st.markdown(result.get("user_story", "No review available."))

            with tab2:
                st.markdown("### Product Owner Review")
                st.markdown(result.get("product_feedback", "No review available."))

            with tab3:
                st.markdown("### Design Document")
                design_doc = result.get("design_doc", "No design document generated.")
                st.markdown(design_doc)

                # Create a formatted PDF from design doc
                #if "pdf_output" not in st.session_state:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "Design Document", ln=True, align="C")
                pdf.ln(10)
                pdf.set_font("Arial", size=12)

                for line in design_doc.split("\n"):
                    line_temp = unidecode(line)  # Convert Unicode to ASCII
                    pdf.multi_cell(0, 10, line_temp)

                pdf_output = pdf.output(dest="S").encode("latin-1")
                ste.download_button("Download Design Doc as PDF", pdf_output,"design_doc.pdf")

            with tab4:
                st.markdown("### Generated Code")
                code = result.get("code", "# No code generated.")
                st.code(code, language="python")

                ste.download_button("Download Code as .py",code, "generated_code.py")

            with tab5:
                st.markdown("### Security Review")
                st.markdown(result.get("security_feedback", "No security review available."))

            with tab6:
                st.markdown("### Test Cases")
                test_cases = result.get("test_cases", "No test cases generated.")
                st.markdown(test_cases)

            with tab7:
                st.markdown("### QA Review")
                st.markdown(result.get("qa_review", "No QA review available."))
                st.markdown(result.get("qa_feedback", "No QA review available."))
        
        