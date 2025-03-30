# import os, re, json, pandas as pd, openai, time
# # Azure OpenAI Configuration
# AZURE_OAI_KEY = "AYxiyqI41yG0k6Yh6eFJNNBg2yy8iSwnAgSd4beaFT3qMyTJjWmrJQQJ99ALACYeBjFXJ3w3AAABACOGHzA8"
# AZURE_OAI_MODEL = "gpt-4o"
# AZURE_OPENAI_ENDPOINT = "https://az-pii.openai.azure.com/"
# AZURE_OPENAI_VERSION = "2023-08-01-preview"


# # Initialize OpenAI client
# client = openai.AzureOpenAI(
#     api_key=AZURE_OAI_KEY,
#     api_version=AZURE_OPENAI_VERSION,
#     azure_endpoint=AZURE_OPENAI_ENDPOINT,
# )



# # Define file paths
# files = 'C:/QProjects/TestData_AI/Input_Files'
# input_files = [file for file in os.listdir(files)]
# output_dir = "generated_test_data_w"
# os.makedirs(output_dir, exist_ok=True)

# # Read all tables into DataFrames
# tables = {file.lower(): pd.read_csv(files + '/' + file) for file in input_files}

# # Function to infer primary and foreign key relationships
# def infer_relationships(tables):
#     relationships = []
#     primary_keys = {}

#     # Identify primary keys (columns with unique values)
#     for table_name, df in tables.items():
#         for col in df.columns:
#             if df[col].nunique() == len(df):  # Column has unique values
#                 primary_keys[(table_name, col)] = df[col].tolist()

#     # Identify foreign keys (columns matching primary keys in other tables)
#     for table_name, df in tables.items():
#         for col in df.columns:
#             for (pk_table, pk_col), pk_values in primary_keys.items():
#                 if col != pk_col and df[col].isin(pk_values).sum() > len(df) * 0.8:  # 80% match
#                     relationships.append({
#                         "table": table_name,
#                         "column": col,
#                         "references": pk_table,
#                         "referenced_column": pk_col
#                     })

#     return relationships

# # Function to generate data for a single table in batches, using all previous data
# def generate_data_for_table(table_name, table_df, detected_relationships, records_per_batch=2, total_records=100):
#     all_generated_data = []  # List to store all generated data
#     previous_generated_data = []  # Keep track of all previous batches' records
    
#     # Number of batches we need
#     num_batches = total_records // records_per_batch
#     print('num_batches:', num_batches)
#     for batch_num in range(num_batches):
#         print('batch_num:', batch_num)
#         # Convert all previous generated data into a format that can be passed in the prompt
#         # previous_data = json.dumps(previous_generated_data[-5:])  # We limit the previous data context to 5 records
#         previous_data = json.dumps(previous_generated_data)  # We limit the previous data context to 5 records

#         prompt = f"""
#         I have a related SQL table '{table_name}' stored in an Excel file. The table has the following structure and inferred relationships.

#         Detected Relationships:
#         {json.dumps(detected_relationships, indent=2)}

#         Table Structure & Data Patterns:
#         {{ "file_name": "{table_name}", "schema": {{
#             "columns": {json.dumps(list(table_df.columns))},
#             "sample_data": {json.dumps(table_df.head(5).to_dict(orient="records"))},
#             "column_distributions": {json.dumps({col: table_df[col].value_counts(normalize=True).to_dict() for col in table_df.columns})}
#         }} }}

#         **Task:** Generate {records_per_batch} unique test records for the table while preserving the same format as the input file.
#         - Keep the same column names and data types.
#         - Maintain primary key uniqueness and foreign key relationships.
#         - Distribute values similarly to the original dataset but ensure that the generated values do not match any existing values in the input files.
#         - Ensure the generated data is different from all previously generated data: {previous_data}
#         - Return the output as a complete and valid JSON object with this structure: {{ {table_name}: [{{column1: value, column2: value, ...}}] }}. Ensure the response is properly closed and contains all necessary brackets and commas.
#         """
        
        
#         max_retries = 5
#         retry_count = 0
#         backoff_time = 60  # Start with 60 seconds

