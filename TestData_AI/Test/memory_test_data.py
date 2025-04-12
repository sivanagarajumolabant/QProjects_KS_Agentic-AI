import os
import json
import pandas as pd
from langchain_openai import AzureChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Store to maintain session-based histories
store = {}
load_dotenv()
# Global session ID for all tables
global_session_id = "12345"

# Function to get session-specific history based on session_id
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    print(f"Retrieving history for session: {session_id}")
    if session_id not in store:
        store[session_id] = ChatMessageHistory()  # Create a new history if session doesn't exist
    return store[session_id]

# Initialize the Langchain OpenAI model
model = AzureChatOpenAI(
    api_version = "2024-12-01-preview",
    azure_endpoint="https://qmig-open-ai.openai.azure.com/",
    temperature=0.7,
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    model_name = "gpt-4o"
)
# model=ChatGroq(model="llama-3.3-70b-versatile")

# # Function to infer relationships
# def infer_relationships(tables):
#     relationships = []
#     primary_keys = {}

#     # Identify primary keys (columns with unique values)
#     for table_name, df in tables.items():
#         for col in df.columns:
#             if df[col].nunique() == len(df):  # Column has unique values
#                 primary_keys[(table_name, col)] = df[col].tolist()
#                 # Add primary key info to relationships list
#                 relationships.append({
#                     "table": table_name,
#                     "primary_key": col,
#                     "values": df[col].tolist()
#                 })

#     # Identify foreign keys (columns matching primary keys in other tables)
#     for table_name, df in tables.items():
#         for col in df.columns:
#             for (pk_table, pk_col), pk_values in primary_keys.items():
#                 if table_name != pk_table and pk_col != col and df[col].isin(pk_values).sum() > len(df) * 0.7:  # 70% match
#                     relationships.append({
#                         "table": table_name,
#                         "column": col,
#                         "references": pk_table,
#                         "referenced_column": pk_col
#                     })

#     return relationships

import re


def parse_ddl(ddl_statements):
    relationships = []

    # Regular expression patterns for primary key and foreign key extraction
    pk_pattern = re.compile(r'PRIMARY KEY\s*\((\w+)\)')
    fk_pattern = re.compile(r'FOREIGN KEY\s*\((\w+)\)\s*REFERENCES\s*(\w+)\.(\w+)\s*\((\w+)\)')

    for ddl in ddl_statements:
        # Search for primary key
        pk_match = pk_pattern.search(ddl)
        if pk_match:
            pk_column = pk_match.group(1)
            table_name = ddl.split()[2]  # Get table name from CREATE TABLE statement
            relationships.append({
                "table": table_name,
                "primary_key": pk_column
            })
        
        # Search for foreign keys
        fk_matches = fk_pattern.findall(ddl)
        for fk in fk_matches:
            fk_column, table_name , referenced_table, referenced_column,  = fk
            # table_name = ddl.split()[2]  # Get table name from CREATE TABLE statement
            relationships.append({
                "table": table_name,
                "foreign_key": fk_column,
                "references": referenced_table,
                "referenced_column": referenced_column
            })

    return relationships


def print_session_history(session_id):
    history = get_session_history(session_id)
    print(f"Session history for session {session_id}:")
    for message in history.messages:
        print(f"Message: {message.content} | Type: {message.__class__.__name__}")

# Track all generated primary keys across tables
# generated_primary_keys = {}

