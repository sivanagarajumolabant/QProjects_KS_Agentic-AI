import os, re, json, pandas as pd, openai, random
# Azure OpenAI Configuration
AZURE_OAI_KEY = "EzqbdX8l2m0PzedkWSxkjESB5wGGDseac0Aq8SmfthOIqZ6jweNQJQQJ99BCACYeBjFXJ3w3AAABACOG5ZKu"
AZURE_OAI_MODEL = "gpt-4o"
AZURE_OPENAI_ENDPOINT = "https://qmig-open-ai.openai.azure.com/"
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



















# Define file paths
files = 'C:/QProjects/TestData_AI/New_data'
input_files = [file for file in os.listdir(files)]
output_dir = "generated_test_data_new_data"
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
def generate_data_for_table(all_generated_data, previous_generated_data, table_name, table_df, detected_relationships, records_per_batch=5, total_records=20):
    
    # Number of batches we need
    num_batches = total_records // records_per_batch
    print('num_batches:', num_batches)
    for batch_num in range(num_batches):
        print('batch_num:', batch_num)
        # Convert all previous generated data into a format that can be passed in the prompt
        previous_data = json.dumps(previous_generated_data[-5:])  # We limit the previous data context to 5 records
        # previous_data = json.dumps(previous_generated_data)  # We limit the previous data context to 5 records

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
                print(len(new_records), ' Length of Batch Records')
                # Add the new batch of records to all generated data
                all_generated_data.extend(new_records)
                previous_generated_data.extend(new_records)  # Add to the previous batch data for next iteration

                # Ensure we only generate the desired number of records
                if len(all_generated_data) >= total_records:
                    break

            except json.JSONDecodeError as e:
                print(f"JSON decode error for {table_name}: {e}")
                continue

        except Exception as e:
            print(f"Error generating data for {table_name} (batch {batch_num+1}): {e}")
            return None
    if len(all_generated_data) < total_records:
        print('Attempted to generate less records than requested')
        generated_data = generate_data_for_table(all_generated_data, previous_generated_data,table_name, table_df, detected_relationships)
    # Return the final generated data
    return {table_name: all_generated_data}

# Main logic to process each table one by one
detected_relationships = infer_relationships(tables)

print(tables.keys(), '===========')
for file_name, df in tables.items():
    # if file_name not in ['1-registration.registrationmaster.csv']:
    #     continue
    print(f"Generating test data for {file_name}...")
    all_generated_data = []  # List to store all generated data
    previous_generated_data = []  # Keep track of all previous batches' records
    # Generate data for each table in batches of 10, totaling 100 records
    generated_data = generate_data_for_table(all_generated_data, previous_generated_data,file_name, df, detected_relationships)

    if generated_data:
        generated_data = generated_data[:101] if len(generated_data)>100 else generated_data
        output_path = os.path.join(output_dir, file_name)
        print(f"Saving generated data for {file_name} to {output_path}...")
        generated_df = pd.DataFrame(generated_data[file_name])
        generated_df.to_csv(output_path, index=False)
    else:
        print(f"Failed to generate data for {file_name}. Moving to next table.")

print(f"Test data generation complete. Output saved in '{output_dir}' folder.")






