#         while retry_count < max_retries:
#             try:
#                 response = client.chat.completions.create(
#                     model=AZURE_OAI_MODEL,
#                     messages=[{"role": "system", "content": "You are an AI that generates structured test data."},
#                                 {"role": "user", "content": prompt}],
#                     temperature=0.7,
#                     response_format={"type": "json_object"},
#                     timeout=600
#                 )

#                 response_text = response.choices[0].message.content
#                 generated_data = json.loads(response_text)
#                 new_records = generated_data[table_name]  # Extract the batch of records

#                 # Add the new batch of records to all generated data
#                 all_generated_data.extend(new_records)
#                 previous_generated_data.extend(new_records)  # Add to the previous batch data for next iteration

#                 # Ensure we only generate the desired number of records
#                 if len(all_generated_data) >= total_records:
#                     break

#                 # If successful, break out of the retry loop
#                 break
                
#             except Exception as e:
#                 retry_count += 1
#                 print(f"Rate limit error encountered. Retrying in {backoff_time} seconds...")
#                 time.sleep(backoff_time)
#                 backoff_time *= 2  # Exponential backoff

#         if retry_count == max_retries:
#             print(f"Failed to generate data for {table_name} after {max_retries} retries due to rate limit.")
#             return None

#         time.sleep(300)  # Original sleep time
#         print('sleep for 300 seconds')
#     # Return the final generated data
#     return {table_name: all_generated_data}

# # Main logic to process each table one by one
# detected_relationships = infer_relationships(tables)

# print(tables.keys(), '===========')

# for file_name, df in tables.items():
#     if file_name not in ['8-billing.servicerequestdetails.csv','2-registration.patient.csv']:
#         continue
#     print(f"Generating test data for {file_name}...")

#     # Generate data for each table in batches of 10, totaling 100 records
#     generated_data = generate_data_for_table(file_name, df, detected_relationships)

#     if generated_data:
#         # print('=======================================')
#         # print(generated_data)
#         # print('=======================================')
#         # Convert JSON response to DataFrame and save as a CSV file
#         output_path = os.path.join(output_dir, file_name)
#         print(f"Saving generated data for {file_name} to {output_path}...")
#         generated_df = pd.DataFrame(generated_data[file_name])
#         generated_df.to_csv(output_path, index=False)
#     else:
#         print(f"Failed to generate data for {file_name}. Moving to next table.")

# print(f"Test data generation complete. Output saved in '{output_dir}' folder.")















# import os
# import json
# import pandas as pd
# import openai
# import time
# # import uuid

# # Azure OpenAI Configuration
# AZURE_OAI_KEY = "EzqbdX8l2m0PzedkWSxkjESB5wGGDseac0Aq8SmfthOIqZ6jweNQJQQJ99BCACYeBjFXJ3w3AAABACOG5ZKu"
# AZURE_OAI_MODEL = "gpt-4o"
# AZURE_OPENAI_ENDPOINT = "https://qmig-open-ai.openai.azure.com/"
# AZURE_OPENAI_VERSION = "2023-08-01-preview"

# # Initialize OpenAI client
# client = openai.AzureOpenAI(
#     api_key=AZURE_OAI_KEY,
#     api_version=AZURE_OPENAI_VERSION,
#     azure_endpoint=AZURE_OPENAI_ENDPOINT,
# )

# # Define file paths
# files = 'C:/QProjects/TestData_AI/Input_Files'
# input_files = [file for file in os.listdir(files)]
# output_dir = "generated_test_data_w"
# os.makedirs(output_dir, exist_ok=True)

# # Read all tables into DataFrames
# tables = {file.lower(): pd.read_csv(files + '/' + file) for file in input_files}

# # Function to infer primary and foreign key relationships
# def infer_relationships(tables):
#     relationships = []
#     primary_keys = {}

#     # Identify primary keys (columns with unique values)
#     for table_name, df in tables.items():
#         for col in df.columns:
#             if df[col].nunique() == len(df):  # Column has unique values
#                 primary_keys[(table_name, col)] = df[col].tolist()

