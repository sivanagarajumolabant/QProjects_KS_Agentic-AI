import os
from langchain_openai import ChatOpenAI
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

os.environ["OPENAI_API_KEY"] = 'sk-None-s0WHOaVSO7j098OsNYKjT3BlbkFJDA98E0grtsyw9vqGcwbh'
llm = ChatOpenAI(model="gpt-3.5-turbo")


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


def chatbot(state: State):
    return {"messages": llm.invoke(state['messages'])}


graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, 'chatbot')
graph_builder.add_edge('chatbot', END)

graph = graph_builder.compile()

from IPython.display import Image, display

try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception:
    pass

while True:
    user_input = input("User: ")
    if user_input.lower() in ["quit", "q"]:
        print("Good Bye")
        break
    for event in graph.stream({'messages': ("user", user_input)}):
        print(event.values(), '==========')
        for value in event.values():
            print("=", value['messages'])
            print("Assistant:", value["messages"].content)