# # DDLs for each table (ensure you fill these DDLs as per your actual schema)
# ddls = {
#     "registration.registrationmaster": """
#         CREATE TABLE registration.registrationmaster (
#         registrationid numeric(19) NOT NULL,
#         registrationtype numeric(10) NOT NULL,
#         registrationsource varchar(100) NULL,
#         registrationdescription varchar(100) NULL,
#         updateddate timestamp NOT NULL,
#         updatedby varchar(100) NOT NULL,
#         CONSTRAINT pk_registrationmaster PRIMARY KEY (registrationid));
#     """,
#     "registration.patient": """
#         CREATE TABLE registration.patient (
#         registrationid numeric(19) NOT NULL,
#         preregistrationno varchar(50) NULL,
#         emergencyno varchar(100) NULL,
#         uhid varchar(100) NULL,
#         locationid numeric(10) NULL,
#         corporateemployeeid varchar(100) NULL,
#         corporateid numeric(19) NULL,
#         refferaldoctorid numeric(19) NULL,
#         refferalentityid numeric(19) NULL,
#         employeeid varchar(100) NULL,
#         recruitmentid varchar(100) NULL,
#         employeereferralid numeric(10) NULL,
#         relationshipcode numeric(10) NULL,
#         campid varchar(100) NULL,
#         campname varchar(100) NULL,
#         camptype varchar(100) NULL,
#         campregistrationid varchar(100) NULL,
#         batchid varchar(100) NULL,
#         title varchar(200) NULL,
#         firstname varchar(200) NULL,
#         middlename varchar(200) NULL,
#         lastname varchar(200) NULL,
#         sufix varchar(200) NULL,
#         educationalqualification varchar(200) NULL,
#         otherdegree varchar(200) NULL,
#         birthdate timestamp NULL,
#         birthtime timestamp NULL,
#         fathername varchar(200) NULL,
#         spousename varchar(200) NULL,
#         mothermaidenname varchar(200) NULL,
#         gaurdianname varchar(200) NULL,
#         birthplace varchar(200) NULL,
#         approximate numeric(10) NULL,
#         age numeric(10) NULL,
#         agetype numeric(10) NULL,
#         agecategory numeric(10) NULL,
#         gender varchar(200) NULL,
#         maritalstatus varchar(200) NULL,
#         religion varchar(200) NULL,
#         race varchar(200) NULL,
#         ethnicgroup varchar(200) NULL,
#         employmentstatus varchar(200) NULL,
#         monthlyincome numeric(19, 4) NULL,
#         primarylanguage varchar(200) NULL,
#         translatorrequired varchar(200) NULL,
#         translatorname varchar(200) NULL,
#         citizenship varchar(200) NULL,
#         literate varchar(200) NULL,
#         financialstatus varchar(200) NULL,
#         emotionalbarriers varchar(200) NULL,
#         patienttype varchar(200) NULL,
#         disability varchar(200) NULL,
#         disabledpersoncode bpchar(20) NULL,
#         disabledpersonidentifier varchar(100) NULL,
#         identificationmark1 varchar(200) NULL,
#         identificationmark2 varchar(200) NULL,
#         socialsecuritynumber varchar(100) NULL,
#         possesspassport varchar(200) NULL,
#         diabetic numeric(10) NULL,
#         allergic numeric(10) NULL,
#         bloodgroup bpchar(20) NULL,
#         rhfactor varchar(40) NULL,
#         donor numeric(10) NULL,
#         donortype bpchar(20) NULL,
#         organtype bpchar(20) NULL,
#         donorcode bpchar(20) NULL,
#         paymentforregistration numeric(10) NULL,
#         paymentcurrency varchar(100) NULL,
#         paymentmethod varchar(100) NULL,
#         referenceno varchar(200) NULL,
#         createdby varchar(50) NULL,
#         createddate timestamp NULL,
#         howdoyoucometoknowaboutus varchar(200) NULL,
#         preferredmodeofcontact varchar(200) NULL,
#         wantalertsonhospitalpromotions numeric(10) NULL,
#         filetype varchar(100) NULL,
#         status numeric(10) NOT NULL,
#         business varchar(100) NULL,
#         preferredlocation bpchar(40) NULL,
#         privacystatus bpchar(20) NULL,
#         customerstatus varchar(100) NULL,
#         aliasname varchar(100) NULL,
#         startdate timestamp NULL,
#         enddate timestamp NULL,
#         noofissues numeric(10) NULL,
#         updatedby varchar(100) NULL,
#         updateddate timestamp NULL,
#         flexifield1 varchar(100) NULL,
#         flexifield2 varchar(100) NULL,
#         flexifield3 varchar(100) NULL,
#         flexifield4 varchar(100) NULL,
#         filename varchar(200) NULL,
#         filepath varchar(2000) NULL,
#         emailid varchar(200) NULL,
#         cancellationdate timestamp NULL,
#         reasonforcancellation varchar(400) NULL,
#         babyof varchar(200) NULL,
#         reasonforreissue varchar(400) NULL,
#         counterno varchar(100) NULL,
#         shiftno varchar(100) NULL,
#         draft numeric NULL,
#         tempdraftid varchar(100) NULL,
#         ismlccase numeric NULL,
#         mlccaseno varchar(800) NULL,
#         ishypertension numeric NULL,
#         havecommunicabledisease numeric NULL,
#         patientpreference varchar(4000) NULL,
#         foodpreference varchar(4000) NULL,
#         diabetictype varchar(400) NULL,
#         deathdatetime timestamp NULL,
#         employeerelation varchar(200) NULL,
#         eventid varchar(200) NULL,
#         eventname varchar(200) NULL,
#         eventtype varchar(200) NULL,
#         currentstatus numeric(2) DEFAULT 0 NULL,
#         lasttransaction timestamp NULL,
#         reasonforfree varchar(4000) NULL,
#         olduhid varchar(200) NULL,
#         referralpatientuhid varchar(100) NULL,
#         mothersuhid varchar(100) NULL,
#         customerloyaltyno varchar(100) NULL,
#         flag numeric NULL,
#         regularizationcheck numeric(38) NULL,
#         regularizationdate timestamp NULL,
#         secondarylanguage varchar(1000) NULL,
#         bloodgroupflag numeric(1) DEFAULT 0 NULL,
#         baselocation numeric(10) DEFAULT NULL::numeric NULL,
#         transferdate timestamp NULL,
#         releasedate timestamp NULL,
#         emergencyflag numeric(1) DEFAULT 0 NULL,
#         emrgncdate timestamp NULL,
#         emrlocation numeric(10) NULL,
#         edocid numeric(10) NULL,
#         "source" varchar(10) NULL,
#         CONSTRAINT pk_patient_regstrnid PRIMARY KEY (registrationid)
#     );    
#     """,
#     "registration.addressmaster":"""
#         CREATE TABLE registration.addressmaster (
#         registrationid numeric(19) NOT NULL,
#         addresstypeid numeric(10) NOT NULL,
#         street varchar(200) NULL,
#         locality varchar(200) NULL,
#         country numeric(19) NULL,
#         state numeric(19) NULL,
#         district numeric(19) NULL,
#         city numeric(19) NULL,
#         address1 varchar(500) NULL,
#         address2 varchar(500) NULL,
#         residencenumber varchar(100) NULL,
#         officenumber varchar(100) NULL,
#         "extension" varchar(100) NULL,
#         mobilenumber varchar(100) NULL,
#         emergencynumber varchar(100) NULL,
#         residencefaxnumber varchar(100) NULL,
#         officefaxnumber varchar(100) NULL,
#         primaryemail varchar(200) NULL,
#         alternateemail varchar(200) NULL,
#         pincode varchar(40) NULL,
#         contactnumber1 varchar(100) NULL,
#         contactnumber2 varchar(100) NULL,
#         startdate timestamp NULL,
#         enddate timestamp NULL,
#         status numeric(10) NULL,
#         updatedby varchar(100) NULL,
#         updateddate timestamp NULL,
#         flexifield1 varchar(100) NULL,
#         flexifield2 varchar(100) NULL
#         );
#         ALTER TABLE registration.addressmaster ADD CONSTRAINT fk_taddtype_taddress FOREIGN KEY (addresstypeid) REFERENCES registration.addresstypemaster(addresstypeid);
#     """,
#     "registration.patientvisadetail":"""
#         CREATE TABLE registration.patientvisadetail (
#         registrationid numeric(19) NOT NULL,
#         nationality varchar(200) NULL,
#         internationalpatient varchar(200) NULL,
#         countryissued numeric(10) NULL,
#         passportnumber varchar(100) NULL,
#         passportissuedate timestamp NULL,
#         passportexpirydate timestamp NULL,
#         visatype varchar(100) NULL,
#         visaissuingauthority varchar(100) NULL,
#         visaissuedate timestamp NULL,
#         visaexpirydate timestamp NULL,
#         startdate timestamp NULL,
#         enddate timestamp NULL,
#         status numeric(10) NULL,
#         updatedby varchar(100) NULL,
#         updateddate timestamp NULL,
#         flexifield1 varchar(100) NULL,
#         flexifield2 varchar(100) NULL,
#         CONSTRAINT pk_patientvisadetail PRIMARY KEY (registrationid)
#         );
#     """,
#     "billing.patientpolicymaster":"""
#         CREATE TABLE billing.patientpolicymaster (
#         patientpolicymasterid numeric NOT NULL,
#         locationid varchar(50) NULL,
#         registrationno varchar(100) NOT NULL,
#         billingtypeid numeric NULL,
#         createdby varchar(100) NULL,
#         createddte timestamp NULL,
#         updatedby varchar(100) NULL,
#         updateddate timestamp NULL,
#         CONSTRAINT pk_policymaster PRIMARY KEY (patientpolicymasterid)
#         );
    
