import os, re, json, pandas as pd, openai

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



# files = 'C:/QProjects/TestData_AI/Input_Files'
# # Define input Excel file paths
# input_files = [file for file in os.listdir(files) ]
# # Create output directory
# output_dir = "generated_test_data"
# os.makedirs(output_dir, exist_ok=True)

# # Read all tables into DataFrames
# tables = {file: pd.read_csv(files+'/'+file) for file in input_files}

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

# # Infer relationships
# detected_relationships = infer_relationships(tables)

# # Analyze tables (columns, sample data, distributions)
# table_analysis = []
# for file_name, df in tables.items():
#     schema = {
#         "columns": list(df.columns),
#         "sample_data": df.head(5).to_dict(orient="records"),
#         "column_distributions": {col: df[col].value_counts(normalize=True).to_dict() for col in df.columns}
#     }
#     table_analysis.append({"file_name": file_name, "schema": schema})

# # Create the OpenAI prompt
# prompt = f"""
# I have few related SQL tables stored in Excel files. Each table has a specific structure and inferred relationships.

# Detected Relationships:
# {json.dumps(detected_relationships, indent=2)}

# Table Structures & Data Patterns:
# {json.dumps(table_analysis, indent=2)}

# **Task:** Generate 20 unique test records per table while preserving the same format as the input files.
# - Keep the same column names and data types.
# - Maintain primary key uniqueness and foreign key relationships.
# - Distribute values similarly to the original dataset but ensure that the generated values do not match any existing values in the input files.
# - Return the output as a complete and valid JSON object with this structure: {{ "file_name": [{{column1: value, column2: value, ...}}] }}. Ensure the response is properly closed and contains all necessary brackets and commas.
# """

# response = client.chat.completions.create(
#             model=AZURE_OAI_MODEL,
#     messages=[{"role": "system", "content": "You are an AI that generates structured test data."},
#               {"role": "user", "content": prompt}],
#     temperature=0.7,
#     response_format={"type": "json_object"}
#         )

# print('==================================================')
# print(response.choices[0].message.content)
# print('================================================')

# try:
#     generated_data = json.loads(response.choices[0].message.content)
#     print('Successfully parsed the generated data:')
#     print(generated_data)
# except json.JSONDecodeError as e:
#     print(f"JSON decode error: {e}")
#     print("Raw response:", response.choices[0].message.content)
    
# # Convert JSON response to DataFrames and save each as a separate Excel file
# for file_name, records in generated_data.items():
#     print(file_name, ' filename')
#     df = pd.DataFrame(records)
#     output_path = os.path.join(output_dir, file_name)
#     print(output_path, ' Path')
#     df.to_csv(output_path, index=False)

# print(f"Test data generation complete. Output saved in '{output_dir}' folder.")















# # Define file paths
# files = 'C:/QProjects/TestData_AI/Input_Files'
# input_files = [file for file in os.listdir(files)]
# output_dir = "generated_test_data"
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

# # Function to generate test data for a single table
# def generate_data_for_table(table_name, table_df, detected_relationships):
#     prompt = f"""
#     I have a related SQL table '{table_name}' stored in an Excel file. The table has the following structure and inferred relationships.

#     Detected Relationships:
#     {json.dumps(detected_relationships, indent=2)}

#     Table Structure & Data Patterns:
#     {{ "file_name": "{table_name}", "schema": {{
#         "columns": {json.dumps(list(table_df.columns))},
#         "sample_data": {json.dumps(table_df.head(5).to_dict(orient="records"))},
#         "column_distributions": {json.dumps({col: table_df[col].value_counts(normalize=True).to_dict() for col in table_df.columns})}
#     }} }}

#     **Task:** Generate 20 unique test records for the table while preserving the same format as the input file.
#     - Keep the same column names and data types.
#     - Maintain primary key uniqueness and foreign key relationships.
#     - Distribute values similarly to the original dataset but ensure that the generated values do not match any existing values in the input files.
#     - Return the output as a complete and valid JSON object with this structure: {{ {table_name}: [{{column1: value, column2: value, ...}}] }}. Ensure the response is properly closed and contains all necessary brackets and commas.
#     """

