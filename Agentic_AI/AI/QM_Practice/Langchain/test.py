# import os
# import re
# import glob
# import pandas as pd
# import faiss
# import numpy as np
# from sentence_transformers import SentenceTransformer
# from dotenv import load_dotenv

# load_dotenv()


# def retrieve_comments(source_data):
#     source_data = re.sub(r'\-\-+', '--', source_data)
#     source_data = source_data.replace('--','\n--')
 
#     comments_dictionary = {}
#     comment_identifiers = 'Start: /* End: */&Start: -- End: \\n'
 
#     comment_identifiers = re.sub(' +', ' ', comment_identifiers).lower()
#     current_comment_identifiers_split_list = comment_identifiers.split('&')
 
#     counter = 0
#     for comment_rule in current_comment_identifiers_split_list:
#         start_key = comment_rule.split('end:')[0].split('start:')[1].strip()
#         end_key = comment_rule.split('end:')[1].strip()
 
#         if '-' in start_key:
#             start_key = start_key.replace('-', '\-')
#         elif '/' in start_key or '*' in start_key:
#             start_key = start_key.replace('/', '\/').replace('*', '\*')
#         if '*/' in end_key:
#             end_key = end_key.replace('*/', '\*/')
#         comments_data_list = re.findall(rf"{start_key}[\s\S]*?{end_key}", source_data)
 
#         for comments_data in comments_data_list:
#             if '-' in start_key:
#                 source_data = source_data.replace(comments_data,
#                                                   ' comment_quad_marker_' + str(counter) + '_us' + ' \n')
#                 comments_dictionary['comment_quad_marker_' + str(counter) + '_us'] = comments_data
#             else:
#                 comments_data_modified = '/*' + comments_data.replace('/*', '').replace('*/',
#                                                                                         '').replace('/',
#                                                                                                     '') + '*/'
#                 source_data = source_data.replace(comments_data, comments_data_modified)
#                 source_data = source_data.replace(comments_data_modified,
#                                                   ' comment_quad_marker_' + str(counter) + '_us' + ' \n')
#                 comments_dictionary['comment_quad_marker' + str(counter) + '_us'] = comments_data_modified
#             counter += 1
#     return source_data, comments_dictionary


# def retrieve_singlequote_data(source_data):
#     single_quote_comment_dictionary = {}
 
#     arrow_comments = re.findall(r"\-+\>", source_data)
#     for comment in arrow_comments:
#         source_data = source_data.replace(comment, 'arrow_quad_marker', 1)
 
#     singlequote_data = re.findall(r"\'.*?\'", source_data, flags=re.DOTALL)
 
#     if len(singlequote_data):
#         counter = 0
#         for i in singlequote_data:
#             if i.strip().lower() in source_data.lower().strip():
#                 unique_marker = ' single_quote_quad_marker_' + str(counter) + '_us '
#                 source_data = source_data.replace(i, unique_marker, 1)
#                 single_quote_comment_dictionary[unique_marker] = i
#             counter = counter + 1
#     else:
#         source_data = source_data
#     return source_data, single_quote_comment_dictionary


# def split_sql_file_into_statements(file_path):
#     with open(file_path, "r", encoding="utf-8") as file:
#         content = file.read()
        
#     # Remove comments and single quotes
#     content, single_quote_comment_dictionary = retrieve_singlequote_data(content)
#     content, comments_dictionary = retrieve_comments(content)
#     content = re.sub(r'\bcomment_quad_marker_\d+_us\b', '', content,
#                          flags=re.IGNORECASE | re.DOTALL)
#     content = re.sub(r'\bsingle_quote_quad_marker_\d+_us\b', '', content,
#                          flags=re.IGNORECASE | re.DOTALL)
#     content = re.sub(r'\barrow_quad_marker\b', '', content,
#                          flags=re.IGNORECASE | re.DOTALL)
#     content = re.sub(r' +', ' ', content)
#     # Remove comments and single quotes
    
#     content = "\n".join([line for line in content.splitlines() if line.strip()])
#     statements = [stmt.strip() + ";" for stmt in content.split(";")]
#     statements = [stmt for stmt in statements if stmt.strip() != ";"]
#     return statements

