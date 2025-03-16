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

# Directory path containing Excel files
directory_path = "C:/Repos/QMigrator_AI/Assessment/Assessment_Documents"

# Load Excel files and extract data into LangChain documents
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

# Split documents into smaller chunks for embedding
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
documents = text_splitter.split_documents(docs)
print(f"{len(documents)} documents prepared for processing.")

# Initialize embeddings and vector store
ollama_embeddings = OllamaEmbeddings(model="llama3.2")
vector_store = FAISS.from_documents(documents, ollama_embeddings)

# Initialize LLM
llm = OllamaLLM(model="llama3.2")

# Refined prompt structure for document generation
prompt_template = ChatPromptTemplate.from_template(
    """
You are an advanced document generator skilled in creating professional PowerPoint presentations and Word documents based on data from Excel files.

**Context:**
The goal is to use multiple Excel files containing structured data to create a detailed presentation or report. The style, structure, and format should align with the design principles demonstrated in the "Unilever Assessment Summary" PowerPoint. The presentation/report should include the following sections:

1. **Title Slide:**
   - Include a title, subtitle, and branding (e.g., company name, logo).
2. **Business Objective:**
   - Summarize key objectives based on the data.
3. **Scope of Assessment:**
   - Highlight the scope using bullet points or tables (referencing specific data columns).
4. **Data Analysis:**
   - Visualize key insights and metrics from the Excel data (e.g., charts, graphs).
5. **Challenges and Assumptions:**
   - List challenges and assumptions, integrating related metadata from Excel.
6. **Recommendations and Actions:**
   - Provide recommendations or next steps, guided by the data and metadata provided.
7. **Conclusion:**
   - Summarize findings and provide a call to action.

**Instructions:**
- Use data from the provided Excel files to create slides or sections.
- Ensure charts, graphs, and tables are formatted professionally.
- Use the colors, fonts, and design elements from the "Unilever Assessment Summary" PowerPoint as a reference for style.
- For text-heavy content, include summaries and headers to improve readability.

**Output Requirements:**
- If generating a PowerPoint: Create slides that follow the above structure with professional visuals.
- If generating a Word document: Create a report with headings, tables, and charts corresponding to the above structure.
- Embed metadata (e.g., source file, column names) subtly where applicable.

Provide a detailed and professional output.

<context>
{context}
</context>
Question: {input}
"""
)

# Create document processing chain
document_chain = create_stuff_documents_chain(llm, prompt_template)
retriever = vector_store.as_retriever()
retrieval_chain = create_retrieval_chain(retriever, document_chain)

# Query for document generation
query = "Generate a PowerPoint presentation summarizing the provided Excel data."
response = retrieval_chain.invoke({"input": query})

# Display the response
print("Generated Response:")
print(response["answer"])
