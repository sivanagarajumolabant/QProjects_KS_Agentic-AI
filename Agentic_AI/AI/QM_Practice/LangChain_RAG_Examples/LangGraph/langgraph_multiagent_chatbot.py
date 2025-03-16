import os
from langchain_openai import ChatOpenAI
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun
from langgraph.prebuilt import ToolNode, tools_condition

## Arxiv And Wikipedia tools


arxiv_wrapper = ArxivAPIWrapper(top_k_results=1, doc_content_chars_max=300)
arxiv_tool = ArxivQueryRun(api_wrapper=arxiv_wrapper)

api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=300)
wiki_tool = WikipediaQueryRun(api_wrapper=api_wrapper)
# print(wiki_tool.invoke("who is Sharukh Khan?"))
# print(arxiv_tool.invoke("Attention is all you need"))
tools = [wiki_tool, arxiv_tool]

os.environ["OPENAI_API_KEY"] = 'sk-None-s0WHOaVSO7j098OsNYKjT3BlbkFJDA98E0grtsyw9vqGcwbh'
llm = ChatOpenAI(model="gpt-3.5-turbo")


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)
llm_with_tools = llm.bind_tools(tools=tools)


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

graph = graph_builder.compile()

from IPython.display import Image, display

try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception:
    # This requires some extra dependencies and is optional
    pass

# user_input = "Hi there!, My name is John"
#
# events = graph.stream(
#     {"messages": [("user", user_input)]}, stream_mode="values"
# )
#
# for event in events:
#     event["messages"][-1].pretty_print()
#
# user_input = "what is RLHF."
#
# # The config is the **second positional argument** to stream() or invoke()!
# events = graph.stream(
#     {"messages": [("user", user_input)]}, stream_mode="values"
# )
# for event in events:
#     event["messages"][-1].pretty_print()


user_input = "what is python?"

# The config is the **second positional argument** to stream() or invoke()!
events = graph.stream(
    {"messages": [("user", user_input)]}, stream_mode="values"
)
for event in events:
    event["messages"][-1].pretty_print()
