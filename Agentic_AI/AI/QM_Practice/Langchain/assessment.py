import os
import glob
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS


directory_path = "C:/Repos/QMigrator_AI/Assessment/Assessment_Documents"

excel_files = glob.glob(os.path.join(directory_path, "**", "*.xlsx"), recursive=True)
docs = []
for excel_file in excel_files:
    print(f"Loading Excel file: {excel_file}")
    try:
        df = pd.read_excel(excel_file, engine="openpyxl")
        for column in df.columns:
            text_data = df[column].dropna().astype(str).tolist()
            for text in text_data:
                doc = Document(
                    page_content=text, metadata={"source": excel_file, "column": column}
                )
                docs.append(doc)
        print(f"Loaded {len(docs)} documents from {excel_file}")
    except Exception as e:
        print(f"Error loading {excel_file}: {e}")

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
documents = text_splitter.split_documents(docs)
print(len(documents), " Length of Documents")
ollama_embeddings = OllamaEmbeddings(model="llama3.2")
vector_store = FAISS.from_documents(documents, ollama_embeddings)

llm = OllamaLLM(model="llama3.2")
prompt = ChatPromptTemplate.from_template(
    """
You are an expert sales analyst. 

<context>
{context}
</context>
Question: {input}"""
)

document_chain = create_stuff_documents_chain(llm, prompt)
retriever = vector_store.as_retriever()
retrieval_chain = create_retrieval_chain(retriever, document_chain)
query = "what is the Total Hours using Tool?"
response = retrieval_chain.invoke({"input": query})
print(response["answer"])
