"""
Step 2: Convert Calculated Fields to DAX Measures
This script converts Tableau calculated fields to Power BI DAX equivalents and validates them.
"""

import json
import pandas as pd
import os
from datetime import datetime

def load_metadata():
    """Load the dataset metadata from Step 1"""
    try:
        with open('powerbi_output/dataset_metadata.json', 'r') as f:
            metadata = json.load(f)
        print("✅ Loaded dataset metadata")
        return metadata
    except Exception as e:
        print(f"❌ Error loading metadata: {e}")
        return None

def create_dax_measures(calculated_fields):
    """Create DAX measures from calculated fields"""
    
    dax_measures = []
    
    for field in calculated_fields:
        if field['role'] == 'measure':
            # This is a measure (aggregated calculation)
            measure = {
                'name': field['name'],
                'dax_formula': field['dax_formula'],
                'format': get_format_string(field),
                'description': field['description'],
                'type': 'measure',
                'original_tableau': field['tableau_formula']
            }
            dax_measures.append(measure)
    
    return dax_measures

def create_dax_calculated_columns(calculated_fields):
    """Create DAX calculated columns from calculated fields"""
    
    dax_columns = []
    
    for field in calculated_fields:
        if field['role'] == 'dimension':
            # This is a calculated column (row-level calculation)
            
            # For dimension calculations, we need to adjust the DAX
            adjusted_dax = adjust_dax_for_calculated_column(field)
            
            column = {
                'name': field['name'],
                'dax_formula': adjusted_dax,
                'datatype': field['datatype'],
                'description': field['description'],
                'type': 'calculated_column',
                'original_tableau': field['tableau_formula']
            }
            dax_columns.append(column)
    
    return dax_columns

def adjust_dax_for_calculated_column(field):
    """Adjust DAX formulas for calculated columns (row-level vs aggregated)"""
    
    if field['name'] == 'Sales Category':
        # This needs to be a measure, not a calculated column
        # Keep the original aggregated version
        return field['dax_formula']
    elif field['name'] == 'Year':
        # Row-level calculation - no aggregation needed
        return 'YEAR(Sales[OrderDate])'
    elif field['name'] == 'Quarter':
        # Row-level calculation - no aggregation needed  
        return '"Q" & FORMAT(Sales[OrderDate], "Q")'
    else:
        return field['dax_formula']

def get_format_string(field):
    """Get appropriate format string for the field"""
    
    if field['name'] == 'Profit Margin':
        return 'Percentage'
    elif field['datatype'] == 'real' and 'Amount' in field['name']:
        return 'Currency'
    elif field['datatype'] == 'real':
        return 'Decimal'
    elif field['datatype'] == 'integer':
        return 'Whole Number'
    else:
        return 'General'

def create_enhanced_dax_measures():
    """Create additional useful DAX measures for the sales report"""
    
    enhanced_measures = [
        {
            'name': 'Total Sales',
            'dax_formula': 'SUM(Sales[SalesAmount])',
            'format': 'Currency',
            'description': 'Total sales amount',
            'type': 'measure'
        },
        {
            'name': 'Total Profit',
            'dax_formula': 'SUM(Sales[Profit])',
            'format': 'Currency',
            'description': 'Total profit amount',
            'type': 'measure'
        },
        {
            'name': 'Total Quantity',
            'dax_formula': 'SUM(Sales[Quantity])',
            'format': 'Whole Number',
            'description': 'Total quantity sold',
            'type': 'measure'
        },
        {
            'name': 'Average Order Value',
            'dax_formula': 'DIVIDE(SUM(Sales[SalesAmount]), DISTINCTCOUNT(Sales[OrderID]), 0)',
            'format': 'Currency',
            'description': 'Average value per order',
            'type': 'measure'
        },
        {
            'name': 'Order Count',
            'dax_formula': 'DISTINCTCOUNT(Sales[OrderID])',
            'format': 'Whole Number',
            'description': 'Total number of orders',
            'type': 'measure'
        },
        {
            'name': 'Customer Count',
            'dax_formula': 'DISTINCTCOUNT(Sales[CustomerID])',
            'format': 'Whole Number',
            'description': 'Total number of customers',
            'type': 'measure'
        }
    ]
    
    return enhanced_measures

def validate_dax_syntax(dax_measures, dax_columns):
    """Basic validation of DAX syntax"""
    
    validation_results = []
    
    # Check measures
    for measure in dax_measures:
        result = {
            'name': measure['name'],
            'type': 'measure',
            'formula': measure['dax_formula'],
            'valid': True,
            'issues': []
        }
        
        # Basic syntax checks
        formula = measure['dax_formula']
        
        # Check for balanced parentheses
        if formula.count('(') != formula.count(')'):
            result['valid'] = False
            result['issues'].append('Unbalanced parentheses')
        
        # Check for proper table references
        if 'Sales[' not in formula and any(field in formula for field in ['SalesAmount', 'Profit', 'OrderDate']):
            result['issues'].append('Missing table reference - should use Sales[FieldName]')
        
        validation_results.append(result)
    
    # Check calculated columns
    for column in dax_columns:
        result = {
            'name': column['name'],
            'type': 'calculated_column',
            'formula': column['dax_formula'],
            'valid': True,
            'issues': []
        }
        
        # Basic syntax checks for calculated columns
        formula = column['dax_formula']
        
        if formula.count('(') != formula.count(')'):
            result['valid'] = False
            result['issues'].append('Unbalanced parentheses')
        
        validation_results.append(result)
    
    return validation_results

