import streamlit as st
import os
import time
import threading

# Import the agent workflow and initial state from your agent module.
import CompanyDBSummaryAgent as agent
from CompanyDBSummaryAgent import app as summary_agent_app, initial_state as agent_initial_state

llm_config = {}

#############################
# Sidebar: LLM Settings
#############################
st.sidebar.title("LLM Settings")

# 1. LLM Provider Dropdown
provider = st.sidebar.selectbox("Select LLM Provider", ["Groq", "OpenAI"])

# 2. Model Selection (updates based on provider)
if provider == "Groq":
    model_options = ["llama-3.3-70b-versatile", "qwen-2.5-32b", "mistral-saba-24b", "deepseek-r1-distill-llama-70b-specdec", "llama3-70b-8192"]
    api_info_link = "https://groq.com/your-api-creation-page"  # Replace with actual URL
else:
    model_options = ["OpenAI GPT-3.5", "OpenAI GPT-4", "OpenAI O1 Mini", "OpenAI GPT-4o"]
    api_info_link = "https://platform.openai.com/account/api-keys"

model_selection = st.sidebar.selectbox("Select Model", model_options)

# 3. API Key Input
api_key = st.sidebar.text_input("API Key", type="password")
st.sidebar.markdown(f"[Need an API key? Click here.]({api_info_link})")

# Set environment variables so that get_llm() (in your agent) picks them up.
if provider.lower() == "groq":
    llm_config["provider"] = "Groq"
    llm_config["api_key"] = api_key
    llm_config["model"] = model_selection
else:
    llm_config["provider"] = "OpenAI"
    llm_config["api_key"] = api_key
    llm_config["model"] = model_selection

#############################
# Global Progress & Final Summary
#############################
timeline_steps = [
    "Tool Calling LLM",
    "Store Website Text",
    "Page Extraction",
    "Loop Page Summarization",
    "Combined Summaries",
    "Recursive Summarization",
    "Final Refinement",
    "Completed"
]

progress_lock = threading.Lock()
global_progress_info = {
    "completed": [],
    "current": None,
    "upcoming": timeline_steps.copy()
}
global_final_summary = None

def update_progress(node, status):
    """
    Thread-safe progress callback called from the agent's nodes.
    """
    global global_progress_info
    with progress_lock:
        if status == "start":
            global_progress_info["current"] = node
            if node in global_progress_info["upcoming"]:
                global_progress_info["upcoming"].remove(node)
        elif status == "end":
            if node not in global_progress_info["completed"]:
                global_progress_info["completed"].append(node)
            global_progress_info["current"] = None

def render_timeline():
    """
    Build HTML for the scrollable timeline display with dark mode styling.
    The current step is highlighted.
    """
    with progress_lock:
        progress = global_progress_info.copy()
    current_color = "#FFFFFF"
    completed_color = "#AAAAAA"
    upcoming_color = "#CCCCCC"
    other_color = "#777777"
    html = "<div style='overflow-y:auto; max-height:400px; padding:10px; border:1px solid #444; background-color:#222;'>"
    for step in timeline_steps:
        if step in progress["completed"]:
            html += f"<div style='font-size:12px; color:{completed_color}; opacity:0.6; margin:2px 0;'>{step}</div>"
        elif step == progress["current"]:
            html += f"<div style='font-weight:bold; font-size:16px; color:{current_color}; text-shadow:0 0 8px #FFD700; margin:4px 0;'>{step}</div>"
        elif step in progress["upcoming"]:
            html += f"<div style='font-size:12px; color:{upcoming_color}; opacity:0.9; margin:2px 0;'>{step}</div>"
        else:
            html += f"<div style='font-size:10px; color:{other_color}; margin:2px 0;'>{step}</div>"
    html += "</div>"
    return html

# Override the agent's progress callback.
agent.progress_callback = update_progress

def run_workflow(initial_state):
    """
    Runs the workflow in a background thread.
    The final state (including 'final_summary') is stored in a global variable.
    """
    initial_state["llm_config"] = llm_config
    global global_final_summary
    final_state = summary_agent_app.invoke(
        initial_state,
        config={"configurable": {"thread_id": "streamlit-session"}},
    )
    try:
        global_final_summary = final_state.get("final_summary", "No summary produced.")
    except (KeyError, IndexError, AttributeError):
        global_final_summary = "No summary produced."
    with progress_lock:
        global_progress_info["completed"].append("Completed")
        global_progress_info["current"] = None

#############################
# Main Layout: 75% Left / 25% Right
#############################
st.markdown(
    """
    <style>
    body {background-color:#121212; color:#e0e0e0;}
    .stTextInput>div>div>input, .stTextArea>div>textarea {background-color:#333333; color:#e0e0e0;}
    </style>
    """, unsafe_allow_html=True
)
left_col, right_col = st.columns([3,1])

#############################
# Right Column: Progress Timeline
#############################
with right_col:
    st.subheader("Progress")
    timeline_placeholder = st.empty()
    timeline_placeholder.markdown(render_timeline(), unsafe_allow_html=True)

#############################
# Left Column: Final Summary & Query Input
#############################
with left_col:
    st.subheader("Final Summary")
    if "final_summary" not in st.session_state:
        st.session_state["final_summary"] = "Your final summary will appear here."
    summary_text = st.session_state["final_summary"]
    st.text_area("Final Summary (Markdown)", value=summary_text, height=200, key="final_summary_display", label_visibility="hidden")
    if st.button("Copy Final Summary"):
        copy_js = f"<script>navigator.clipboard.writeText({repr(summary_text)});</script>"
        st.markdown(copy_js, unsafe_allow_html=True)
        st.success("Copied final summary to clipboard!")
    
    st.write("### Query Input")
    query_col1, query_col2 = st.columns([4,1])
    # Provide a non-empty label and hide it
    if "user_query" not in st.session_state:
        st.session_state["user_query"] = ""
    with query_col1:
        user_query_val = st.text_input("Query", value=st.session_state["user_query"], key="query_input", label_visibility="hidden")
    with query_col2:
        generate_clicked = st.button("Generate")
    
    st.write("#### Example Queries")
    example_queries = [
        "Please fetch and summarize this URL: https://www.krishnaik.in/",
        "Summary this website here's the URL: https://www.xbyteanalytics.com",
        "Create company summary by this URL: https://yalantis.com/"
    ]
    for ex in example_queries:
        if st.button(ex, key=ex):
            st.session_state["user_query"] = ex
            st.rerun()  # Immediately update so the query text input reflects the selection

    
    # If Generate is clicked, trigger the workflow.
    if generate_clicked:
        print("DEBUG: Generate button clicked")
        local_state = agent_initial_state.copy()
        from langchain_core.messages import HumanMessage
        local_state["messages"][0] = HumanMessage(content=user_query_val)
        print("DEBUG: local_state before workflow thread start:", local_state)
        st.info("Processing... This may take a few minutes.")
        thread = threading.Thread(target=run_workflow, args=(local_state,))
        thread.start()
        # While the workflow thread is running, update the timeline.
        while thread.is_alive():
            timeline_placeholder.markdown(render_timeline(), unsafe_allow_html=True)
            time.sleep(0.5)
        timeline_placeholder.markdown(render_timeline(), unsafe_allow_html=True)
        st.session_state["final_summary"] = (
            global_final_summary if global_final_summary is not None else "No summary produced."
        )
        print("DEBUG: Workflow completed. Final summary:", st.session_state["final_summary"])
        st.rerun()  # Rerun so the Final Summary text area updates automatically