#     # Identify foreign keys (columns matching primary keys in other tables)
#     for table_name, df in tables.items():
#         for col in df.columns:
#             for (pk_table, pk_col), pk_values in primary_keys.items():
#                 if col != pk_col and df[col].isin(pk_values).sum() > len(df) * 0.8:  # 80% match
#                     relationships.append({
#                         "table": table_name,
#                         "column": col,
#                         "references": pk_table,
#                         "referenced_column": pk_col
#                     })

#     return relationships

# # Function to generate data for a single table in batches, using all previous data (with session context)
# def generate_data_for_table_with_context(table_name, table_df, detected_relationships, records_per_batch=10, total_records=100):
#     all_generated_data = []  # List to store all generated data
    
#     # Generate a new session ID for maintaining conversational history
#     # session_id = str(uuid.uuid4())  # Generate a unique session ID
#     conversation_history = [{"role": "system", "content": "You are an AI that generates structured test data."}]
    
#     # Add the table structure, relationships, and task instructions to the context
#     conversation_history.append({
#         "role": "user", 
#         "content": f"""
#         I have a related SQL table '{table_name}' stored in an Excel file. The table has the following structure and inferred relationships.

#         Detected Relationships:
#         {json.dumps(detected_relationships, indent=2)}

#         Table Structure & Data Patterns:
#         {{ "file_name": "{table_name}", "schema": {{
#             "columns": {json.dumps(list(table_df.columns))},
#             "sample_data": {json.dumps(table_df.head(5).to_dict(orient="records"))},
#             "column_distributions": {json.dumps({col: table_df[col].value_counts(normalize=True).to_dict() for col in table_df.columns})}
#         }} }}

#         **Task:** Generate {records_per_batch} unique test records for the table while preserving the same format as the input file.
#         - Keep the same column names and data types.
#         - Maintain primary key uniqueness and foreign key relationships.
#         - Distribute values similarly to the original dataset but ensure that the generated values do not match any existing values in the input files.
#         - Ensure the generated data is different from all previously generated data.
#         - Return the output as a complete and valid JSON object with this structure: {{ {table_name}: [{{column1: value, column2: value, ...}}] }}. Ensure the response is properly closed and contains all necessary brackets and commas.
#         """
#     })
    
#     num_batches = total_records // records_per_batch
#     print(num_batches, 'Num of Batches')
#     for batch_num in range(num_batches):   
#         print(batch_num, ' Batch Num')     
#         max_retries = 5
#         retry_count = 0
#         backoff_time = 60  # Start with 60 seconds

#         while retry_count < max_retries:
#             try:
#                 # Make the request to the OpenAI API with the session_id to maintain context
#                 response = client.chat.completions.create(
#                     model=AZURE_OAI_MODEL,
#                     # session_id=session_id,  # Maintain session context
#                     messages=conversation_history,  # Maintain conversation history
#                     temperature=0.7,
#                     response_format={"type": "json_object"},
#                     timeout=600
#                 )

#                 # Parse the response
#                 response_text = response.choices[0].message.content
#                 generated_data = json.loads(response_text)
#                 new_records = generated_data[table_name]  # Extract the batch of records
#                 print(len(new_records), f'Length of Records for Batch {batch_num}')

#                 # Add the new batch of records to all generated data
#                 all_generated_data.extend(new_records)
                
#                 # Append the model's response to conversation history
#                 conversation_history.append({
#                     "role": "assistant",
#                     "content": response_text
#                 })

#                 # If successful, break out of the retry loop
#                 break

#             except Exception as e:
#                 print(e)
#                 retry_count += 1
#                 print(f"Rate limit error encountered. Retrying in {backoff_time} seconds...")
#                 time.sleep(backoff_time)
#                 backoff_time *= 2  # Exponential backoff

#         if retry_count == max_retries:
#             print(f"Failed to generate data for {table_name} after {max_retries} retries due to rate limit.")
#             return None

#     # Return the final generated data
#     return {table_name: all_generated_data}

# # Main logic to process each table one by one
# detected_relationships = infer_relationships(tables)

