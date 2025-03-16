# https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag_local/#components

from langchain_ollama import ChatOllama
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.document_loaders import WebBaseLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import SKLearnVectorStore
from langchain_nomic.embeddings import NomicEmbeddings

import json
from langchain_core.messages import HumanMessage, SystemMessage

urls = [
    'https://www.javatpoint.com/python-magic-method'
    # "https://lilianweng.github.io/posts/2023-06-23-agent/",
    # "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
    # "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
]

loader = PyPDFLoader("Siva-pdf504504.pdf")
docs = loader.load()

# Load documents
# docs = [WebBaseLoader(url).load() for url in urls]
# docs_list = [item for sublist in docs for item in sublist]

# Split documents
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=1000, chunk_overlap=200
)
doc_splits = text_splitter.split_documents(docs)

# Add to vectorDB
vectorstore = SKLearnVectorStore.from_documents(
    documents=doc_splits,
    embedding=NomicEmbeddings(model="nomic-embed-text-v1.5", inference_mode="local")
)

# Create retriever
retriever = vectorstore.as_retriever(k=3)

local_llm = "llama3.2:3b-instruct-fp16"
llm = ChatOllama(model=local_llm, temperature=0)
llm_json_mode = ChatOllama(model=local_llm, temperature=0, format="json")

### Router

# Prompt
# router_instructions = """You are an expert at routing a user question to a vectorstore or web search.
#
# The vectorstore contains documents related to agents, prompt engineering, and adversarial attacks.
#
# Use the vectorstore for questions on these topics. For all else, and especially for current events, use web-search.
#
# Return JSON with single key, datasource, that is 'websearch' or 'vectorstore' depending on the question."""

# Test router
# test_web_search = llm_json_mode.invoke(
#     [SystemMessage(content=router_instructions)]
#     + [
#         HumanMessage(
#             content="who is winner of IPL 2024?"
#         )
#     ]
# )
# test_web_search_2 = llm_json_mode.invoke(
#     [SystemMessage(content=router_instructions)]
#     + [HumanMessage(content="who is the Cheif Minister of Andhra Pradesh in 2019 elections?")]
# )
# test_vector_store = llm_json_mode.invoke(
#     [SystemMessage(content=router_instructions)]
#     + [HumanMessage(content="GZip middleware")]
# )
# print(
#     json.loads(test_web_search.content),
#     json.loads(test_web_search_2.content),
#     json.loads(test_vector_store.content),
# )


# router_instructions = """You are an expert at routing a user question to a vectorstore or web search.
#
# The vectorstore contains documents related to agents, prompt engineering, and adversarial attacks.
#
# Use the vectorstore for questions on these topics. For all else, and especially for current events, use web-search.
#
# Return JSON with single key, datasource, that is 'websearch' or 'vectorstore' and provide answer as well for the question depending on the question."""
#
# test_web_search = llm_json_mode.invoke(
#     [SystemMessage(content=router_instructions)]
#     + [
#         HumanMessage(
#             content="who is winner of IPL 2022?"
#         )
#     ]
# )
# test_vector_store = llm_json_mode.invoke(
#     [SystemMessage(content=router_instructions)]
#     + [HumanMessage(content="what is the company he is working?")]
# )
# test_web_search_2 = llm_json_mode.invoke(
#     [SystemMessage(content=router_instructions)]
#     + [HumanMessage(content="who is the Chief Minister of Andhra Pradesh in 2014 elections?")]
# )
# print(
#     json.loads(test_web_search.content),
#     json.loads(test_vector_store.content),
#     json.loads(test_web_search_2.content)
# )

### Retrieval Grader

# Doc grader instructions
doc_grader_instructions = """You are a grader assessing relevance of a retrieved document to a user question.

If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant."""

# Grader prompt
doc_grader_prompt = """Here is the retrieved document: \n\n {document} \n\n Here is the user question: \n\n {question}.

This carefully and objectively assess whether the document contains at least some information that is relevant to the question.

Return JSON with single key, binary_score, that is 'yes' or 'no' score to indicate whether the document contains at least some information that is relevant to the question & provide answer as well for this question."""

# Test
question = "what is the current company he is working?"
docs = retriever.invoke(question)
doc_txt = docs[1].page_content
doc_grader_prompt_formatted = doc_grader_prompt.format(
    document=doc_txt, question=question
)
result = llm_json_mode.invoke(
    [SystemMessage(content=doc_grader_instructions)]
    + [HumanMessage(content=doc_grader_prompt_formatted)]
)
print(json.loads(result.content))
