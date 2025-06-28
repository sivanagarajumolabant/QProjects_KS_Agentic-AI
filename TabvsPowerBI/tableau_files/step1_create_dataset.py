"""
Step 1: Create Power BI Dataset Structure
This script reads our sample CSV data and creates the basic dataset structure for Power BI conversion.
"""

import pandas as pd
import json
import os
from datetime import datetime

def load_sample_data():
    """Load the sample sales data from CSV file"""
    try:
        # Load the CSV data
        csv_path = os.path.join('tableau_files', 'sample_sales_data.csv')
        df = pd.read_csv(csv_path)
        
        # Convert OrderDate to datetime
        df['OrderDate'] = pd.to_datetime(df['OrderDate'])
        
        print(f"✅ Loaded {len(df)} records from sample data")
        print(f"📊 Columns: {list(df.columns)}")
        print(f"📅 Date range: {df['OrderDate'].min()} to {df['OrderDate'].max()}")
        
        return df
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None

def analyze_data_structure(df):
    """Analyze the data structure and create field definitions"""
    
    field_definitions = []
    
    for column in df.columns:
        dtype = df[column].dtype
        
        # Determine Power BI data type and role
        if column in ['OrderID', 'CustomerID', 'ProductName', 'Category', 'Region']:
            # Dimensions (categorical data)
            field_def = {
                'name': column,
                'datatype': 'string' if dtype == 'object' else 'integer',
                'role': 'dimension',
                'type': 'nominal' if dtype == 'object' else 'ordinal',
                'aggregation': 'Count'
            }
        elif column == 'OrderDate':
            # Date dimension
            field_def = {
                'name': column,
                'datatype': 'datetime',
                'role': 'dimension',
                'type': 'ordinal',
                'aggregation': 'Year'
            }
        elif column in ['SalesAmount', 'Quantity', 'Profit']:
            # Measures (numeric data for aggregation)
            field_def = {
                'name': column,
                'datatype': 'real' if column in ['SalesAmount', 'Profit'] else 'integer',
                'role': 'measure',
                'type': 'quantitative',
                'aggregation': 'Sum'
            }
        
        field_definitions.append(field_def)
    
    return field_definitions

def create_calculated_fields():
    """Define the calculated fields that need to be converted from Tableau to DAX"""
    
    calculated_fields = [
        {
            'name': 'Profit Margin',
            'tableau_formula': 'SUM([Profit]) / SUM([SalesAmount])',
            'dax_formula': 'DIVIDE(SUM(Sales[Profit]), SUM(Sales[SalesAmount]), 0)',
            'datatype': 'real',
            'role': 'measure',
            'description': 'Profit margin percentage calculation'
        },
        {
            'name': 'Sales Category',
            'tableau_formula': 'IF SUM([SalesAmount]) > 10000 THEN "High Sales" ELSEIF SUM([SalesAmount]) > 5000 THEN "Medium Sales" ELSE "Low Sales" END',
            'dax_formula': 'IF(SUM(Sales[SalesAmount]) > 10000, "High Sales", IF(SUM(Sales[SalesAmount]) > 5000, "Medium Sales", "Low Sales"))',
            'datatype': 'string',
            'role': 'dimension',
            'description': 'Categorizes sales amounts into High/Medium/Low'
        },
        {
            'name': 'Year',
            'tableau_formula': 'YEAR([OrderDate])',
            'dax_formula': 'YEAR(Sales[OrderDate])',
            'datatype': 'integer',
            'role': 'dimension',
            'description': 'Extract year from order date'
        },
        {
            'name': 'Quarter',
            'tableau_formula': '"Q" + STR(DATEPART("quarter", [OrderDate]))',
            'dax_formula': '"Q" & FORMAT(Sales[OrderDate], "Q")',
            'datatype': 'string',
            'role': 'dimension',
            'description': 'Extract quarter from order date (Q1, Q2, Q3, Q4)'
        }
    ]
    
    return calculated_fields

def create_dataset_metadata(df, field_definitions, calculated_fields):
    """Create comprehensive dataset metadata for Power BI conversion"""
    
    metadata = {
        'dataset_info': {
            'name': 'Sales Data',
            'description': 'Sample sales dataset converted from Tableau',
            'created_date': datetime.now().isoformat(),
            'record_count': len(df),
            'source_type': 'CSV',
            'source_path': 'tableau_files/sample_sales_data.csv'
        },
        'connection_info': {
            'original_tableau': {
                'type': 'SQL Server',
                'server': 'sql-server-01',
                'database': 'SalesDB',
                'table': '[dbo].[Sales]',
                'authentication': 'Windows Authentication'
            },
            'powerbi_equivalent': {
                'type': 'CSV',
                'path': 'tableau_files/sample_sales_data.csv',
                'note': 'Using CSV for demo - would be SQL Server in production'
            }
        },
        'base_fields': field_definitions,
        'calculated_fields': calculated_fields,
        'data_summary': {
            'total_sales': float(df['SalesAmount'].sum()),
            'total_profit': float(df['Profit'].sum()),
            'total_quantity': int(df['Quantity'].sum()),
            'unique_customers': df['CustomerID'].nunique(),
            'unique_products': df['ProductName'].nunique(),
            'regions': df['Region'].unique().tolist(),
            'categories': df['Category'].unique().tolist(),
            'date_range': {
                'start': df['OrderDate'].min().isoformat(),
                'end': df['OrderDate'].max().isoformat()
            }
        }
    }
    
    return metadata

def save_dataset_structure(df, metadata):
    """Save the dataset and metadata for next steps"""
    
    # Create output directory
    os.makedirs('powerbi_output', exist_ok=True)
    
    # Save the processed data
    df.to_csv('powerbi_output/sales_data_processed.csv', index=False)
    
    # Save metadata as JSON
    with open('powerbi_output/dataset_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    
    print("✅ Dataset structure created successfully!")
    print("📁 Files saved:")
    print("   - powerbi_output/sales_data_processed.csv")
    print("   - powerbi_output/dataset_metadata.json")

def main():
    """Main function to execute Step 1"""
    print("🚀 Step 1: Creating Power BI Dataset Structure")
    print("=" * 50)
    
    # Load sample data
    df = load_sample_data()
    if df is None:
        return
    
    # Analyze data structure
    print("\n📋 Analyzing data structure...")
    field_definitions = analyze_data_structure(df)
    
    # Create calculated fields definitions
    print("🧮 Defining calculated fields...")
    calculated_fields = create_calculated_fields()
    
    # Create comprehensive metadata
    print("📊 Creating dataset metadata...")
    metadata = create_dataset_metadata(df, field_definitions, calculated_fields)
    
    # Save everything
    print("💾 Saving dataset structure...")
    save_dataset_structure(df, metadata)
    
    # Display summary
    print(f"\n📈 Dataset Summary:")
    print(f"   Records: {len(df):,}")
    print(f"   Base Fields: {len(field_definitions)}")
    print(f"   Calculated Fields: {len(calculated_fields)}")
    print(f"   Total Sales: ${metadata['data_summary']['total_sales']:,.2f}")
    print(f"   Total Profit: ${metadata['data_summary']['total_profit']:,.2f}")
    
    print(f"\n✨ Step 1 Complete! Ready for Step 2: DAX Conversion")

if __name__ == "__main__":
    main()