# print(tables.keys(), '===========')

# for file_name, df in tables.items():
#     if file_name not in ['2-registration.patient.csv']:
#         continue
#     print(f"Generating test data for {file_name}...")

#     # Generate data for each table in batches of 10, totaling 100 records
#     generated_data = generate_data_for_table_with_context(file_name, df, detected_relationships)

#     if generated_data:
#         # Convert JSON response to DataFrame and save as a CSV file
#         output_path = os.path.join(output_dir, file_name)
#         print(f"Saving generated data for {file_name} to {output_path}...")
#         generated_df = pd.DataFrame(generated_data[file_name])
#         generated_df.to_csv(output_path, index=False)
#     else:
#         print(f"Failed to generate data for {file_name}. Moving to next table.")

# print(f"Test data generation complete. Output saved in '{output_dir}' folder.")

























# import os
# import json
# import pandas as pd
# import openai
# import time
# # import uuid

# # Azure OpenAI Configuration
# AZURE_OAI_KEY = "EzqbdX8l2m0PzedkWSxkjESB5wGGDseac0Aq8SmfthOIqZ6jweNQJQQJ99BCACYeBjFXJ3w3AAABACOG5ZKu"
# AZURE_OAI_MODEL = "gpt-4o"
# AZURE_OPENAI_ENDPOINT = "https://qmig-open-ai.openai.azure.com/"
# AZURE_OPENAI_VERSION = "2023-08-01-preview"


# # Initialize OpenAI client
# client = openai.AzureOpenAI(
#     api_key=AZURE_OAI_KEY,
#     api_version=AZURE_OPENAI_VERSION,
#     azure_endpoint=AZURE_OPENAI_ENDPOINT,
# )

# # Define file paths
# files = 'C:/QProjects/TestData_AI/Input_Files'
# input_files = [file for file in os.listdir(files)]
# output_dir = "generated_test_data_w"
# os.makedirs(output_dir, exist_ok=True)

# # Read all tables into DataFrames
# tables = {file.lower(): pd.read_csv(files + '/' + file) for file in input_files}

# # Function to infer primary and foreign key relationships
# def infer_relationships(tables):
#     relationships = []
#     primary_keys = {}

#     # Identify primary keys (columns with unique values)
#     for table_name, df in tables.items():
#         for col in df.columns:
#             if df[col].nunique() == len(df):  # Column has unique values
#                 primary_keys[(table_name, col)] = df[col].tolist()

#     # Identify foreign keys (columns matching primary keys in other tables)
#     for table_name, df in tables.items():
#         for col in df.columns:
#             for (pk_table, pk_col), pk_values in primary_keys.items():
#                 if col != pk_col and df[col].isin(pk_values).sum() > len(df) * 0.8:  # 80% match
#                     relationships.append({
#                         "table": table_name,
#                         "column": col,
#                         "references": pk_table,
#                         "referenced_column": pk_col
#                     })

#     return relationships

# # Function to generate data for a single table in batches, using all previous data (with session context)
# def generate_data_for_table_with_context(table_name, table_df, detected_relationships, conversation_history, records_per_batch=6, total_records=100):
#     all_generated_data = []  # List to store all generated data
    
    
#     num_batches = total_records // records_per_batch
#     print(num_batches, "num batches")
#     for batch_num in range(num_batches):
#         batch_num = batch_num + 1
#         print(batch_num, ' Batch')
#         max_retries = 5
#         retry_count = 0
#         backoff_time = 60  # Start with 60 seconds
#         # Add the table structure, relationships, and task instructions to the context
#         conversation_history.append({
#             "role": "user", 
#             "content": f"""
#             I have a related SQL table '{table_name}' stored in an Excel file. The table has the following structure and inferred relationships.

#             Detected Relationships:
#             {json.dumps(detected_relationships, indent=2)}

#             Table Structure & Data Patterns:
#             {{ "file_name": "{table_name}", "schema": {{
#                 "columns": {json.dumps(list(table_df.columns))},
#                 "sample_data": {json.dumps(table_df.head(5).to_dict(orient="records"))},
#                 "column_distributions": {json.dumps({col: table_df[col].value_counts(normalize=True).to_dict() for col in table_df.columns})}
#             }} }}

