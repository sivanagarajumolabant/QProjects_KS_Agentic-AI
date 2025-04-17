# SQL Statement Mapper

This tool uses AI to create detailed mappings between Oracle and PostgreSQL statements.

## Features

- Splits SQL files into individual statements
- Analyzes and maps corresponding statements
- Handles complex cases like PL/SQL blocks
- Creates detailed JSON mappings including:
  - Statement type
  - Column and data type mappings
  - Syntax differences
  - Control structures
  - Potential issues/warnings

## Setup

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key in the script

## Usage

1. Place your source Oracle SQL in `source_oracle.sql`
2. Place your target PostgreSQL SQL in `target_postgres.sql`
3. Run the mapper:
```python
from sql_statement_mapper import SQLStatementMapper

mapper = SQLStatementMapper("your-api-key-here")
mappings = mapper.create_mapping("source_oracle.sql", "target_postgres.sql")
mapper.save_mappings(mappings, "sql_mappings.json")
```

The tool will generate a JSON file containing detailed mappings between the statements.
