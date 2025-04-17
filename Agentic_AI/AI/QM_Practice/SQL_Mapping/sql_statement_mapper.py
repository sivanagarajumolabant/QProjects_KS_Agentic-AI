from typing import List, Dict, Tuple
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json

class SQLStatementMapper:
    def __init__(self, api_key: str):
        """Initialize the SQL Statement Mapper with OpenAI API key."""
        self.llm = ChatOpenAI(
            api_key=api_key,
            model="gpt-4",
            temperature=0.2
        )
        
        self.mapping_prompt = ChatPromptTemplate.from_template("""
            You are an expert in SQL migration from Oracle to PostgreSQL.
            Analyze the following SQL statements and create a detailed mapping:
            
            Source (Oracle) SQL: {source_sql}
            Target (PostgreSQL) SQL: {target_sql}
            
            Create a JSON response with the following structure:
            1. Statement type (CREATE, INSERT, UPDATE, etc.)
            2. Mapping of columns and their data types
            3. Differences in syntax or functionality
            4. Control structures (if any)
            5. Any potential issues or warnings
            
            Respond only with the JSON structure, no additional text.
        """)

    def split_sql_statements(self, sql_content: str) -> List[str]:
        """Split SQL content into individual statements by semicolon."""
        # Handle complex cases like PL/SQL blocks
        statements = []
        current_statement = []
        in_plsql_block = False
        
        for line in sql_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('--'):
                continue
                
            if 'BEGIN' in line.upper():
                in_plsql_block = True
            
            if in_plsql_block:
                current_statement.append(line)
                if 'END;' in line.upper():
                    in_plsql_block = False
                    statements.append('\n'.join(current_statement))
                    current_statement = []
            else:
                if line.endswith(';'):
                    current_statement.append(line[:-1])
                    statements.append('\n'.join(current_statement))
                    current_statement = []
                else:
                    current_statement.append(line)
        
        # Add any remaining statement
        if current_statement:
            statements.append('\n'.join(current_statement))
            
        return [stmt.strip() for stmt in statements if stmt.strip()]

    def analyze_statements(self, source_sql: str, target_sql: str) -> Dict:
        """Analyze and create mapping between source and target SQL statements."""
        response = self.llm.invoke(
            self.mapping_prompt.format(
                source_sql=source_sql,
                target_sql=target_sql
            )
        )
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse mapping response",
                "raw_response": response.content
            }

    def create_mapping(self, source_file: str, target_file: str) -> List[Dict]:
        """Create mappings for all statements in the source and target files."""
        # Read files
        with open(source_file, 'r') as f:
            source_content = f.read()
        with open(target_file, 'r') as f:
            target_content = f.read()
            
        # Split statements
        source_statements = self.split_sql_statements(source_content)
        target_statements = self.split_sql_statements(target_content)
        
        mappings = []
        
        # Create mappings for each pair of statements
        for source_stmt, target_stmt in zip(source_statements, target_statements):
            mapping = self.analyze_statements(source_stmt, target_stmt)
            mappings.append(mapping)
            
        return mappings

    def save_mappings(self, mappings: List[Dict], output_file: str):
        """Save the mappings to a JSON file."""
        with open(output_file, 'w') as f:
            json.dump(mappings, f, indent=2)

# Example usage
if __name__ == "__main__":
    # Initialize mapper with your OpenAI API key
    mapper = SQLStatementMapper("your-api-key-here")
    
    # Example files
    source_file = "source_oracle.sql"
    target_file = "target_postgres.sql"
    output_file = "sql_mappings.json"
    
    # Create mappings
    mappings = mapper.create_mapping(source_file, target_file)
    
    # Save mappings
    mapper.save_mappings(mappings, output_file)
