from pprint import pprint
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, AnyMessage
import os
from typing_extensions import TypedDict
from typing import Annotated, Dict, List, Literal
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from Scrapper import scrape_and_process


# ------------------------
# Global progress callback.
# It can be overridden by the UI (app.py) to update a shared progress state.
progress_callback = lambda node, status: None

# ========================
# Define the State Class
# ========================
# Define a proper LLM configuration dictionary with the required keys.

class LLMConfig(TypedDict):
    provider: str
    model: str
    api_key: str

class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    domain_folder: str
    SCRAPED_WEBSITE_TEXT: str
    current_page_index: int
    total_pages: int
    pages: List[HumanMessage]
    page_summaries: List[str]
    combined_summary: str
    final_summary: str
    llm_config: LLMConfig

# ========================
# Helper: Append Report in Domain Folder
# ========================
# def append_report_in_domain_folder(domain_folder: str, report: str, filename: str):
    # """
    # Writes the 'report' text to a file named 'filename.txt' in the domain_folder.
    # """
    # filepath = os.path.join(domain_folder, f"{filename}.txt")
    # with open(filepath, "w", encoding="utf-8") as f:
    #     f.write(report + "\n\n")
    # print(f"--------------[DEBUG] Report saved to {filepath}--------------")


# === LLM Helper ===
def get_llm(state: State):
    import os
    # Get provider and default to "Groq" if empty
    config =state.get("llm_config")
    provider = config.get("provider", "Groq").strip().lower()
    if not provider:
        provider = "groq"
    # Get model selection, default to a value if not set
    model_selection = config.get("model", "llama3-70b-8192").strip()
    temperature = 0.5

    # Define model mapping dictionaries (keys should be lowercase for mapping)
    groq_model_map = {
        "llama-3.3-70b-versatile": "llama-3.3-70b-versatile",
        "mistral-saba-24b": "mistral-saba-24b",
        "qwen-2.5-32b": "qwen-2.5-32b",
        "deepseek-r1-distill-llama-70b-specdec": "deepseek-r1-distill-llama-70b-specdec",
        "llama3-70b-8192": "llama3-70b-8192",  # Update with actual model names as needed
    }
    openai_model_map = {
        "openai gpt-3.5": "gpt-3.5-turbo",
        "openai gpt-4": "gpt-4",
        "o1-mini" : "o1-mini",
        "gpt-4o": "gpt-4o",
    }

    if provider == "groq":
        from langchain_groq import ChatGroq
        api_key = config.get("api_key", "")
        mapped_model = groq_model_map.get(model_selection.lower(), "llama-3.3-70b-versatile")
        return ChatGroq(model=mapped_model, temperature=temperature, api_key=api_key)
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        api_key = config.get("api_key", "")
        mapped_model = openai_model_map.get(model_selection.lower(), "gpt-3.5-turbo")
        return ChatOpenAI(model_name=mapped_model, temperature=temperature, openai_api_key=api_key)
    else:
        raise ValueError(f"Unsupported provider: {provider}")



# ========================
# 1) Define the "fetch_page_content" tool
# ========================
def fetch_page_content(url: str) -> str:
    """
    Fetch raw text content from a webpage using Scrapper.py.
    """
    print(f"--------------[DEBUG] Fetching content from {url}--------------")
    text = scrape_and_process(url)
    return text

# ========================
# 2) Initialize LLM with Tools
# ========================


# ========================
# 3) Node: Tool Calling LLM
# ========================
def tool_calling_llm(state: State):
    progress_callback("Tool Calling LLM", "start")
    print("--------------[DEBUG] Tool calling LLM--------------")
    llm_base = get_llm(state)
    llm_with_tools = llm_base.bind_tools([fetch_page_content])
    updated_messages = [llm_with_tools.invoke(state["messages"])]
    state.update({"messages": updated_messages})
    return state

# ========================
# 4) Dynamically create a folder based on the domain name from the URL
# ========================
def make_folder_for_url(url: str) -> str:
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc
    if not domain:
        domain = "unknown_domain"
    os.makedirs(domain, exist_ok=True)
    print(f"--------------[DEBUG] Created folder for domain: {domain}--------------")
    return domain

