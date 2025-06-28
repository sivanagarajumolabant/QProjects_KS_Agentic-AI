"""
Step 3: Create Power BI Visuals
This script creates Power BI visual configurations that match the original Tableau worksheets.
"""

import json
import os
from datetime import datetime

def load_conversion_data():
    """Load data from previous steps"""
    try:
        # Load dataset metadata
        with open('powerbi_output/dataset_metadata.json', 'r') as f:
            dataset_metadata = json.load(f)
        
        # Load DAX conversion results
        with open('powerbi_output/dax_conversion_results.json', 'r') as f:
            dax_results = json.load(f)
        
        print("✅ Loaded conversion data from previous steps")
        return dataset_metadata, dax_results
    except Exception as e:
        print(f"❌ Error loading conversion data: {e}")
        return None, None

def analyze_tableau_worksheets():
    """Analyze the original Tableau worksheets to understand visual requirements"""
    
    # Based on our sample_sales_report.twb analysis
    tableau_worksheets = [
        {
            'name': 'Sales by Region',
            'type': 'bar_chart',
            'orientation': 'horizontal',
            'fields': {
                'rows': ['Region'],
                'columns': ['SUM(SalesAmount)'],
                'color': ['Region']
            },
            'sorting': {
                'field': 'SUM(SalesAmount)',
                'direction': 'descending'
            },
            'colors': {
                'East': '#1f77b4',
                'North': '#ff7f0e', 
                'South': '#2ca02c',
                'West': '#d62728'
            }
        },
        {
            'name': 'Sales Trend',
            'type': 'line_chart',
            'fields': {
                'columns': ['MONTH(OrderDate)'],
                'rows': ['SUM(SalesAmount)']
            },
            'sorting': {
                'field': 'MONTH(OrderDate)',
                'direction': 'ascending'
            },
            'colors': {
                'line': '#1f77b4'
            }
        },
        {
            'name': 'Category Performance',
            'type': 'pie_chart',
            'fields': {
                'color': ['Category'],
                'size': ['SUM(SalesAmount)']
            },
            'colors': {
                'Electronics': '#1f77b4',
                'Furniture': '#ff7f0e',
                'Office Supplies': '#2ca02c'
            }
        },
        {
            'name': 'Profit Analysis',
            'type': 'scatter_plot',
            'fields': {
                'columns': ['SUM(SalesAmount)'],
                'rows': ['SUM(Profit)'],
                'color': ['Category']
            }
        }
    ]
    
    return tableau_worksheets

def create_powerbi_visual_configs(tableau_worksheets, dax_results):
    """Convert Tableau worksheet configurations to Power BI visual configurations"""
    
    powerbi_visuals = []
    
    for worksheet in tableau_worksheets:
        if worksheet['type'] == 'bar_chart':
            visual = create_bar_chart_config(worksheet, dax_results)
        elif worksheet['type'] == 'line_chart':
            visual = create_line_chart_config(worksheet, dax_results)
        elif worksheet['type'] == 'pie_chart':
            visual = create_pie_chart_config(worksheet, dax_results)
        elif worksheet['type'] == 'scatter_plot':
            visual = create_scatter_plot_config(worksheet, dax_results)
        
        powerbi_visuals.append(visual)
    
    return powerbi_visuals

def create_bar_chart_config(worksheet, dax_results):
    """Create Power BI clustered bar chart configuration"""
    
    config = {
        'name': worksheet['name'],
        'type': 'clusteredBarChart',
        'title': worksheet['name'],
        'data_fields': {
            'category': ['Region'],
            'values': ['Total Sales']  # Using our DAX measure
        },
        'formatting': {
            'data_colors': worksheet.get('colors', {}),
            'show_data_labels': True,
            'legend_position': 'Right',
            'x_axis_title': 'Sales Amount',
            'y_axis_title': 'Region'
        },
        'interactions': {
            'cross_filter': True,
            'cross_highlight': True
        },
        'sorting': {
            'field': 'Total Sales',
            'direction': 'Descending'
        }
    }
    
    return config

