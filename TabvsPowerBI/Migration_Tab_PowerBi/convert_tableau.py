"""
MAIN CONVERSION SCRIPT - Uses Full Migration Engine
Converts any Tableau file using all available capabilities

USAGE: python convert_tableau.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Main conversion using full migration engine"""
    
    print("🚀 TABLEAU TO POWER BI MIGRATION ENGINE")
    print("🔄 Using ALL Available Capabilities")
    print("=" * 60)
    
    # Your Tableau file
    tableau_file = r"C:\QProjects\TabvsPowerBI\tableau_files\sample_sales_report.twb"
    output_name = "full_migration_output"
    
    print(f"📄 Converting: {Path(tableau_file).name}")
    print(f"📁 Source: {tableau_file}")
    print(f"📂 Output: {output_name}")
    
    try:
        # Import the full migration engine
        from src.migration_engine import MigrationEngine
        
        print("\n🏗️ Initializing Migration Engine...")
        engine = MigrationEngine()
        
        # Validate environment
        print("🛡️ Validating Environment...")
        validation = engine.validate_environment()
        
        if validation['environment_valid']:
            print("✅ Environment validation passed")
        else:
            print("⚠️ Environment issues found:")
            for issue in validation.get('issues', []):
                print(f"   - {issue}")
        
        # Show engine capabilities
        print("\n🎯 Engine Capabilities:")
        features = engine.get_supported_features()
        print(f"   📄 File Types: {', '.join(features['file_types'])}")
        print(f"   🎨 Visual Types: {len(features['visual_types'])} types")
        print(f"   🔧 Function Categories: {len(features['function_categories'])} categories")
        print(f"   🔗 Data Sources: {len(features['data_sources'])} connectors")
        
        # Convert the file using FULL capabilities
        print(f"\n🔄 Starting Full Conversion...")
        print("   Using: Parser + Data Converter + Formula Converter + Visual Converter + Power BI Generator")
        
        result = engine.convert_file(tableau_file, output_name=output_name)
        
        if result.success:
            print("\n🎉 CONVERSION SUCCESSFUL!")
            print("=" * 40)
            
            # Show what was generated
            if hasattr(result, 'metadata') and 'generated_files' in result.metadata:
                print("📁 Generated Files:")
                for file_type, file_path in result.metadata['generated_files'].items():
                    if isinstance(file_path, list):
                        for fp in file_path:
                            print(f"   ✅ {file_type}: {Path(fp).name}")
                    else:
                        print(f"   ✅ {file_type}: {Path(file_path).name}")
            
            # Show conversion statistics
            if hasattr(result, 'metadata'):
                metadata = result.metadata
                print(f"\n📊 Conversion Statistics:")
                
                # Data sources
                if 'datasources_converted' in metadata:
                    print(f"   📊 Data Sources: {metadata['datasources_converted']}")
                
                # Visuals
                if 'visuals_converted' in metadata:
                    print(f"   🎨 Visuals: {metadata['visuals_converted']}")
                
                # Formulas
                if 'formulas_converted' in metadata:
                    print(f"   🧮 Formulas: {metadata['formulas_converted']}")
                
                # Pages
                if 'pages_created' in metadata:
                    print(f"   📄 Pages: {metadata['pages_created']}")
            
            print(f"\n🎯 Full Migration Complete!")
            print(f"📂 Check 'output/{output_name}' directory for all files")
            
        else:
            print("\n❌ CONVERSION FAILED!")
            print("=" * 40)
            
            if result.errors:
                print("🔍 Error Details:")
                for error in result.errors:
                    error_type = error.get('exception_type', 'Unknown')
                    error_msg = error.get('message', 'Unknown error')
                    print(f"   ❌ {error_type}: {error_msg}")
            
            print(f"\n💡 Troubleshooting:")
            print(f"   - Check that the Tableau file exists and is readable")
            print(f"   - Verify all migration engine components are working")
            print(f"   - Review error messages above for specific issues")
        
        # Generate migration report
        try:
            print(f"\n📋 Generating Migration Report...")
            summary = engine.get_migration_summary()
            
            print(f"📊 Migration Summary:")
            print(f"   🆔 Session ID: {summary['engine_info']['session_id']}")
            print(f"   📄 Files Processed: {summary['statistics']['files_processed']}")
            print(f"   ✅ Success Rate: {summary['success_rate']:.1f}%")
            print(f"   ⏱️ Processing Time: {summary['statistics'].get('total_processing_time', 'N/A')}")
            
        except Exception as e:
            print(f"⚠️ Could not generate migration report: {e}")
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("💡 Make sure all migration engine components are available")
        print("   Check that src/ directory contains all required files")
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 This indicates an issue with the migration engine")
        print("   Review the error details above for troubleshooting")
    
    print(f"\n" + "=" * 60)
    print(f"🏁 Migration Engine Execution Complete")

if __name__ == "__main__":
    main()