#     # Send the prompt to OpenAI API
#     try:
#         response = client.chat.completions.create(
#             model=AZURE_OAI_MODEL,
#             messages=[{"role": "system", "content": "You are an AI that generates structured test data."},
#                       {"role": "user", "content": prompt}],
#             temperature=0.7,
#             response_format={"type": "json_object"},
#             timeout=600
#         )

#         response_text = response.choices[0].message.content
#         # Parse the response
#         try:
#             generated_data = json.loads(response_text)
#             return generated_data
#         except json.JSONDecodeError as e:
#             print(f"JSON decode error for {table_name}: {e}")
#             return None

#     except Exception as e:
#         print(f"Error generating data for {table_name}: {e}")
#         return None

# # Main logic to process each table one by one
# detected_relationships = infer_relationships(tables)

# print(tables.keys(), '===========')
# for file_name, df in tables.items():
#     print(f"Generating test data for {file_name}...")
    
#     generated_data = generate_data_for_table(file_name, df, detected_relationships)
    
#     if generated_data:
#         print('=======================================')
#         print(generated_data)
#         print('=======================================')
#         # Convert JSON response to DataFrame and save as a CSV file
#         output_path = os.path.join(output_dir, file_name)
#         print(f"Saving generated data for {file_name} to {output_path}...")
#         generated_df = pd.DataFrame(generated_data[file_name])
#         generated_df.to_csv(output_path, index=False)
#     else:
#         print(f"Failed to generate data for {file_name}. Moving to next table.")
    
# print(f"Test data generation complete. Output saved in '{output_dir}' folder.")

























# # Define file paths
# files = 'C:/QProjects/TestData_AI/Input_Files'
# input_files = [file for file in os.listdir(files)]
# output_dir = "generated_test_data"
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

# # Function to generate data for a single table in batches of 10 records
# def generate_data_for_table(table_name, table_df, detected_relationships, records_per_batch=10, total_records=100):
#     all_generated_data = []
    
#     # Determine how many batches we need
#     num_batches = total_records // records_per_batch
#     print("Number of Batches ", num_batches)
#     for batch_num in range(num_batches):
#         print("Generating Test Data for Batch Data ", batch_num)
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
#         - Return the output as a complete and valid JSON object with this structure: {{ {table_name}: [{{column1: value, column2: value, ...}}] }}. Ensure the response is properly closed and contains all necessary brackets and commas.
#         """
        
#         # Send the prompt to OpenAI API
#         try:
#             response = client.chat.completions.create(
#                 model=AZURE_OAI_MODEL,
#                 messages=[{"role": "system", "content": "You are an AI that generates structured test data."},
#                           {"role": "user", "content": prompt}],
#                 temperature=0.7,
#                 response_format={"type": "json_object"},
#                 timeout=600
#             )

#             response_text = response.choices[0].message.content
#             # Parse the response
#             try:
#                 generated_data = json.loads(response_text)
#                 all_generated_data.append(generated_data[table_name])  # Append the batch
#             except json.JSONDecodeError as e:
#                 print(f"JSON decode error for {table_name}: {e}")
#                 return None

#         except Exception as e:
#             print(f"Error generating data for {table_name} (batch {batch_num+1}): {e}")
#             return None

#     # Combine all batches into a single list and return
#     return {table_name: [record for batch in all_generated_data for record in batch]}

# # Main logic to process each table one by one
# detected_relationships = infer_relationships(tables)

# print(tables.keys(), '===========')
# for file_name, df in tables.items():
#     print(f"Generating test data for {file_name}...")
#     print('Length of df shape', df.shape)

#     # Generate data for each table in batches of 10, totaling 100 records
#     generated_data = generate_data_for_table(file_name, df, detected_relationships)

#     if generated_data:
#         # Convert JSON response to DataFrame and save as a CSV file
#         output_path = os.path.join(output_dir, file_name)
#         print(f"Saving generated data for {file_name} to {output_path}...")
#         generated_df = pd.DataFrame(generated_data[file_name])
#         generated_df.to_csv(output_path, index=False)
#     else:
#         print(f"Failed to generate data for {file_name}. Moving to next table.")