def create_line_chart_config(worksheet, dax_results):
    """Create Power BI line chart configuration"""
    
    config = {
        'name': worksheet['name'],
        'type': 'lineChart',
        'title': worksheet['name'],
        'data_fields': {
            'axis': ['OrderDate'],  # Will use date hierarchy
            'values': ['Total Sales']
        },
        'formatting': {
            'line_color': worksheet['colors']['line'],
            'show_data_labels': False,
            'legend_position': 'None',
            'x_axis_title': 'Order Date',
            'y_axis_title': 'Sales Amount'
        },
        'interactions': {
            'cross_filter': True,
            'cross_highlight': True
        },
        'date_hierarchy': {
            'level': 'Month',
            'auto_date_hierarchy': True
        }
    }
    
    return config

def create_pie_chart_config(worksheet, dax_results):
    """Create Power BI pie chart configuration"""
    
    config = {
        'name': worksheet['name'],
        'type': 'pieChart',
        'title': worksheet['name'],
        'data_fields': {
            'legend': ['Category'],
            'values': ['Total Sales']
        },
        'formatting': {
            'data_colors': worksheet.get('colors', {}),
            'show_data_labels': True,
            'legend_position': 'Right',
            'detail_labels': 'Category'
        },
        'interactions': {
            'cross_filter': True,
            'cross_highlight': True
        }
    }
    
    return config

def create_scatter_plot_config(worksheet, dax_results):
    """Create Power BI scatter chart configuration"""
    
    config = {
        'name': worksheet['name'],
        'type': 'scatterChart',
        'title': worksheet['name'],
        'data_fields': {
            'x_axis': ['Total Sales'],
            'y_axis': ['Total Profit'],
            'legend': ['Category'],
            'size': ['Total Quantity']  # Optional: size by quantity
        },
        'formatting': {
            'data_colors': {
                'Electronics': '#1f77b4',
                'Furniture': '#ff7f0e',
                'Office Supplies': '#2ca02c'
            },
            'show_data_labels': False,
            'legend_position': 'Right',
            'x_axis_title': 'Sales Amount',
            'y_axis_title': 'Profit'
        },
        'interactions': {
            'cross_filter': True,
            'cross_highlight': True
        }
    }
    
    return config

def create_dashboard_layout():
    """Create Power BI dashboard layout matching Tableau dashboard"""
    
    # Based on the Tableau dashboard structure
    dashboard_config = {
        'name': 'Sales Dashboard',
        'page_size': {
            'width': 1280,
            'height': 720,
            'type': '16:9'
        },
        'layout': {
            'type': 'grid',
            'sections': [
                {
                    'name': 'top_section',
                    'position': {'x': 0, 'y': 0, 'width': 1280, 'height': 360},
                    'visual': 'Sales by Region'
                },
                {
                    'name': 'bottom_left',
                    'position': {'x': 0, 'y': 360, 'width': 640, 'height': 360},
                    'visual': 'Sales Trend'
                },
                {
                    'name': 'bottom_right',
                    'position': {'x': 640, 'y': 360, 'width': 640, 'height': 360},
                    'visual': 'Category Performance'
                }
            ]
        },
        'additional_pages': [
            {
                'name': 'Detailed Analysis',
                'visuals': ['Profit Analysis']
            }
        ],
        'filters': {
            'page_level': ['Region', 'Category'],
            'report_level': ['Year']
        }
    }
    
    return dashboard_config

def create_filter_configurations():
    """Create filter and slicer configurations"""
    
    filters = [
        {
            'name': 'Region Filter',
            'type': 'slicer',
            'field': 'Region',
            'style': 'dropdown',
            'default_selection': 'All',
            'position': {'x': 20, 'y': 20, 'width': 200, 'height': 100}
        },
        {
            'name': 'Category Filter',
            'type': 'slicer',
            'field': 'Category',
            'style': 'list',
            'multi_select': True,
            'position': {'x': 240, 'y': 20, 'width': 200, 'height': 100}
        },
        {
            'name': 'Date Range',
            'type': 'date_slicer',
            'field': 'OrderDate',
            'style': 'between',
            'position': {'x': 460, 'y': 20, 'width': 300, 'height': 100}
        }
    ]
    
    return filters