# def normalize_sql(sql):
#     # sql = re.sub(r"--.*", "", sql)  # Remove comments
#     # sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)  # Remove block comments
#     sql = re.sub(r"\s+", " ", sql).strip()  # Normalize whitespaces
#     return sql

# source_directory_path = "Practice/Langchain/Source"
# target_directory_path = "Practice/Langchain/Target"

# source_sql_files = glob.glob(
#     os.path.join(source_directory_path, "**", "*.sql"), recursive=True
# )
# target_sql_files = glob.glob(
#     os.path.join(target_directory_path, "**", "*.sql"), recursive=True
# )

# source_statements = []
# for sql_file in source_sql_files:
#     statements = split_sql_file_into_statements(sql_file)
#     for idx, stmt in enumerate(statements):
#         source_statements.append(
#             {"content": normalize_sql(stmt), "file": sql_file, "line_number": idx + 1}
#         )

# target_statements = []
# for sql_file in target_sql_files:
#     statements = split_sql_file_into_statements(sql_file)
#     for idx, stmt in enumerate(statements):
#         target_statements.append(
#             {"content": normalize_sql(stmt), "file": sql_file, "line_number": idx + 1}
#         )

# # Embed all SQL statements using a pre-trained model
# model = SentenceTransformer("all-MiniLM-L6-v2")

# # Generate embeddings and normalize them to unit vectors
# source_embeddings = model.encode([stmt["content"] for stmt in source_statements])
# target_embeddings = model.encode([stmt["content"] for stmt in target_statements])

# source_embeddings_norm = source_embeddings / np.linalg.norm(source_embeddings, axis=1, keepdims=True)
# target_embeddings_norm = target_embeddings / np.linalg.norm(target_embeddings, axis=1, keepdims=True)

# # Use FAISS with Inner Product (cosine similarity)
# dimension = source_embeddings_norm.shape[1]
# index_source_to_target = faiss.IndexFlatIP(dimension)
# index_target_to_source = faiss.IndexFlatIP(dimension)

# index_source_to_target.add(target_embeddings_norm)
# index_target_to_source.add(source_embeddings_norm)

# # Dictionaries to store matches
# best_source_matches = {}
# best_target_matches = {}
# threshold = 0.8
# k = 5  # Retrieve top 5 candidates

# # Process source statements
# for source_idx, source in enumerate(source_statements):
#     source_embedding = source_embeddings_norm[source_idx]
#     similarities, indices = index_source_to_target.search(np.array([source_embedding]), k=k)
    
#     best_match_idx = None
#     best_similarity = -1
#     best_line_diff = float('inf')
    
#     for i in range(k):
#         candidate_idx = indices[0][i]
#         if candidate_idx >= len(target_statements):
#             continue
        
#         similarity = similarities[0][i]
#         if similarity < threshold:
#             continue
        
#         line_diff = abs(source["line_number"] - target_statements[candidate_idx]["line_number"])
        
#         if (similarity > best_similarity) or (similarity == best_similarity and line_diff < best_line_diff):
#             best_similarity = similarity
#             best_match_idx = candidate_idx
#             best_line_diff = line_diff
    
#     if best_match_idx is not None:
#         if (best_match_idx not in best_target_matches or 
#             best_similarity > best_target_matches[best_match_idx]["similarity_score"]):
#             if best_match_idx in best_target_matches:
#                 prev_source_idx = best_target_matches[best_match_idx]["source_idx"]
#                 del best_source_matches[prev_source_idx]
                
#             best_source_matches[source_idx] = {
#                 "target_idx": best_match_idx,
#                 "similarity_score": best_similarity,
#             }
#             best_target_matches[best_match_idx] = {
#                 "source_idx": source_idx,
#                 "similarity_score": best_similarity,
#             }

# # Process target statements
# for target_idx, target in enumerate(target_statements):
#     target_embedding = target_embeddings_norm[target_idx]
#     similarities, indices = index_target_to_source.search(np.array([target_embedding]), k=k)
    
#     best_match_idx = None
#     best_similarity = -1
#     best_line_diff = float('inf')
    
#     for i in range(k):
#         candidate_idx = indices[0][i]
#         if candidate_idx >= len(source_statements):
#             continue
        