#             **Task:** Generate {records_per_batch} unique test records for the table while preserving the same format as the input file.
#             - Keep the same column names and data types.
#             - Maintain primary key uniqueness and foreign key relationships.
#             - Distribute values similarly to the original dataset but ensure that the generated values do not match any existing values in the input files.
#             - Ensure the generated data is different from all previously generated data.
#             - The output must contain exactly **{records_per_batch} records**, no more and no less.
#             - Return the output as a complete and valid JSON object with this structure: {{ {table_name}: [{{column1: value, column2: value, ...}}] }}. Ensure the response is properly closed and contains all necessary brackets and commas.
#             """
#         })
#         while retry_count < max_retries :
#             print(retry_count, "retry count")
#             try:
#                 # Make the request to the OpenAI API with the session_id to maintain context
#                 response = client.chat.completions.create(
#                     model=AZURE_OAI_MODEL,
#                     messages=conversation_history,  # Maintain conversation history
#                     temperature=0.7,
#                     response_format={"type": "json_object"},
#                     timeout=600
#                 )

#                 # Parse the response
#                 response_text = response.choices[0].message.content
#                 # print('===============================================')
#                 # print(response_text)
#                 # print('===============================================')

#                 generated_data = json.loads(response_text)
                
#                 new_records = generated_data[table_name]  # Extract the batch of records
#                 print(len(new_records), f'Length of Records for Batch {batch_num}')
#                 # Add the new batch of records to all generated data
#                 all_generated_data.extend(new_records)
                
#                 # Append the model's response to conversation history
#                 conversation_history.append({
#                     "role": "assistant",
#                     "content": response_text
#                 })

#                 # If successful, break out of the retry loop
#                 break

#             except Exception as e:
#                 print("error:", e)
#                 retry_count += 1
#                 time.sleep(backoff_time)
#                 backoff_time *= 2  # Exponential backoff

#         if retry_count == max_retries:
#             print(f"Failed to generate data for {table_name} after {max_retries} retries due to rate limit.")
#             return None

#     # Return the final generated data
#     return {table_name: all_generated_data}

# # Main logic to process each table one by one
# detected_relationships = infer_relationships(tables)



# for file_name, df in tables.items():
#     if file_name not in ['2-registration.patient.csv']:
#         continue
#     print(f"Generating test data for {file_name}...")
#     # Initialize conversation history once for the entire generation process
#     conversation_history = [{"role": "system", "content": "You are an AI that generates structured test data."}]

#     # Generate data for each table in batches of 10, totaling 100 records
#     generated_data = generate_data_for_table_with_context(file_name, df, detected_relationships, conversation_history)

#     if generated_data:
#         # Convert JSON response to DataFrame and save as a CSV file
#         output_path = os.path.join(output_dir, file_name)
#         generated_df = pd.DataFrame(generated_data[file_name])
#         generated_df.to_csv(output_path, index=False)
#     else:
#         print(f"Failed to generate data for {file_name}. Moving to next table.")

# print(f"Test data generation complete. Output saved in '{output_dir}' folder.")


















import os, re, json, pandas as pd, openai, time
# Azure OpenAI Configuration
AZURE_OAI_KEY = "AYxiyqI41yG0k6Yh6eFJNNBg2yy8iSwnAgSd4beaFT3qMyTJjWmrJQQJ99ALACYeBjFXJ3w3AAABACOGHzA8"
AZURE_OAI_MODEL = "gpt-4o"
AZURE_OPENAI_ENDPOINT = "https://az-pii.openai.azure.com/"
AZURE_OPENAI_VERSION = "2023-08-01-preview"


# Initialize OpenAI client
client = openai.AzureOpenAI(
    api_key=AZURE_OAI_KEY,
    api_version=AZURE_OPENAI_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)


# Define file paths
files = 'C:/QProjects/TestData_AI/Input_Files'
input_files = [file for file in os.listdir(files)]
output_dir = "generated_test_data_w"
os.makedirs(output_dir, exist_ok=True)