# print(f"Test data generation complete. Output saved in '{output_dir}' folder.")



















# # Define file paths
# files = 'C:/QProjects/TestData_AI/Input_Files'
# input_files = [file for file in os.listdir(files)]
# output_dir = "generated_test_data"
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
# def generate_data_for_table(table_name, table_df, detected_relationships, records_per_batch=10, total_records=100):
#     all_generated_data = []  # List to store all generated data
#     previous_generated_data = []  # Keep track of all previous batches' records
    
#     # Number of batches we need
#     num_batches = total_records // records_per_batch
    
#     for batch_num in range(num_batches):
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
        
#         # Send the prompt to OpenAI API
#         try:
#             response = client.chat.completions.create(
#                 model=AZURE_OAI_MODEL,
#                 messages=[{"role": "system", "content": "You are an AI that generates structured test data."},
#                           {"role": "user", "content": prompt}],
#                 temperature=0.7,
#                 response_format={"type": "json_object"},
#                 timeout=600
#             )

#             response_text = response.choices[0].message.content
#             # Parse the response
#             try:
#                 generated_data = json.loads(response_text)
#                 new_records = generated_data[table_name]  # Extract the batch of records

#                 # Add the new batch of records to all generated data
#                 all_generated_data.extend(new_records)
#                 previous_generated_data.extend(new_records)  # Add to the previous batch data for next iteration

#                 # Ensure we only generate the desired number of records
#                 if len(all_generated_data) >= total_records:
#                     break

#             except json.JSONDecodeError as e:
#                 print(f"JSON decode error for {table_name}: {e}")
#                 return None

#         except Exception as e:
#             print(f"Error generating data for {table_name} (batch {batch_num+1}): {e}")
#             return None

#     # Return the final generated data
#     return {table_name: all_generated_data}

# # Main logic to process each table one by one
# detected_relationships = infer_relationships(tables)

# print(tables.keys(), '===========')
# for file_name, df in tables.items():
#     print(f"Generating test data for {file_name}...")

#     # Generate data for each table in batches of 10, totaling 100 records
#     generated_data = generate_data_for_table(file_name, df, detected_relationships)

#     if generated_data:
#         print('=======================================')
#         print(generated_data)
#         print('=======================================')
#         # Convert JSON response to DataFrame and save as a CSV file
#         output_path = os.path.join(output_dir, file_name)
#         print(f"Saving generated data for {file_name} to {output_path}...")
#         generated_df = pd.DataFrame(generated_data[file_name])
#         generated_df.to_csv(output_path, index=False)
#     else:
#         print(f"Failed to generate data for {file_name}. Moving to next table.")

# print(f"Test data generation complete. Output saved in '{output_dir}' folder.")

























# Define file paths
files = 'C:/QProjects/TestData_AI/Input_Files'
input_files = [file for file in os.listdir(files)]
output_dir = "generated_test_data"
os.makedirs(output_dir, exist_ok=True)

# Read all tables into DataFrames
tables = {file.lower(): pd.read_csv(files + '/' + file) for file in input_files}

# Function to parse DDLs and extract primary and foreign key relationships
def parse_ddl(ddl):
    primary_keys = {}
    foreign_keys = []
    
    # Regex to find primary keys
    pk_pattern = re.compile(r"PRIMARY\s+KEY\s*\((\w+)\)", re.IGNORECASE)
    pk_matches = pk_pattern.findall(ddl)
    for pk in pk_matches:
        primary_keys[pk] = pk
    
    # Regex to find foreign keys
    fk_pattern = re.compile(r"FOREIGN\s+KEY\s*\((\w+)\)\s+REFERENCES\s+(\w+)\s*\((\w+)\)", re.IGNORECASE)
    fk_matches = fk_pattern.findall(ddl)
    for fk in fk_matches:
        foreign_keys.append({
            "column": fk[0],
            "references": fk[1],
            "referenced_column": fk[2]
        })
    
    return primary_keys, foreign_keys