#     """,
#     "billing.opmaster":"""
#         CREATE TABLE billing.opmaster (
#         opmasterid numeric NULL,
#         locationid varchar(50) NULL,
#         registrationno varchar(100) NULL,
#         patientidentifierno varchar(100) NULL,
#         patientname varchar(200) NULL,
#         billingtypeid numeric NULL,
#         patientserviceid numeric NULL,
#         createdby varchar(100) NULL,
#         createddate timestamp NULL,
#         updatedby varchar(100) NULL,
#         updateddate timestamp NULL,
#         patienttypeid numeric NULL,
#         primarydoctorid numeric NULL,
#         referraldoctorid numeric NULL,
#         cusotmerid numeric NULL,
#         agreementid numeric NULL,
#         visitno numeric NULL,
#         wardsopnumber varchar(100) NULL,
#         isgenfromreg bpchar(1) DEFAULT 0 NULL,
#         deleteflag numeric DEFAULT 1 NULL,
#         otrequestnumber varchar(50) NULL,
#         serviceid numeric NULL,
#         serviceamount numeric NULL,
#         prism_flag numeric NULL
#         );
#     """,
#     "billing.servicerequest":"""
#         CREATE TABLE billing.servicerequest (
#         registrationno varchar(100) NULL,
#         patientidentifierno varchar(50) NULL,
#         requestid numeric NOT NULL,
#         requesteddeptid varchar(50) NULL,
#         requestdate timestamp NULL,
#         createdby varchar(50) NULL,
#         updatedby varchar(50) NULL,
#         updateddate timestamp NULL,
#         locationid varchar(50) NOT NULL,
#         companyid varchar(20) NULL,
#         patientserviceid numeric NULL,
#         biliingtype numeric NULL,
#         customerid numeric NULL,
#         bedcategoryid numeric NULL,
#         billingservice varchar(10) NULL,
#         requestno varchar(100) NULL,
#         patienttypeid numeric NULL,
#         createddate timestamp NULL,
#         doctorid varchar(30) NULL,
#         requeststatus varchar(50) DEFAULT NULL::character varying NULL,
#         admissionnoteno varchar(50) NULL,
#         status numeric DEFAULT 1 NULL,
#         agreementid numeric NULL,
#         requestedfromurl varchar(100) NULL,
#         remarks varchar(350) NULL,
#         transferlocationid varchar(50) NULL,
#         baselocationid varchar(50) NULL,
#         CONSTRAINT servicerequest_pk PRIMARY KEY (requestid, locationid)
#         );
#     """,
#     "billing.servicerequestdetails":"""
#         CREATE TABLE billing.servicerequestdetails (
#         servicerequestdetailsid numeric NOT NULL,
#         requestid numeric NOT NULL,
#         serviceid numeric NULL,
#         billingstatus varchar(20) NULL,
#         servicestatus varchar(100) NULL,
#         bedcategoryid numeric NULL,
#         createdby varchar(100) NULL,
#         updatedby varchar(100) NULL,
#         updateddate timestamp NULL,
#         createddate timestamp NULL,
#         servicename varchar(200) NULL,
#         servicetypeid numeric NULL,
#         locationid varchar(50) NULL,
#         mappedpackageid numeric NULL,
#         requestno varchar(100) NULL,
#         includedinpackage varchar(2) NULL,
#         fnbservicerequestid numeric NULL,
#         bloodbagno varchar(50) NULL,
#         bloodtype varchar(50) NULL,
#         startdatetime timestamp NULL,
#         enddatetime timestamp NULL,
#         payerid numeric NULL,
#         authrequestid numeric NULL,
#         authrequestedflag numeric DEFAULT 0 NULL,
#         doctorid varchar(20) NULL,
#         doctorfeetypeid numeric NULL,
#         consultationdate timestamp NULL,
#         consultationtime varchar(50) NULL,
#         authstatusid numeric NULL,
#         requestedbedcategoryid numeric NULL,
#         allotedbedcategoryid numeric NULL,
#         billablebedcategoryid numeric NULL,
#         pkgroomrent numeric NULL,
#         pkgicu numeric NULL,
#         servicedetailindex numeric NULL,
#         requestdate timestamp NULL,
#         doctorfeeamount numeric NULL,
#         upgradedpackageid numeric NULL,
#         requestedquantity numeric DEFAULT 1 NULL,
#         billno varchar(50) NULL,
#         extrachargeflag varchar(5) NULL,
#         billabledate timestamp NULL,
#         applicabledate timestamp NULL,
#         packageexcluded varchar(20) NULL,
#         creditnoteissued bpchar(1) DEFAULT 'N'::bpchar NULL,
#         creditnotetranid numeric NULL,
#         remarks varchar(350) NULL,
#         degradedpackageid numeric NULL,
#         promodiscount bpchar(1) NULL,
#         patientpayable bpchar(1) NULL,
#         bedsideflag varchar(5) NULL,
#         issecondary bpchar(1) NULL
#         )
#         PARTITION BY RANGE (servicerequestdetailsid);
#     """,
#     "billing.generalaccountmaster":"""
#         CREATE TABLE billing.generalaccountmaster (
#         cumdebitamount numeric(20, 4) DEFAULT 0 NULL,
#         cumcreditamount numeric(20, 4) DEFAULT 0 NULL,
#         accountstatus varchar(100) NULL,
#         accountcreationdate timestamp NULL,
#         accountclosedate timestamp NULL,
#         locationid varchar(100) NOT NULL,
#         amountblockedip numeric(20, 4) DEFAULT 0 NULL,
#         amountblockedop numeric(20, 4) DEFAULT 0 NULL,
#         currencycode varchar(10) NULL,
#         customerid varchar(100) NULL,
#         companyid varchar(100) NULL,
#         createdby varchar(50) NULL,
#         createddate timestamp NULL,
#         accountno varchar(100) NOT NULL,
#         waiverallowed varchar(100) NULL,
#         updateddate timestamp NULL,
#         updatedby varchar(100) NULL,
#         accounttype bpchar(1) NULL,
#         cumminimumdeposit numeric DEFAULT 0 NULL,
#         packagedueamount numeric NULL,
#         remarks varchar(350) NULL,
#         CONSTRAINT pk_generalaccountmaster PRIMARY KEY (accountno)
#         );
#     """
# }


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
# def generate_data_for_table(all_generated_data,previous_generated_data, table_name, table_df, detected_relationships, records_per_batch=10, total_records=100):
#     # all_generated_data = []  # List to store all generated data
#     # Keep track of all previous batches' records
    