#         similarity = similarities[0][i]
#         if similarity < threshold:
#             continue
        
#         line_diff = abs(target["line_number"] - source_statements[candidate_idx]["line_number"])
        
#         if (similarity > best_similarity) or (similarity == best_similarity and line_diff < best_line_diff):
#             best_similarity = similarity
#             best_match_idx = candidate_idx
#             best_line_diff = line_diff
    
#     if best_match_idx is not None:
#         if (best_match_idx not in best_source_matches or 
#             best_similarity > best_source_matches[best_match_idx]["similarity_score"]):
#             if best_match_idx in best_source_matches:
#                 prev_target_idx = best_source_matches[best_match_idx]["target_idx"]
#                 del best_target_matches[prev_target_idx]
                
#             best_target_matches[target_idx] = {
#                 "source_idx": best_match_idx,
#                 "similarity_score": best_similarity,
#             }
#             best_source_matches[best_match_idx] = {
#                 "target_idx": target_idx,
#                 "similarity_score": best_similarity,
#             }

# # Generate results based on best matches (same as before)
# results = []
# for source_idx, source in enumerate(source_statements):
#     if source_idx in best_source_matches:
#         target_idx = best_source_matches[source_idx]["target_idx"]
#         similarity_score = best_source_matches[source_idx]["similarity_score"]
#         target = target_statements[target_idx]
#         results.append(
#             {
#                 "Source SQL Statement": source["content"],
#                 "Target SQL Statement": target["content"],
#                 "Similarity Score": similarity_score,
#                 "Source File": source["file"],
#                 "Target File": target["file"],
#                 "Source Line": source["line_number"],
#                 "Target Line": target["line_number"],
#             }
#         )
#     else:
#         results.append(
#             {
#                 "Source SQL Statement": source["content"],
#                 "Target SQL Statement": "No match found",
#                 "Similarity Score": similarity_score,
#                 "Source File": source["file"],
#                 "Target File": target["file"],
#                 "Source Line": source["line_number"],
#                 "Target Line": "",
#             }
#         )

# print(best_target_matches)
# for target_idx, target in enumerate(target_statements):
#     if target_idx not in best_target_matches:
#         print(target_idx)
#         print(target_statements[target_idx])
#         results.append(
#             {
#                 "Source SQL Statement": "No match found",
#                 "Target SQL Statement": target["content"],
#                 "Similarity Score": 0,
#                 "Source File": source["file"],
#                 "Target File": target["file"],
#                 "Source Line": "",
#                 "Target Line": target["line_number"],
#             }
#         )

# # Save to file
# df_results = pd.DataFrame(results)
# df_results = df_results.sort_values(by=['Source Line', 'Target Line'], ascending=[True, True])
# output_file = "Practice/Langchain/sql_mapping_results_ordered_separate2.xlsx"
# df_results.to_excel(output_file, index=False)






import os
import re
import glob
import pandas as pd
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()


def retrieve_comments(source_data):
    source_data = re.sub(r'\-\-+', '--', source_data)
    source_data = source_data.replace('--','\n--')
 
    comments_dictionary = {}
    comment_identifiers = 'Start: /* End: */&Start: -- End: \\n'
 
    comment_identifiers = re.sub(' +', ' ', comment_identifiers).lower()
    current_comment_identifiers_split_list = comment_identifiers.split('&')
 
    counter = 0
    for comment_rule in current_comment_identifiers_split_list:
        start_key = comment_rule.split('end:')[0].split('start:')[1].strip()
        end_key = comment_rule.split('end:')[1].strip()
 
        if '-' in start_key:
            start_key = start_key.replace('-', '\-')
        elif '/' in start_key or '*' in start_key:
            start_key = start_key.replace('/', '\/').replace('*', '\*')
        if '*/' in end_key:
            end_key = end_key.replace('*/', '\*/')
        comments_data_list = re.findall(rf"{start_key}[\s\S]*?{end_key}", source_data)
 
        for comments_data in comments_data_list:
            if '-' in start_key:
                source_data = source_data.replace(comments_data,
                                                  ' comment_quad_marker_' + str(counter) + '_us' + ' \n')
                comments_dictionary['comment_quad_marker_' + str(counter) + '_us'] = comments_data
            else:
                comments_data_modified = '/*' + comments_data.replace('/*', '').replace('*/',
                                                                                        '').replace('/',
                                                                                                    '') + '*/'
                source_data = source_data.replace(comments_data, comments_data_modified)
                source_data = source_data.replace(comments_data_modified,
                                                  ' comment_quad_marker_' + str(counter) + '_us' + ' \n')
                comments_dictionary['comment_quad_marker' + str(counter) + '_us'] = comments_data_modified
            counter += 1
    return source_data, comments_dictionary


