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

        1. Split and map SQL statements - VERY IMPORTANT:
           - Each semicolon (;) marks the end of a separate statement
           - Split statements ONLY at semicolons, keeping the semicolon with its statement
           - DO NOT combine multiple semicolon-terminated statements
           - Each IF/ELSE/BEGIN/END block should be split into its component statements
           - Keep comments with their immediately following statement

        2. Map each component after splitting:
           - Each statement must be exactly as it appears in the source/target
           - Include the semicolon at the end of each statement
           - Keep proper indentation and formatting
           - Include all comments that precede a statement

        3. For each split statement identify:
           - The exact statement content including its semicolon
           - The line number where the statement starts
           - The line number where the statement ends (at the semicolon)
           - Whether it exists in both source and target

        4. Special handling:
           - Split compound statements at their semicolons (e.g. multiple SELECTs/UPDATEs)
           - Keep variable declarations as separate statements
           - Split each DML statement (SELECT/INSERT/UPDATE/DELETE) separately
           - Split each control statement (IF/ELSE/BEGIN/END) at its semicolon
           - IMPORTANT: Include ALL target statements, even if they don't exist in source

        Source SQL:
        {source_content}

        Target SQL:
        {target_content}

        Return the response strictly as a JSON array where each object has these exact fields:
        source_statement: The exact statement from source or empty string if target-only
        target_statement: The corresponding statement in target
        source_line_number: Sequential number in source or "-" if target-only
        target_line_number: Sequential number in target
        status: One of "Mapped", "Source Only", or "Target Only"

        IMPORTANT: Make sure to include ALL statements from both source and target, including:
        1. Statements that match between source and target (status: Mapped)
        2. Statements only in source (status: Source Only)
        3. Statements only in target (status: Target Only)

        For target-only statements, use:
        - source_statement: ""
        - source_line_number: "-"
        - status: "Target Only"
        """

        # Get analysis from Azure OpenAI using LangChain interface
        messages = [
            SystemMessage(content="You are a SQL migration expert specializing in Oracle to PostgreSQL conversions. You must include ALL statements from both source and target in your mapping, especially target-only statements. IMPORTANT: Split each statement at semicolons."),
            HumanMessage(content=prompt)
        ]

        response = self.client.invoke(messages, response_format={"type": "json_object"})
        import json
        response_data = json.loads(response.content)
        if 'response' in response_data:
            response_data = response_data['response']
        print(response_data)
        # Ensure response_data is a list of objects and validate each mapping
        if isinstance(response_data, list):
            # Validate and clean mappings
            cleaned_mappings = []
            for mapping in response_data:
                if all(k in mapping for k in ['source_statement', 'target_statement', 'source_line_number', 'target_line_number', 'status']):
                    # Ensure target-only entries are properly formatted
                    if mapping['status'] == 'Target Only':
                        mapping['source_statement'] = ''
                        mapping['source_line_number'] = '-'
                    cleaned_mappings.append(mapping)
            
            print("Total mappings:", len(cleaned_mappings))  # Debug: Print count of mappings
            return cleaned_mappings
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
