import os
import glob
import faiss
import pickle
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

os.environ["OPENAI_API_KEY"] = 'sk-None-s0WHOaVSO7j098OsNYKjT3BlbkFJDA98E0grtsyw9vqGcwbh'

faiss_index_path = "faiss_index.index"
docstore_path = "docstore.pkl"
index_to_docstore_id_path = "index_to_docstore_id.pkl"


def create_rag_pipeline(oracle_directory, postgres_directory):
    oracle_sql_files = glob.glob(os.path.join(oracle_directory, "**", "*.sql"), recursive=True)
    postgres_sql_files = glob.glob(os.path.join(postgres_directory, "**", "*.sql"), recursive=True)
    docs = []
    for sql_file in oracle_sql_files + postgres_sql_files:
        loader = TextLoader(sql_file)
        loaded_docs = loader.load()
        print(f"Loaded {len(loaded_docs)} documents from {sql_file}")
        docs.extend(loaded_docs)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
    documents = text_splitter.split_documents(docs)
    print(f"Total documents after splitting: {len(documents)}")

    embeddings = OpenAIEmbeddings()
    db = FAISS.from_documents(documents, embeddings)

    faiss.write_index(db.index, faiss_index_path)
    with open(docstore_path, 'wb') as f:
        pickle.dump(db.docstore, f)

    with open(index_to_docstore_id_path, 'wb') as f:
        pickle.dump(db.index_to_docstore_id, f)

    return db


def load_vector_store():
    index = faiss.read_index(faiss_index_path)
    with open(docstore_path, 'rb') as f:
        docstore = pickle.load(f)

    with open(index_to_docstore_id_path, 'rb') as f:
        index_to_docstore_id = pickle.load(f)

    return FAISS(index=index, embedding_function=OpenAIEmbeddings(), docstore=docstore,
                 index_to_docstore_id=index_to_docstore_id)


def get_conversion_response(oracle_sql_query, oracle_directory, postgres_directory):
    if os.path.exists(faiss_index_path):
        print('Loading the Existing Vector Store')
        db = load_vector_store()
    else:
        print('Creating the Vector Store')
        db = create_rag_pipeline(oracle_directory, postgres_directory)

    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

    prompt = ChatPromptTemplate.from_template("""
        You are an expert SQL conversion assistant specializing in converting Oracle SQL syntax to PostgreSQL syntax based solely on the provided data.
        Instructions:
        1. Respond with only the converted SQL code—no explanations, comments, or additional information.
        2. Accurately convert the provided Oracle SQL code into its PostgreSQL equivalent, ensuring all data types, functions, and SQL features are appropriately adapted.
        3. Pay special attention to data types: convert Oracle data types to their PostgreSQL equivalents, ensuring that VARCHAR2 becomes VARCHAR, NUMBER becomes NUMERIC, and DATE becomes TIMESTAMP WITHOUT TIME ZONE, among others.
        4. Include only the essential table structure (column names and types) and omit any constraints (e.g., primary keys, foreign keys, NOT NULL constraints, indexes, or unique constraints).
        5. Use the following context for reference during the conversion: <context> {context} </context>.
        6. If any part of the Oracle SQL code is not convertible or unclear, respond with "Conversion not available for this SQL." 
        7. Only utilize the SQL files provided in the input documents for guidance; do not reference any external knowledge or examples.
        Oracle SQL Code that needs to be converted:
        {input}
    """)

    document_chain = create_stuff_documents_chain(llm, prompt)
    retriever = db.as_retriever()
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    response = retrieval_chain.invoke({"input": oracle_sql_query})

    return response.get('answer', 'No conversion available')


oracle_directory = "Oracle"
postgres_directory = "Postgres"

oracle_sql_query = """
          CREATE OR REPLACE  PROCEDURE "REGISTRATION"."P_DELINKUHID" (IV_ParentUHID IN LinkedUHID.ParentUHID%TYPE,
                                         IV_LinkedUHID IN LinkedUHID.LinkedUHID%TYPE,
                                         IV_LoginID    IN LinkedUHID.UpdatedBy%TYPE,
                                         IV_Remarks    IN LinkedUHID.arks%TYPE)
/*//////////////////////////////////////////////////////////////////////////////////
  //
  // File Description        :        P_DelinkUHID
  // Description             :        This procedure is to delink the two records
  // Parameters              :         IV_ParentUHID    INPUT
                                       IV_LinkedUHID  INPUT
                                       IV_LoginID    INPUT
                                       IV_Remarks   INPUT

  // Returns                 :
  // ----------------------------------------------------------------------------------
  // Date Created            :          Mar 09,2007
  // Author                  :          Santosh Challa
  // -----------------------------------------------------------------------------------
  // Change History          :
  // Date Modified           :          Month DD, YYYY (e.g. Sep 08, 2006)
  // Changed By              :
  // Change Description      :
  // Version                 :
  ////////////////////////////////////////////////////////////////////////////////////*/
 AS
BEGIN

  INSERT INTO LINKEDUHID_LOG
  SELECT parentuhid,
         linkeduhid,
         filename,
         filepath,
         filetype,
         relationshipcode,
         arks,
         status,
         updatedby,
         updateddate,
         linkedupto,
         transactionid,
         SYSDATE
   FROM linkeduhid
   WHERE ParentUHID = UPPER(IV_ParentUHID) AND
         LinkedUHID = UPPER(IV_LinkedUHID);

  UPDATE LinkedUHID
     SET Status      = 0,
         UpdatedBy   = IV_LoginID,
         arks        = IV_Remarks,
         UpdatedDate = Sysdate
   WHERE ParentUHID = UPPER(IV_ParentUHID) AND
         LinkedUHID = UPPER(IV_LinkedUHID);
/*  COMMIT;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE(SQLERRM || SQLCODE);*/
END P_DelinkUHID;
        """

conversion_response = get_conversion_response(oracle_sql_query, oracle_directory, postgres_directory)

print('=====================================Conversion Response===================================')
print(conversion_response)
print('==========================================================================================')