# ========================
# 5) Node: Store Website Text
# ========================
def store_website_text_node(state: State) -> State:
    progress_callback("Tool Calling LLM", "end")
    progress_callback("Store Website Text", "start")
    messages = state["messages"]
    last_msg = messages[-1]
    
    if "ToolMessage" in last_msg.__class__.__name__ and getattr(last_msg, "name", "") == "fetch_page_content":
        print("--------------[DEBUG] Detected a ToolMessage from fetch_page_content --------------")
        tool_text = last_msg.content
        domain_folder = "unknown_domain"
        if len(messages) >= 2 and isinstance(messages[-2], AIMessage) and hasattr(messages[-2], "tool_calls"):
            prev_msg = messages[-2]
            for call in prev_msg.tool_calls:
                if call.get("name", "") == "fetch_page_content":
                    url_called = call.get("args", {}).get("url", "")
                    domain_folder = make_folder_for_url(url_called)
                    break
        else:
            os.makedirs(domain_folder, exist_ok=True)
        state.update({
            "domain_folder": domain_folder,
            "SCRAPED_WEBSITE_TEXT": tool_text
        })
    else:
        print("--------------[DEBUG] No valid ToolMessage detected; using last message content --------------")
        state.update({
            "domain_folder": "unknown_domain",
            "SCRAPED_WEBSITE_TEXT": last_msg.content
        })
    return state

# ========================
# 6) Node: Page Extraction
# ========================
def page_extraction_node(state: State) -> Dict:
    progress_callback("Store Website Text", "end")
    progress_callback("Page Extraction", "start")
    print("--------------[DEBUG] Page Extraction Node--------------")
    website_text = state.get("SCRAPED_WEBSITE_TEXT", "")
    if not website_text.strip():
        print("[DEBUG] No website text found.")
        progress_callback("Page Extraction", "end")
        return state
    PAGE_DELIMITER = "---PAGE DELIMITER---"
    pages = [page.strip() for page in website_text.split(PAGE_DELIMITER) if page.strip()]
    page_messages = [HumanMessage(content=f"[Page {i+1}]\n{page}") for i, page in enumerate(pages)]
    state.update({
        "pages": page_messages,
        "total_pages": len(page_messages),
        "current_page_index": 0,
        "page_summaries": []
    })

    return state


def custom_recursive_summarize(text: str, max_chunk_size: int, overlap_size: int, target_length: int, llm) -> str:
    """
    Recursively summarizes text that is longer than target_length.
    
    For the first chunk, a summary is generated normally.
    For subsequent chunks, the previous summary and the new chunk are combined to produce an updated summary.
    This process repeats until the final summary is under the target_length.
    """
    # If text is already short enough, return it.
    if len(text) <= target_length:
        return text

    # Split the text into chunks with overlap.
    chunks = split_text(text, max_chunk_size, overlap_size)
    summary = ""
    
    for i, chunk in enumerate(chunks):
        if i == 0:
            # First chunk: generate an initial summary.
            system_msg = SystemMessage(
                content="You are an experienced research analyst. Summarize the following text comprehensively for a company database. Preserve every critical detail."
            )
            human_msg = HumanMessage(
                content=f"Text:\n\n{chunk}\n\nProvide a detailed summary."
            )
            response = llm.invoke([system_msg, human_msg])
            summary = response.content.strip()
        else:
            # For subsequent chunks, update the existing summary with the new additional text.
            system_msg = SystemMessage(
                content="You are an experienced research analyst. Update the existing summary by integrating additional information without losing any critical details."
            )
            human_msg = HumanMessage(
                content=f"Existing Summary:\n\n{summary}\n\nAdditional Text:\n\n{chunk}\n\nProduce an updated comprehensive summary."
            )
            response = llm.invoke([system_msg, human_msg])
            summary = response.content.strip()

    # If the resulting summary is still too long, recursively summarize it.
    if len(summary) > target_length:
        return custom_recursive_summarize(summary, max_chunk_size, overlap_size, target_length, llm)
    return summary