# Function to generate data for a single table in batches, using all previous data
def generate_data_for_table_with_ddl(table_name, table_df, ddl, records_per_batch=10, total_records=100):
    all_generated_data = []  # List to store all generated data
    previous_generated_data = []  # Keep track of all previous batches' records
    
    # Parse DDL for primary and foreign key relationships
    primary_keys, foreign_keys = parse_ddl(ddl)
    
    # Number of batches we need
    num_batches = total_records // records_per_batch
    
    for batch_num in range(num_batches):
        # Convert all previous generated data into a format that can be passed in the prompt
        previous_data = json.dumps(previous_generated_data)  # We limit the previous data context to 5 records

        prompt = f"""
        I have a related SQL table '{table_name}' stored in an Excel file. The table has the following structure and inferred relationships.
        
        Table DDL:
        {ddl}  # Pass the DDL statement here to define the table structure, types, and constraints
        
        Primary Keys:
        {json.dumps(primary_keys, indent=2)}

        Foreign Keys:
        {json.dumps(foreign_keys, indent=2)}

        Table Structure & Data Patterns:
        {{ "file_name": "{table_name}", "schema": {{
            "columns": {json.dumps(list(table_df.columns))},
            "sample_data": {json.dumps(table_df.head(5).to_dict(orient="records"))},
            "column_distributions": {json.dumps({col: table_df[col].value_counts(normalize=True).to_dict() for col in table_df.columns})}
        }} }}

        **Task:** Generate {records_per_batch} unique test records for the table while preserving the same format as the input file.
        - Keep the same column names and data types as specified in the DDL.
        - Maintain primary key uniqueness and foreign key relationships.
        - Distribute values similarly to the original dataset but ensure that the generated values do not match any existing values in the input files.
        - Ensure the generated data is different from all previously generated data: {previous_data}
        - Return the output as a complete and valid JSON object with this structure: {{ {table_name}: [{{column1: value, column2: value, ...}}] }}. Ensure the response is properly closed and contains all necessary brackets and commas.
        """
        
        # Send the prompt to OpenAI API
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
            # Parse the response
            try:
                generated_data = json.loads(response_text)
                new_records = generated_data[table_name]  # Extract the batch of records

                # Add the new batch of records to all generated data
                all_generated_data.extend(new_records)
                previous_generated_data.extend(new_records)  # Add to the previous batch data for next iteration

                # Ensure we only generate the desired number of records
                if len(all_generated_data) >= total_records:
                    break

            except json.JSONDecodeError as e:
                print(f"JSON decode error for {table_name}: {e}")
                return None

        except Exception as e:
            print(f"Error generating data for {table_name} (batch {batch_num+1}): {e}")
            return None

    # Return the final generated data
    return {table_name: all_generated_data}

# DDLs for each table (ensure you fill these DDLs as per your actual schema)
ddls = {
    "table1": """
        CREATE TABLE table1 (
            id INT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            age INT,
            country_id INT,
            FOREIGN KEY (country_id) REFERENCES countries(id)
        );
    """,
    "table2": """
        CREATE TABLE table2 (
            id INT PRIMARY KEY,
            country_name VARCHAR(255),
            continent VARCHAR(255)
        );
    """
    # Add other tables' DDLs as necessary
}

print(tables.keys(), '===========')
fghj
# Main logic to process each table one by one
for file_name, df in tables.items():
    print(f"Generating test data for {file_name}...")

    # Retrieve the corresponding DDL for the table
    table_ddl = ddls.get(file_name.lower(), "")

    # Generate data for each table in batches of 10, totaling 100 records
    generated_data = generate_data_for_table_with_ddl(file_name, df, table_ddl)

    if generated_data:
        print('=======================================')
        print(generated_data)
        print('=======================================')
        # Convert JSON response to DataFrame and save as a CSV file
        output_path = os.path.join(output_dir, file_name)
        print(f"Saving generated data for {file_name} to {output_path}...")
        generated_df = pd.DataFrame(generated_data[file_name])
        generated_df.to_csv(output_path, index=False)
    else:
        print(f"Failed to generate data for {file_name}. Moving to next table.")

print(f"Test data generation complete. Output saved in '{output_dir}' folder.")