def retrieve_singlequote_data(source_data):
    single_quote_comment_dictionary = {}
 
    arrow_comments = re.findall(r"\-+\>", source_data)
    for comment in arrow_comments:
        source_data = source_data.replace(comment, 'arrow_quad_marker', 1)
 
    singlequote_data = re.findall(r"\'.*?\'", source_data, flags=re.DOTALL)
 
    if len(singlequote_data):
        counter = 0
        for i in singlequote_data:
            if i.strip().lower() in source_data.lower().strip():
                unique_marker = ' single_quote_quad_marker_' + str(counter) + '_us '
                source_data = source_data.replace(i, unique_marker, 1)
                single_quote_comment_dictionary[unique_marker] = i
            counter = counter + 1
    else:
        source_data = source_data
    return source_data, single_quote_comment_dictionary


def split_sql_file_into_statements(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        
    # Remove comments and single quotes
    content, single_quote_comment_dictionary = retrieve_singlequote_data(content)
    content, comments_dictionary = retrieve_comments(content)
    content = re.sub(r'\bcomment_quad_marker_\d+_us\b', '', content,
                         flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'\bsingle_quote_quad_marker_\d+_us\b', '', content,
                         flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'\barrow_quad_marker\b', '', content,
                         flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r' +', ' ', content)
    # Remove comments and single quotes
    content = "\n".join([line for line in content.splitlines() if line.strip()])
    statements = [stmt.strip() + ";" for stmt in content.split(";")]
    statements = [stmt for stmt in statements if stmt.strip() != ";"]
    return statements

def normalize_sql(sql):
    # sql = re.sub(r"--.*", "", sql)  # Remove comments
    # sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)  # Remove block comments
    sql = re.sub(r"\s+", " ", sql).strip()  # Normalize whitespaces
    return sql

source_directory_path = "Practice/Langchain/Source"
target_directory_path = "Practice/Langchain/Target"

source_sql_files = glob.glob(
    os.path.join(source_directory_path, "**", "*.sql"), recursive=True
)
target_sql_files = glob.glob(
    os.path.join(target_directory_path, "**", "*.sql"), recursive=True
)

source_statements = []
for sql_file in source_sql_files:
    statements = split_sql_file_into_statements(sql_file)
    print(statements)
    for idx, stmt in enumerate(statements):
        source_statements.append(
            {"content": normalize_sql(stmt), "file": sql_file, "line_number": idx + 1}
        )

target_statements = []
for sql_file in target_sql_files:
    statements = split_sql_file_into_statements(sql_file)
    print(statements)
    for idx, stmt in enumerate(statements):
        target_statements.append(
            {"content": normalize_sql(stmt), "file": sql_file, "line_number": idx + 1}
        )

# Embed all SQL statements using a pre-trained model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Generate embeddings and normalize them to unit vectors
source_embeddings = model.encode([stmt["content"] for stmt in source_statements])
target_embeddings = model.encode([stmt["content"] for stmt in target_statements])

source_embeddings_norm = source_embeddings / np.linalg.norm(source_embeddings, axis=1, keepdims=True)
target_embeddings_norm = target_embeddings / np.linalg.norm(target_embeddings, axis=1, keepdims=True)

# Use FAISS with Inner Product (cosine similarity)
dimension = source_embeddings_norm.shape[1]
index_source_to_target = faiss.IndexFlatIP(dimension)
index_target_to_source = faiss.IndexFlatIP(dimension)

index_source_to_target.add(target_embeddings_norm)
index_target_to_source.add(source_embeddings_norm)

# Dictionaries to store matches
best_source_matches = {}
best_target_matches = {}
threshold = 0.8
k = 5  # Retrieve top 5 candidates

matched_target_indices = set()
# Process source statements
for source_idx, source in enumerate(source_statements):
    source_embedding = source_embeddings_norm[source_idx]
    similarities, indices = index_source_to_target.search(np.array([source_embedding]), k=k)
    
    best_match_idx = None
    best_similarity = -1
    best_line_diff = float('inf')
    
    for i in range(k):
        candidate_idx = indices[0][i]
        if candidate_idx >= len(target_statements) or candidate_idx in matched_target_indices:
            continue
        
        similarity = similarities[0][i]
        if similarity < threshold:
            continue
        
        line_diff = abs(source["line_number"] - target_statements[candidate_idx]["line_number"])
        
        if (similarity > best_similarity) or (similarity == best_similarity and line_diff < best_line_diff):
            best_similarity = similarity
            best_match_idx = candidate_idx
            best_line_diff = line_diff
    
    if best_match_idx is not None:
        matched_target_indices.add(best_match_idx)
        best_source_matches[source_idx] = {
            "target_idx": best_match_idx,
            "similarity_score": best_similarity,
        }
        best_target_matches[best_match_idx] = {
            "source_idx": source_idx,
            "similarity_score": best_similarity,
        }

# Process target statements
for target_idx, target in enumerate(target_statements):
    if target_idx in matched_target_indices:
        continue  # Skip already matched targets
    
    target_embedding = target_embeddings_norm[target_idx]
    similarities, indices = index_target_to_source.search(np.array([target_embedding]), k=k)
    
    best_match_idx = None
    best_similarity = -1
    best_line_diff = float('inf')
    
    for i in range(k):
        candidate_idx = indices[0][i]
        if candidate_idx >= len(source_statements):
            continue
        
        similarity = similarities[0][i]
        if similarity < threshold:
            continue
        
        line_diff = abs(target["line_number"] - source_statements[candidate_idx]["line_number"])
        
        if (similarity > best_similarity) or (similarity == best_similarity and line_diff < best_line_diff):
            best_similarity = similarity
            best_match_idx = candidate_idx
            best_line_diff = line_diff
    
    if best_match_idx is not None:
        matched_target_indices.add(target_idx)
        best_target_matches[target_idx] = {
            "source_idx": best_match_idx,
            "similarity_score": best_similarity,
        }
        best_source_matches[best_match_idx] = {
            "target_idx": target_idx,
            "similarity_score": best_similarity,
        }

# Generate results based on best matches (same as before)
results = []
for source_idx, source in enumerate(source_statements):
    if source_idx in best_source_matches:
        target_idx = best_source_matches[source_idx]["target_idx"]
        similarity_score = best_source_matches[source_idx]["similarity_score"]
        target = target_statements[target_idx]
        results.append(
            {
                "Source SQL Statement": source["content"],
                "Target SQL Statement": target["content"],
                "Similarity Score": similarity_score,
                "Source File": source["file"],
                "Target File": target["file"],
                "Source Line": source["line_number"],
                "Target Line": target["line_number"],
            }
        )
    else:
        results.append(
            {
                "Source SQL Statement": source["content"],
                "Target SQL Statement": "No match found",
                "Similarity Score": similarity_score,
                "Source File": source["file"],
                "Target File": target["file"],
                "Source Line": source["line_number"],
                "Target Line": "",
            }
        )

for target_idx, target in enumerate(target_statements):
    if target_idx not in best_target_matches:
        print(target_idx)
        print(target_statements[target_idx])
        results.append(
            {
                "Source SQL Statement": "No match found",
                "Target SQL Statement": target["content"],
                "Similarity Score": 0,
                "Source File": source["file"],
                "Target File": target["file"],
                "Source Line": "",
                "Target Line": target["line_number"],
            }
        )

# Save to file
df_results = pd.DataFrame(results)
df_results = df_results.sort_values(by=['Source Line', 'Target Line'], ascending=[True, True])
output_file = "Practice/Langchain/sql_mapping_results_ordered_separate2.xlsx"
df_results.to_excel(output_file, index=False)