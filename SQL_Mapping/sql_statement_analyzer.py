from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import csv
from typing import List, Dict

class SQLStatementAnalyzer:
    def __init__(self, api_key: str, azure_endpoint: str, deployment_name: str):
        self.client = AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            azure_deployment=deployment_name,
            api_key=api_key,
            api_version="2024-12-01-preview",
            temperature=0.1,
        )

    def analyze_sql_files(self, source_content: str, target_content: str) -> List[Dict]:
        """Analyze and map SQL statements between source and target using Azure OpenAI."""

        prompt = f"""
        You are a SQL migration expert. Analyze these two SQL procedures (Oracle source and PostgreSQL target)
        and create a detailed mapping following these rules:

        1. Split and map SQL statements:
           - Split complete SQL statements at semicolons (;)
           - Each semicolon-terminated statement should be mapped independently
           - Keep statements with their associated comments
           - Include declaration sections and control structures

        2. Map each meaningful component including:
           - Complete SQL statements (split at semicolons)
           - Comments preceding or following statements
           - Declaration sections
           - Control structures
           - Empty lines that affect structure

        3. For each line identify:
           - The exact source content
           - The corresponding target content
           - Sequential line numbers for both source and target
           - Whether it's mapped or not found

        4. Special handling:
           - If a statement exists only in source, mark as "Source Only"
           - If a statement exists only in target, mark as "Target Only"
           - Keep track of line numbers even when they don't match
           - Preserve all comments and their placement
           - Include procedure structure elements (BEGIN, END, etc.)
           - Ensure each complete SQL statement (ending with semicolon) is treated as one unit

        Source SQL:
        {source_content}

        Target SQL:
        {target_content}

        Return the response strictly as a JSON array. Do not include any explanation or extra text:
        - source_statement: The exact statement/line from source (complete statement if semicolon-terminated)
        - target_statement: The corresponding statement/line in target
        - source_line_number: Sequential number in source
        - target_line_number: Sequential number in target
        - status: "Mapped", "Source Only", or "Target Only"
        """

        # Get analysis from Azure OpenAI using LangChain interface
        messages = [
            SystemMessage(content="You are a SQL migration expert specializing in Oracle to PostgreSQL conversions."),
            HumanMessage(content=prompt)
        ]

        response = self.client.invoke(messages, response_format={"type": "json_object"})
        import json
        response_data = json.loads(response.content)
        if 'mapping' in response_data:
            response_data =  response_data['mapping']
        # Ensure response_data is a list of objects
        if isinstance(response_data, list):
            print(response_data)  # Debug: Print the entire list of mappings
            # Process and return the mappings
            return response_data
        else:
            raise ValueError("Unexpected response format: Expected a list of objects.")

    def save_to_csv(self, mappings: List[Dict], output_file: str):
        """Save the mappings to a CSV file."""
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Source Statement', 'Target Statement', 'Source Statement Number',
                           'Target Statement Number', 'Status'])

            for mapping in mappings:
                writer.writerow([
                    mapping['source_statement'],
                    mapping['target_statement'],
                    mapping['source_line_number'],
                    mapping['target_line_number'] if mapping['target_line_number'] != '-' else '-',
                    mapping['status']
                ])

def main():
    # Azure OpenAI configuration
    api_key = "wBjgqz2HegyKwtsNCInM8T0aGAYsSFQ2sPHrv2N9BNhmmreKVJ1NJQQJ99BDACYeBjFXJ3w3AAAAACOGQOtm"
    azure_endpoint = "https://ai-testgeneration707727059630.openai.azure.com/"
    deployment_name = "gpt4-deployment"  # The name you gave to your deployed model

    # Initialize analyzer
    analyzer = SQLStatementAnalyzer(api_key, azure_endpoint, deployment_name)

    # Read source and target SQL files
    with open('source.sql', 'r') as f:
        source_content = f.read()
    with open('target.sql', 'r') as f:
        target_content = f.read()

    # Generate mappings
    mappings = analyzer.analyze_sql_files(source_content, target_content)

    # Save to CSV
    analyzer.save_to_csv(mappings, 'azure_sql_mappings.csv')
    print('File Saved')

if __name__ == "__main__":
    main()
