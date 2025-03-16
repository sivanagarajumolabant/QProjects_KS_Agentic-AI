import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.response.pprint_utils import pprint_response

from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine.retriever_query_engine import RetrieverQueryEngine
from llama_index.core.indices.postprocessor import SimilarityPostprocessor

os.environ["OPENAI_API_KEY"] = 'sk-None-s0WHOaVSO7j098OsNYKjT3BlbkFJDA98E0grtsyw9vqGcwbh'

documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents, show_progress=True)
query_engine = index.as_query_engine()

response = query_engine.query('what is the company he is working ?')
response1 = query_engine.query('what are the skill set he is having ?')
pprint_response(response, show_source=True)
pprint_response(response1, show_source=True)
# print(response)
# print(response1)

print('===========================================================================')

retreiver = VectorIndexRetriever(index=index, similarity_top_k=5)
similarity_post_processor = SimilarityPostprocessor(similarity_cutoff=0.70)
query_eng = RetrieverQueryEngine(retriever=retreiver, node_postprocessors=[similarity_post_processor])

response = query_eng.query('what is the company he is working ?')
pprint_response(response, show_source=True)




print('================below code is for store indexes in folder use it for next time==============')

# import os.path
# from llama_index.core import (
#     VectorStoreIndex,
#     SimpleDirectoryReader,
#     StorageContext,
#     load_index_from_storage,
# )
#
# os.environ["OPENAI_API_KEY"] = 'sk-None-s0WHOaVSO7j098OsNYKjT3BlbkFJDA98E0grtsyw9vqGcwbh'
# # check if storage already exists
# PERSIST_DIR = "./storage"
# if not os.path.exists(PERSIST_DIR):
#     # load the documents and create the index
#     documents = SimpleDirectoryReader("data").load_data()
#     index = VectorStoreIndex.from_documents(documents)
#     # store it for later
#     index.storage_context.persist(persist_dir=PERSIST_DIR)
# else:
#     # load the existing index
#     storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
#     index = load_index_from_storage(storage_context)
#
# # either way we can now query the index
# query_engine = index.as_query_engine()
# response = query_engine.query("what is the company he is working ?")
# print(response)