def generate_powerbi_dax_script(dax_measures, dax_columns, enhanced_measures):
    """Generate a Power BI DAX script that can be used to create measures and columns"""
    
    script_lines = []
    script_lines.append("-- Power BI DAX Script")
    script_lines.append("-- Generated from Tableau to Power BI Migration")
    script_lines.append(f"-- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    script_lines.append("")
    
    # Add measures
    script_lines.append("-- MEASURES")
    script_lines.append("-- ========")
    script_lines.append("")
    
    all_measures = dax_measures + enhanced_measures
    
    for measure in all_measures:
        script_lines.append(f"-- {measure['description']}")
        script_lines.append(f"{measure['name']} = {measure['dax_formula']}")
        script_lines.append("")
    
    # Add calculated columns
    script_lines.append("-- CALCULATED COLUMNS")
    script_lines.append("-- ==================")
    script_lines.append("")
    
    for column in dax_columns:
        script_lines.append(f"-- {column['description']}")
        script_lines.append(f"{column['name']} = {column['dax_formula']}")
        script_lines.append("")
    
    return '\n'.join(script_lines)

def save_dax_conversion_results(dax_measures, dax_columns, enhanced_measures, validation_results, dax_script):
    """Save all DAX conversion results"""
    
    # Create comprehensive conversion results
    conversion_results = {
        'conversion_info': {
            'step': 'Step 2 - DAX Conversion',
            'created_date': datetime.now().isoformat(),
            'total_measures': len(dax_measures) + len(enhanced_measures),
            'total_calculated_columns': len(dax_columns)
        },
        'original_calculated_fields': len(dax_measures) + len(dax_columns),
        'dax_measures': dax_measures,
        'dax_calculated_columns': dax_columns,
        'enhanced_measures': enhanced_measures,
        'validation_results': validation_results
    }
    
    # Save JSON results
    with open('powerbi_output/dax_conversion_results.json', 'w') as f:
        json.dump(conversion_results, f, indent=2)
    
    # Save DAX script
    with open('powerbi_output/powerbi_dax_script.dax', 'w') as f:
        f.write(dax_script)
    
    print("✅ DAX conversion results saved!")
    print("📁 Files created:")
    print("   - powerbi_output/dax_conversion_results.json")
    print("   - powerbi_output/powerbi_dax_script.dax")

def main():
    """Main function to execute Step 2"""
    print("🚀 Step 2: Converting Calculated Fields to DAX")
    print("=" * 50)
    
    # Load metadata from Step 1
    metadata = load_metadata()
    if metadata is None:
        return
    
    calculated_fields = metadata['calculated_fields']
    print(f"📊 Found {len(calculated_fields)} calculated fields to convert")
    
    # Create DAX measures and calculated columns
    print("\n🧮 Creating DAX measures...")
    dax_measures = create_dax_measures(calculated_fields)
    
    print("📋 Creating DAX calculated columns...")
    dax_columns = create_dax_calculated_columns(calculated_fields)
    
    print("⚡ Creating enhanced measures...")
    enhanced_measures = create_enhanced_dax_measures()
    
    # Validate DAX syntax
    print("✅ Validating DAX syntax...")
    validation_results = validate_dax_syntax(dax_measures, dax_columns)
    
    # Generate Power BI script
    print("📝 Generating Power BI DAX script...")
    dax_script = generate_powerbi_dax_script(dax_measures, dax_columns, enhanced_measures)
    
    # Save results
    print("💾 Saving conversion results...")
    save_dax_conversion_results(dax_measures, dax_columns, enhanced_measures, validation_results, dax_script)
    
    # Display summary
    print(f"\n📈 Conversion Summary:")
    print(f"   DAX Measures: {len(dax_measures)}")
    print(f"   Calculated Columns: {len(dax_columns)}")
    print(f"   Enhanced Measures: {len(enhanced_measures)}")
    print(f"   Total DAX Objects: {len(dax_measures) + len(dax_columns) + len(enhanced_measures)}")
    
    # Show validation results
    valid_count = sum(1 for r in validation_results if r['valid'])
    print(f"   Validation: {valid_count}/{len(validation_results)} passed")
    
    if valid_count < len(validation_results):
        print("\n⚠️  Validation Issues:")
        for result in validation_results:
            if not result['valid']:
                print(f"   - {result['name']}: {', '.join(result['issues'])}")
    
    print(f"\n✨ Step 2 Complete! Ready for Step 3: Create Power BI Visuals")

if __name__ == "__main__":
    main()