def generate_data_for_table_with_history(all_generated_data, table_name, table_df, detected_relationships, records_per_batch=5, total_records=25):
    # Identify primary key for this table
    primary_key = None
    for rel in detected_relationships:
        if "primary_key" in rel and rel["table"] == table_name.split('-')[1].strip():
            primary_key = rel["primary_key"]
            break
    
    # Get foreign key relationships for this table
    foreign_key = []
    for rel in detected_relationships:
        if "references" in rel and rel["table"] == table_name.split('-')[1].strip():
            foreign_key.append(rel)
            
    num_batches = total_records // records_per_batch

    # Wrap the model with message history using global session history
    with_message_history = RunnableWithMessageHistory(model, get_session_history)
    
    print(detected_relationships)
    
    for batch_num in range(num_batches):
        print(f'Generating batch {batch_num + 1} for {table_name}')

        # Prepare a more specific prompt to maintain relationships
        prompt = f"""
        I have a related SQL table '{table_name}' stored in an Excel file. The table has the following structure and inferred relationships.

        Detected Relationships:
        Primary Key : {primary_key}
        Foreign Keys: {', '.join([rel['foreign_key'] for rel in foreign_key])}

        Table Structure & Data Patterns:
        {{ "file_name": "{table_name}", "schema": {{
            "columns": {json.dumps(list(table_df.columns))},
            "sample_data": {json.dumps(table_df.head(5).to_dict(orient="records"))},
            "column_distributions": {json.dumps({col: table_df[col].value_counts(normalize=True).to_dict() for col in table_df.columns})}
        }} }}

        **Task:** Generate {records_per_batch} unique test records for the table while preserving the same format as the input file.
        - Keep the same column names and data types.
        - Maintain primary key uniqueness and foreign key relationships.
        - Distribute values similarly to the original dataset but ensure that the generated values do not match any existing values in the input files.
        - Ensure that the generated data is different from all previously generated data in this session (i.e., do not repeat any previously generated records across all interactions within the session).
        - If the table has a primary key, DO NOT generate duplicate primary key values that already exist in the dataset or in previously generated records from this session.
        - If the table has foreign key relationships, ensure the foreign key values are valid and follow the relationships with referenced tables.

        IMPORTANT: Return ONLY a valid JSON object with this structure: {{ "{table_name}": [{{column1: value, column2: value, ...}}] }}
        NO markdown, NO code blocks, NO explanations - ONLY the JSON object.
        """
        
        # Create the chat message
        messages = [
            SystemMessage(content="You are an AI that generates structured test data while maintaining database integrity constraints."),
            HumanMessage(content=prompt),
        ]

        # Send the prompt to Langchain OpenAI model with global session-specific message history
        try:
            response = with_message_history.invoke(messages, config={"configurable": {"session_id": global_session_id}})
            print(response)
            response_text = response.content
            
            # print_session_history(global_session_id)
            
            try:
                generated_data = json.loads(response_text)
                new_records = generated_data[table_name]  # Extract the batch of records
                print(f'Generated {len(new_records)} records for {table_name}')
                # Add the valid records to all generated data
                all_generated_data.extend(new_records)

                if len(all_generated_data) >= total_records:
                    break

            except json.JSONDecodeError as e:
                print(f"JSON decode error for {table_name}: {e}")
                print(f"Raw response: {response_text[:500]}...")

        except Exception as e:
            print(f"Error generating data for {table_name} (batch {batch_num + 1}): {e}")
            continue
    
    # if len(all_generated_data) < total_records:
    #     print('Attempted to generate less records than requested')
    #     all_generated_data = generate_data_for_table_with_history(all_generated_data, table_name, table_df, detected_relationships, records_per_batch=5, total_records=100)
    return all_generated_data

# Define file paths and read tables
files = 'C:/QProjects/TestData_AI/New_data'
input_files = [file for file in os.listdir(files)]
output_dir = "generated_test_data_new_data_memory1"
os.makedirs(output_dir, exist_ok=True)

# Read all tables into DataFrames
tables = {os.path.splitext(file.lower())[0]: pd.read_csv(os.path.join(files, file)) for file in input_files}

# Main logic to process each table one by one
# detected_relationships = infer_relationships(tables)
from ddl_data import ddl_statements
relationships = parse_ddl(ddl_statements)

# Print inferred relationships for verification
print("Inferred Relationships:")
for relationship in relationships:
    print(relationship)

# Generate data for each table in the determined order
for table_name in tables:
    df = tables[table_name]
    print(f"Generating test data for {table_name}...")
    
    generated_records = []
    generated_records = generate_data_for_table_with_history(
        generated_records, 
        table_name, 
        df, 
        relationships,
        records_per_batch=5,
        total_records=25
    )
    
    if generated_records:
        # Limit to 20 records if more were generated
        generated_records = generated_records[:20] if len(generated_records) > 20 else generated_records
        output_path = os.path.join(output_dir, f"{table_name}.csv")
        print(f"Saving {len(generated_records)} generated records for {table_name} to {output_path}...")
        generated_df = pd.DataFrame(generated_records)
        generated_df.to_csv(output_path, index=False)
    else:
        print(f"Failed to generate data for {table_name}")

print(f"Test data generation complete. Output saved in '{output_dir}' folder.")