def generate_powerbi_report_json(visuals, dashboard, filters):
    """Generate Power BI report JSON structure"""
    
    report_structure = {
        'version': '1.0',
        'report_info': {
            'name': 'Sales Report - Converted from Tableau',
            'description': 'Migrated from Tableau sample_sales_report.twb',
            'created_date': datetime.now().isoformat(),
            'author': 'Tableau to Power BI Migration Engine'
        },
        'dataset': {
            'name': 'Sales Data',
            'connection_type': 'CSV',
            'refresh_schedule': 'Daily'
        },
        'pages': [
            {
                'name': dashboard['name'],
                'display_name': dashboard['name'],
                'width': dashboard['page_size']['width'],
                'height': dashboard['page_size']['height'],
                'visuals': visuals[:3],  # First 3 visuals on main dashboard
                'filters': filters
            },
            {
                'name': 'Detailed Analysis',
                'display_name': 'Detailed Analysis',
                'width': 1280,
                'height': 720,
                'visuals': visuals[3:],  # Remaining visuals
                'filters': filters
            }
        ],
        'interactions': {
            'cross_filter_enabled': True,
            'cross_highlight_enabled': True,
            'drill_through_enabled': True
        }
    }
    
    return report_structure

def save_visual_configurations(visuals, dashboard, filters, report_structure):
    """Save all visual configurations and report structure"""
    
    # Create comprehensive visual configuration
    visual_config = {
        'conversion_info': {
            'step': 'Step 3 - Visual Creation',
            'created_date': datetime.now().isoformat(),
            'total_visuals': len(visuals),
            'dashboard_pages': len(report_structure['pages'])
        },
        'visuals': visuals,
        'dashboard_layout': dashboard,
        'filters': filters,
        'report_structure': report_structure
    }
    
    # Save visual configurations
    with open('powerbi_output/visual_configurations.json', 'w') as f:
        json.dump(visual_config, f, indent=2)
    
    # Save Power BI report structure
    with open('powerbi_output/powerbi_report_structure.json', 'w') as f:
        json.dump(report_structure, f, indent=2)
    
    print("✅ Visual configurations saved!")
    print("📁 Files created:")
    print("   - powerbi_output/visual_configurations.json")
    print("   - powerbi_output/powerbi_report_structure.json")

def main():
    """Main function to execute Step 3"""
    print("🚀 Step 3: Creating Power BI Visuals")
    print("=" * 50)
    
    # Load conversion data from previous steps
    dataset_metadata, dax_results = load_conversion_data()
    if dataset_metadata is None or dax_results is None:
        return
    
    # Analyze original Tableau worksheets
    print("📊 Analyzing Tableau worksheets...")
    tableau_worksheets = analyze_tableau_worksheets()
    print(f"   Found {len(tableau_worksheets)} worksheets to convert")
    
    # Create Power BI visual configurations
    print("🎨 Creating Power BI visual configurations...")
    powerbi_visuals = create_powerbi_visual_configs(tableau_worksheets, dax_results)
    
    # Create dashboard layout
    print("📋 Creating dashboard layout...")
    dashboard_config = create_dashboard_layout()
    
    # Create filter configurations
    print("🔍 Creating filter configurations...")
    filter_configs = create_filter_configurations()
    
    # Generate complete report structure
    print("📝 Generating Power BI report structure...")
    report_structure = generate_powerbi_report_json(powerbi_visuals, dashboard_config, filter_configs)
    
    # Save all configurations
    print("💾 Saving visual configurations...")
    save_visual_configurations(powerbi_visuals, dashboard_config, filter_configs, report_structure)
    
    # Display summary
    print(f"\n📈 Visual Creation Summary:")
    print(f"   Power BI Visuals: {len(powerbi_visuals)}")
    print(f"   Dashboard Pages: {len(report_structure['pages'])}")
    print(f"   Filters/Slicers: {len(filter_configs)}")
    
    print(f"\n📊 Visual Types Created:")
    for visual in powerbi_visuals:
        print(f"   - {visual['name']}: {visual['type']}")
    
    print(f"\n✨ Step 3 Complete! Ready for Step 4: Build Power BI Report")

if __name__ == "__main__":
    main()
