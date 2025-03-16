import os
import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

os.environ["OPENAI_API_KEY"] = 'sk-None-s0WHOaVSO7j098OsNYKjT3BlbkFJDA98E0grtsyw9vqGcwbh'


st.title('LlamaIndex Demo with OpenAI API')
input_text = st.text_input("Search the topic you want")

documents = SimpleDirectoryReader('../QE_RAG/data').load_data()
index = VectorStoreIndex(documents)
query_engine = index.as_query_engine()

if input_text:
    results = query_engine.query(input_text)
    st.write("Index Results:")
    if isinstance(results, list):
        for result in results:
            st.write(result.response)
    else:
        st.write(results.response)
