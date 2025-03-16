import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from dotenv import load_dotenv
load_dotenv()

def parse_sql_statements(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]
    return statements

# File paths
source_directory_path = "C:\Repos\Agentic_AI\QM_Practice\Langchain\Source\manage_hr_data_cuurent.sql"
target_directory_path = "C:\Repos\Agentic_AI\QM_Practice\Langchain\Target\manage_hr_data_baseline.sql"

# Parse SQL statements
source_statements = parse_sql_statements(source_directory_path)
target_statements = parse_sql_statements(target_directory_path)

# Create documents with metadata
source_docs = [
    Document(
        page_content=stmt,
        metadata={"file_name": source_directory_path, "line_number": i + 1}
    )
    for i, stmt in enumerate(source_statements)
]

target_docs = [
    Document(
        page_content=stmt,
        metadata={"file_name": target_directory_path, "line_number": i + 1}
    )
    for i, stmt in enumerate(target_statements)
]

# Initialize embeddings
embeddings = OpenAIEmbeddings()

# Create FAISS index for target documents
target_vectorstore = FAISS.from_documents(target_docs, embeddings)

# Track matched indices
matched_source_indices = set()
matched_target_indices = set()
mappings = []

# Match source to target
for source_idx, source_doc in enumerate(source_docs):
    if source_idx in matched_source_indices:
        continue
    # Retrieve the most similar target
    docs_with_scores = target_vectorstore.similarity_search_with_score(source_doc.page_content, k=1)
    if docs_with_scores:
        target_doc, score = docs_with_scores[0]
        r_cosine = 1 - (score ** 2) / 2
        if r_cosine >= 0.8:
            target_idx = target_doc.metadata['line_number'] - 1  # Adjust for 0-based index
            if target_idx not in matched_target_indices:
                # Check reverse match (target to source)
                source_for_target = FAISS.from_documents([source_doc], embeddings)
                reverse_docs = source_for_target.similarity_search_with_score(target_doc.page_content, k=1)
                if reverse_docs:
                    reverse_source_doc, reverse_score = reverse_docs[0]
                    rsource_cosine = 1 - (reverse_score ** 2) / 2
                    if rsource_cosine >= 0.8 and reverse_source_doc.metadata['line_number'] == source_doc.metadata['line_number']:
                        mappings.append((source_doc, target_doc, r_cosine))
                        matched_source_indices.add(source_idx)
                        matched_target_indices.add(target_idx)

# Match remaining targets to sources (bidirectional check)
for target_idx, target_doc in enumerate(target_docs):
    if target_idx in matched_target_indices:
        continue
    # Retrieve the most similar source
    source_vectorstore = FAISS.from_documents(source_docs, embeddings)
    docs_with_scores = source_vectorstore.similarity_search_with_score(target_doc.page_content, k=1)
    if docs_with_scores:
        source_doc, score = docs_with_scores[0]
        source_cosine = 1 - (score ** 2) / 2
        if source_cosine >= 0.8:
            source_idx = source_doc.metadata['line_number'] - 1
            if source_idx not in matched_source_indices:
                # Check reverse match (source to target)
                target_vectorstore_temp = FAISS.from_documents([target_doc], embeddings)
                reverse_docs = target_vectorstore_temp.similarity_search_with_score(source_doc.page_content, k=1)
                if reverse_docs:
                    reverse_target_doc, reverse_score = reverse_docs[0]
                    t_cosine = 1 - (reverse_score ** 2) / 2
                    if t_cosine >= 0.8 and reverse_target_doc.metadata['line_number'] == target_doc.metadata['line_number']:
                        mappings.append((source_doc, target_doc, source_cosine))
                        matched_source_indices.add(source_idx)
                        matched_target_indices.add(target_idx)

# Prepare final rows maintaining original order
final_rows = []