#     # Number of batches we need
#     num_batches = total_records // records_per_batch
#     print('num_batches:', num_batches)
#     for batch_num in range(num_batches):
#         print('batch_num:', batch_num)

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
#         - Ensure the generated data is different from all previously generated data
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
#                 print(len(new_records), ' Length of Batch Records')
#                 # Add the new batch of records to all generated data
#                 all_generated_data.extend(new_records)
#                 previous_generated_data.extend(new_records)  # Add to the previous batch data for next iteration

#                 # Ensure we only generate the desired number of records
#                 if len(all_generated_data) >= total_records:
#                     break

#             except json.JSONDecodeError as e:
#                 print(f"JSON decode error for {table_name}: {e}")
#                 continue
#                 # return None

#         except Exception as e:
#             print(f"Error generating data for {table_name} (batch {batch_num+1}): {e}")
#             return None
#     if len(all_generated_data) < total_records:
#         print('Attempted to generate less records than requested')
#         generate_data_for_table(all_generated_data, previous_generated_data, table_name, table_df, detected_relationships)
#     # Return the final generated data
#     return {table_name: all_generated_data, 'previous_data': previous_generated_data}

# # Main logic to process each table one by one
# detected_relationships = infer_relationships(tables)

# print(tables.keys(), '===========')
# for file_name, df in tables.items():
#     # if file_name not in ['2-registration.patient.csv']:
#     #     continue
#     print(f"Generating test data for {file_name}...")
#     all_generated_data = []
#     previous_generated_data = []
#     # Generate data for each table in batches of 10, totaling 100 records
#     generated_data = generate_data_for_table(all_generated_data,previous_generated_data, file_name, df, detected_relationships)

#     if generated_data:
#         generated_data = generated_data[:101] if len(generated_data)>100 else generated_data
#         output_path = os.path.join(output_dir, file_name)
#         print(f"Saving generated data for {file_name} to {output_path}...")
#         generated_df = pd.DataFrame(generated_data[file_name])
#         generated_df.to_csv(output_path, index=False)
#     else:
#         print(f"Failed to generate data for {file_name}. Moving to next table.")

# print(f"Test data generation complete. Output saved in '{output_dir}' folder.")