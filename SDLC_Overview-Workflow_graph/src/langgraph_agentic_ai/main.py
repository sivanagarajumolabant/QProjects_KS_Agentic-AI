import streamlit as st
from src.langgraph_agentic_ai.ui.streamlit_ui.load_ui import LoadStreamlitUI
from src.langgraph_agentic_ai.LLMs.groqllm import GroqLLM
from src.langgraph_agentic_ai.graph.graph_builder import GraphBuilder
from src.langgraph_agentic_ai.ui.streamlit_ui.display_result import DisplayResultStreamlit

# MAIN Function START
def load_langgraph_agenticai_app():
    """
    Loads and runs the LangGraph AgenticAI application with Streamlit UI.
    This function initializes the UI, handles user input, configures the LLM model,
    sets up the graph based on the selected use case, and displays the output while 
    implementing exception handling for robustness.
    """
   
    # Load UI
    ui = LoadStreamlitUI()
    user_input = ui.load_streamlit_ui()

    if not user_input:
        st.error("Error: Failed to load user input from the UI.")
        return
    
    # User Requirement Input
    user_requirement = st.chat_input("Enter User Requirement:")
    
    
        
    if user_requirement:
            try:
                # Configure LLM
                obj_llm_config = GroqLLM(user_controls_input=user_input)
                model = obj_llm_config.get_llm_model()
                
                if not model:
                    st.error("Error: LLM model could not be initialized.")
                    return

                # Initialize and set up the graph based on use case
                usecase = user_input.get('selected_usecase')
                if not usecase:
                    st.error("Error: No use case selected.")
                    return
                

                ### Graph Builder
                graph_builder=GraphBuilder(model)
                try:
                    graph = graph_builder.setup_graph(usecase)
                    DisplayResultStreamlit(usecase,graph,user_requirement).display_result_on_ui()
                except Exception as e:
                    st.error(f"Error: Graph setup failed - {e}")
                    return
                

            except Exception as e:
                 raise ValueError(f"Error Occurred with Exception : {e}")
            

        

   

    