# ========================
# 7) Node: Loop Page Summarization
# ========================
def loop_page_summarization_node(state: State) -> Dict:
    print("--------------[DEBUG] Loop Page Summarization Node--------------")
    idx = state.get("current_page_index", 0)
    total = state.get("total_pages", 0)
    if idx < total:
        print(f"--------------[DEBUG] Summarizing page {idx+1} of {total}...--------------")
        page = state["pages"][idx].content
        llm = get_llm(state)
        # Define a threshold; if the page exceeds this, apply multi-iteration summarization.
        page_threshold = 5000  
        target_summary_length = 3000

        if len(page) > page_threshold:
            print("--------------[DEBUG] Page length exceeds threshold; applying custom recursive summarization for this page --------------")
            page_summary = custom_recursive_summarize(page, max_chunk_size=5500, overlap_size=500, 
                                                      target_length=target_summary_length, llm=llm)
        else:
            system_msg = SystemMessage(
                content=(
                    "Prompt Title: Comprehensive Website Summary for Company Database\n\n"
                    "Context: You are provided with a webpage extracted from a company's website. Your task is to extract all key details "
                    "needed to build a company knowledge database. Focus on identifying the company's field of work, expertise, current operations, "
                    "future goals, client reviews, capabilities, limitations, constraints, and legal or compliance information.\n\n"
                    "Your summary should be structured with the following sections:\n"
                    "[Company Field of Work]\n"
                    "[Expertise Provided]\n"
                    "[Current Scope and Future Goals]\n"
                    "[Company Reviews and Clientele]\n"
                    "[Capabilities, Limitations, and Constraints]\n"
                    "[Compliance, Legal Guidelines, and Guidance]\n\n"
                    "Capture every critical detail for the company database."
                )
            )
            human_msg = HumanMessage(
                content=(
                    "Please analyze the webpage content below and produce a detailed summary including all relevant information. "
                    "Do not omit any details that may be important for the company database."
                )
            )
            context_msg = HumanMessage(
                content="Context: This summary is part of a broader company database building process."
            )
            doc_msg = HumanMessage(
                content=f"### Webpage Content\n\n{page}"
            )
            response = llm.invoke([system_msg, human_msg, context_msg, doc_msg])
            page_summary = f"-----[Page {idx+1} Summary]-----\n\n{response.content}"
        state["page_summaries"].append(page_summary)
        state["current_page_index"] = idx + 1
        print(f"--------------[DEBUG] Summary for page {idx+1} (first 100 chars): {page_summary[:100]}...")
    return state

def check_all_pages(state: State) -> Literal["loop", "initial"]:
    idx = state.get("current_page_index", 0)
    total = state.get("total_pages", 0)
    return "loop" if idx < total else "initial"

# ========================
# 8) Node: Combined Summaries
# ========================
def combined_summaries_node(state: State) -> Dict:
    progress_callback("Loop Page Summarization", "end")
    progress_callback("Combined Summaries", "start")
    domain_folder = state.get("domain_folder", "unknown_domain")
    combined = "\n\n".join(state.get("page_summaries", []))
    state["combined_summary"] = combined
    # append_report_in_domain_folder(domain_folder, combined, "Combined_Page_Summaries")
    print("--------------[DEBUG] Combined page summaries created.--------------")
    
    return state

# ========================
# 9) Node: Recursive Summarization
# ========================
def split_text(text: str, max_chunk_size: int, overlap_size: int) -> List[str]:
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + max_chunk_size, text_len)
        chunks.append(text[start:end])
        if end == text_len:
            break
        start = end - overlap_size
    return chunks

def recursive_summarize(text: str, max_chunk_size: int, overlap_size: int, target_length: int, llm) -> str:
    print("--------------[DEBUG] Recursive summarization in progress...--------------")
    if len(text) <= target_length:
        return text
    chunks = split_text(text, max_chunk_size, overlap_size)
    summaries = []

    for i, chunk in enumerate(chunks):
        system_msg = SystemMessage(
            content=(
                "You are a research analyst tasked with summarizing a portion of a company's website content for a company database. "
                "Your role is to extract every detail including company field of work, expertise, capabilities, constraints, reviews, and goals. "
                "IMPORTANT: Do not remove any information; only add clarifications or reformat ambiguous sections."
            )
        )
        human_msg = HumanMessage(
            content=(
                f"Summarize the following chunk (part {i+1}) in a detailed and structured manner. "
                "Ensure that all details are retained, and only ambiguous or conflicting parts are clarified. "
                "Aim for a summary length of around 3000 characters if possible."
            )
        )
        context_msg = HumanMessage(
            content="Context: This is part of a larger document that will be recursively summarized to build a comprehensive company database."
        )
        doc_msg = HumanMessage(
            content=f"### Chunk {i+1}\n\n{chunk}"
        )
        response = llm.invoke([system_msg, human_msg, context_msg, doc_msg])
        summaries.append(response.content.strip())
        print(f"--------------[DEBUG] Chunk {i+1} summarized.--------------")

    merged = "\n\n".join(summaries)
    return recursive_summarize(merged, max_chunk_size, overlap_size, target_length, llm)

def recursive_summarization_node(state: State) -> Dict:
    progress_callback("Combined Summaries", "end")
    progress_callback("Recursive Summarization", "start")
    domain_folder = state.get("domain_folder", "unknown_domain")
    combined_text = state.get("combined_summary", "")
    local_llm = get_llm(state)
    max_chunk_size = 5500
    overlap_size = 500
    target_summary_length = 6000
    final_summary = recursive_summarize(combined_text, max_chunk_size, overlap_size, target_summary_length, local_llm)
    state["final_summary"] = final_summary
    # append_report_in_domain_folder(domain_folder, final_summary, "Final_Recursive_Summary")
    print("--------------[DEBUG] Recursive summarization completed.--------------")
    progress_callback("Recursive Summarization", "end")
    return state

