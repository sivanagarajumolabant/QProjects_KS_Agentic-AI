import os
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.llms import Ollama
# from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
import streamlit as st




# print(response)
st.title('Langchain Demo With Ollama API')
input_text=st.text_input("Search the topic u want")
if input_text:
    # Load all Python and text files from a directory
    source_path = 'C:/projects/GEN AI/dynamo'
    target_path = 'C:/projects/GEN AI/cosmos'

    files =  [source_path, target_path]
    all_documents = []
    # Load documents
    for file in files:
        if os.path.exists(file):
            print(f"Loading files from: {file}")
            loader = DirectoryLoader(file, glob='*.py')  # Try simpler glob pattern
            documents = loader.load()
            all_documents.extend(documents)
            print(f"Loaded {len(documents)} documents from {file}")
        else:
            print(f"Directory does not exist: {file}")
    # print(all_documents)
    print(f"Total documents loaded: {len(all_documents)}")
    db=FAISS.from_documents(all_documents,OllamaEmbeddings())
    llm=Ollama(model="llama2")
    # print(llm)

    prompt = ChatPromptTemplate.from_template("""
    you are a python expert so please provide cosmos python code corresponding dynamo-python code
    don't change the variables keep same as dynamo end. 
    <context>
    {context}
    </context>
    Question: {input}""")

    document_chain=create_stuff_documents_chain(llm,prompt)
    retriever=db.as_retriever()
    retrieval_chain=create_retrieval_chain(retriever,document_chain)
    response = retrieval_chain.invoke({"input":input_text})
    st.write(response['answer'])


# """You are an expert in python. I have some Python code that interacts with Amazon DynamoDB. 
# I want to convert it to work with Azure Cosmos DB.

# Here's the DynamoDB code:

# ```python
# import boto3
# from boto3.dynamodb.conditions import Attr

# DYNAMODB_ENDPOINT_URL = "@endpointurl"

# dynamodb = boto3.resource(
#     'dynamodb',
#     endpoint_url=DYNAMODB_ENDPOINT_URL
# )


# def fetch_result(table_name, filter_conditions=None, group_by=None):
#     table = dynamodb.Table(table_name)
#     filter_expression = None
#     if filter_conditions:
#         for key, value in filter_conditions.items():
#             if filter_expression is None:
#                 filter_expression = Attr(key).eq(value)
#             else:
#                 filter_expression &= Attr(key).eq(value)

#     scan_args = {}
#     if filter_expression:
#         scan_args['FilterExpression'] = filter_expression

#     response = table.scan(**scan_args)

#     items = response.get('Items', [])

#     grouped_results = {}
#     for item in items:
#         group_key = item.get(group_by, "Unknown")
#         if group_key not in grouped_results:
#             grouped_results[group_key] = []
#         grouped_results[group_key].append(item)
#     return grouped_results

# Please convert this DynamoDB code into Cosmos DB code using Python. Keep the same variable names and logic.
# """