# Read all tables into DataFrames
tables = {file.lower(): pd.read_csv(files + '/' + file) for file in input_files}

# Function to infer primary and foreign key relationships
def infer_relationships(tables):
    relationships = []
    primary_keys = {}

    # Identify primary keys (columns with unique values)
    for table_name, df in tables.items():
        for col in df.columns:
            if df[col].nunique() == len(df):  # Column has unique values
                primary_keys[(table_name, col)] = df[col].tolist()

    # Identify foreign keys (columns matching primary keys in other tables)
    for table_name, df in tables.items():
        for col in df.columns:
            for (pk_table, pk_col), pk_values in primary_keys.items():
                if col != pk_col and df[col].isin(pk_values).sum() > len(df) * 0.8:  # 80% match
                    relationships.append({
                        "table": table_name,
                        "column": col,
                        "references": pk_table,
                        "referenced_column": pk_col
                    })

    return relationships

# Function to generate data for a single table in batches, using all previous data
def generate_data_for_table(table_name, table_df, detected_relationships, records_per_batch=2, total_records=100):
    all_generated_data = []  # List to store all generated data
 
    # Number of batches we need
    num_batches = total_records // records_per_batch
    print('num_batches:', num_batches)
    for batch_num in range(num_batches):
        print('batch_num:', batch_num)

        prompt = f"""
        I have a related SQL table '{table_name}' stored in an Excel file. The table has the following structure and inferred relationships.

        Detected Relationships:
        {json.dumps(detected_relationships, indent=2)}

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
        - Ensure the generated data is different from all previously generated data
        - Return the output as a complete and valid JSON object with this structure: {{ {table_name}: [{{column1: value, column2: value, ...}}] }}. Ensure the response is properly closed and contains all necessary brackets and commas.
        """
        
        
        max_retries = 5
        retry_count = 0
        backoff_time = 60  # Start with 60 seconds

        while retry_count < max_retries:
            try:
                response = client.chat.completions.create(
                    model=AZURE_OAI_MODEL,
                    messages=[{"role": "system", "content": "You are an AI that generates structured test data."},
                                {"role": "user", "content": prompt}],
                    temperature=0.7,
                    response_format={"type": "json_object"},
                    timeout=600
                )

                response_text = response.choices[0].message.content
                generated_data = json.loads(response_text)
                new_records = generated_data[table_name]  # Extract the batch of records

                # Add the new batch of records to all generated data
                all_generated_data.extend(new_records)

                # Ensure we only generate the desired number of records
                if len(all_generated_data) >= total_records:
                    break

                # If successful, break out of the retry loop
                break
                
            except Exception as e:
                retry_count += 1
                print(f"Rate limit error encountered. Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff

        if retry_count == max_retries:
            print(f"Failed to generate data for {table_name} after {max_retries} retries due to rate limit.")
            return None

        time.sleep(300)  # Original sleep time
        print('sleep for 300 seconds')
    # Return the final generated data
    return {table_name: all_generated_data}

# Main logic to process each table one by one
detected_relationships = infer_relationships(tables)

print(tables.keys(), '===========')

for file_name, df in tables.items():
    if file_name not in ['8-billing.servicerequestdetails.csv','2-registration.patient.csv']:
        continue
    print(f"Generating test data for {file_name}...")

    # Generate data for each table in batches of 10, totaling 100 records
    generated_data = generate_data_for_table(file_name, df, detected_relationships)

    if generated_data:
        # print('=======================================')
        # print(generated_data)
        # print('=======================================')
        # Convert JSON response to DataFrame and save as a CSV file
        output_path = os.path.join(output_dir, file_name)
        print(f"Saving generated data for {file_name} to {output_path}...")
        generated_df = pd.DataFrame(generated_data[file_name])
        generated_df.to_csv(output_path, index=False)
    else:
        print(f"Failed to generate data for {file_name}. Moving to next table.")

print(f"Test data generation complete. Output saved in '{output_dir}' folder.")