# ========================
# 10) Node: Final Refinement
# ========================
def final_refinement_node(state: State) -> Dict:
    progress_callback("Final Refinement", "start")
    domain_folder = state.get("domain_folder", "unknown_domain")
    text_for_refine = state.get("final_summary", "")
    local_llm = get_llm(state)
    context_combined = (
        f"### Final Recursive Summary (Current Version)\n\n{text_for_refine}\n\n"
        "Instruction: Refine the final summary to improve clarity, organization, and coherence. "
        "Do not remove any critical details—only add clarifications or reorganize content where necessary."
    )
    system_msg = SystemMessage(
        content=(
            "You are a refinement agent tasked with producing a polished final summary for the company database. "
            "Your goal is to enhance the clarity, structure, and overall presentation of the summary while preserving all essential information. "
            "The final document should be formatted with clear headers for each section as specified."
        )
    )
    human_msg = HumanMessage(
        content=(
            "Please refine the final summary provided below to produce a clear and well-organized company database document. "
            "Ensure that the final summary includes the following sections with detailed information: "
            "[Company Field of Work], [Expertise Provided], [Current Scope and Future Goals], [Company Reviews and Clientele], "
            "[Capabilities, Limitations, and Constraints], and [Compliance, Legal Guidelines, and Guidance]."
        )
    )
    context_human = HumanMessage(
        content="Context: Use the final recursive summary as your basis. Your refined version must not omit any details but may add clarifications and reformat as needed."
    )
    doc_msg = HumanMessage(
        content=context_combined
    )
    refined_resp = local_llm.invoke([system_msg, human_msg, context_human, doc_msg])
    refined_text = refined_resp.content
    state["final_summary"] = refined_text
    # append_report_in_domain_folder(domain_folder, refined_text, "Refined_Final_Summary")
    print("--------------[DEBUG] Final refinement completed.--------------")
    progress_callback("Final Refinement", "end")
    return state

# ========================
# 11) Build the Workflow
# ========================
workflow = StateGraph(State)

workflow.add_node("tool_calling_llm", tool_calling_llm)
workflow.add_node("tools", ToolNode([fetch_page_content]))
workflow.add_node("store_website_text_node", store_website_text_node)
workflow.add_node("PageExtractionNode", page_extraction_node)
workflow.add_node("LoopPageSummarizationNode", loop_page_summarization_node)
workflow.add_node("CombinedSummariesNode", combined_summaries_node)
workflow.add_node("RecursiveSummarizationNode", recursive_summarization_node)
workflow.add_node("FinalRefinementNode", final_refinement_node)

# -------------------------
# Edges:
workflow.add_edge(START, "tool_calling_llm")
workflow.add_conditional_edges("tool_calling_llm", tools_condition)
workflow.add_edge("tools", "store_website_text_node")
workflow.add_edge("store_website_text_node", "PageExtractionNode")
workflow.add_edge("PageExtractionNode", "LoopPageSummarizationNode")
workflow.add_conditional_edges("LoopPageSummarizationNode", check_all_pages, {
    "loop": "LoopPageSummarizationNode",
    "initial": "CombinedSummariesNode"
})
workflow.add_edge("CombinedSummariesNode", "RecursiveSummarizationNode")
workflow.add_edge("RecursiveSummarizationNode", "FinalRefinementNode")
workflow.add_edge("FinalRefinementNode", END)

# ========================
# Optional: Memory Saver
# ========================
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()

# ========================
# Compile the Workflow
# ========================
app = workflow.compile(checkpointer=checkpointer)

# Set initial query message to empty.
# Only run the workflow automatically if this file is executed directly.

initial_state = {
    "messages": [{"role": "user", "content": ""}],
    "domain_folder": "",
    "SCRAPED_WEBSITE_TEXT": "",
    "current_page_index": 0,
    "total_pages": 0,
    "pages": [],
    "page_summaries": [],
    "combined_summary": "",
    "final_summary": "",
     "llm_config": {
        "provider": "groq",              # or "openai"
        "model": "llama3-70b-8192",        # default model selection
        "api_key": ""                    # fill in as needed
    }
}

if __name__ == '__main__':
    final_state = app.invoke(
        initial_state,
        config={"configurable": {"thread_id": "my-session-001"}}
    )
    print(final_state["final_summary"])