# Process all source documents in order
for source_idx, source_doc in enumerate(source_docs):
    matched = False
    for (src, tgt, score) in mappings:
        if src.metadata['line_number'] == source_doc.metadata['line_number'] and src.page_content == source_doc.page_content:
            final_rows.append({
                "source_statement": src.page_content,
                "source_file_name": src.metadata['file_name'],
                "source_line_number": src.metadata['line_number'],
                "target_statement": tgt.page_content,
                "target_file_name": tgt.metadata['file_name'],
                "target_line_number": tgt.metadata['line_number'],
                "similarity_score": score,
                "match_status": "Matched" if score >= 0.8 else "Low Confidence Match"
            })
            matched = True
            break
    if not matched:
        # Find the best match for the unmatched source statement
        docs_with_scores = target_vectorstore.similarity_search_with_score(source_doc.page_content, k=1)
        if docs_with_scores:
            best_match, best_score = docs_with_scores[0]
            cosine_similarity = 1 - (best_score ** 2) / 2
            if best_match.metadata['line_number'] - 1 not in matched_target_indices:  # Ensure target is not already matched
                final_rows.append({
                    "source_statement": source_doc.page_content,
                    "source_file_name": source_doc.metadata['file_name'],
                    "source_line_number": source_doc.metadata['line_number'],
                    "target_statement": best_match.page_content,
                    "target_file_name": best_match.metadata['file_name'],
                    "target_line_number": best_match.metadata['line_number'],
                    "similarity_score": cosine_similarity,
                    "match_status": "Matched" if cosine_similarity >= 0.8 else "Low Confidence Match"
                })
                matched_target_indices.add(best_match.metadata['line_number'] - 1)  # Mark target as matched
        else:
            final_rows.append({
                "source_statement": source_doc.page_content,
                "source_file_name": source_doc.metadata['file_name'],
                "source_line_number": source_doc.metadata['line_number'],
                "target_statement": "no Match Found",
                "target_file_name": "",
                "target_line_number": "",
                "similarity_score": 0.0,
                "match_status": "No Match"
            })

# Process all target documents in order for unmatched targets
for target_idx, target_doc in enumerate(target_docs):
    if target_idx not in matched_target_indices:
        # Find the best match for the unmatched target statement
        source_vectorstore = FAISS.from_documents(source_docs, embeddings)
        docs_with_scores = source_vectorstore.similarity_search_with_score(target_doc.page_content, k=1)
        if docs_with_scores:
            best_match, best_score = docs_with_scores[0]
            cosine_similarity = 1 - (best_score ** 2) / 2
            if best_match.metadata['line_number'] - 1 not in matched_source_indices:  # Ensure source is not already matched
                final_rows.append({
                    "source_statement": best_match.page_content,
                    "source_file_name": best_match.metadata['file_name'],
                    "source_line_number": best_match.metadata['line_number'],
                    "target_statement": target_doc.page_content,
                    "target_file_name": target_doc.metadata['file_name'],
                    "target_line_number": target_doc.metadata['line_number'],
                    "similarity_score": cosine_similarity,
                    "match_status": "Matched" if cosine_similarity >= 0.8 else "Low Confidence Match"
                })
                matched_source_indices.add(best_match.metadata['line_number'] - 1)  # Mark source as matched
        else:
            final_rows.append({
                "source_statement": "no Match Found",
                "source_file_name": "",
                "source_line_number": "",
                "target_statement": target_doc.page_content,
                "target_file_name": target_doc.metadata['file_name'],
                "target_line_number": target_doc.metadata['line_number'],
                "similarity_score": 0.0,
                "match_status": "No Match"
            })

# Create DataFrame
df = pd.DataFrame(final_rows)

# Sort the DataFrame by source line number and target line number to maintain order
df.sort_values(by=['source_line_number', 'target_line_number'], inplace=True)

# Save to Excel
df.to_excel("C:/Repos/Agentic_AI/QM_Practice/Langchain/output.xlsx", index=False)