"""
Generic Tableau to Power BI Migration Engine
Main orchestrator that handles any kind of Tableau report conversion.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .core.config_manager import ConfigManager
from .core.logger import MigrationLogger, ConversionStatus
from .core.exceptions import (
    MigrationException, FileProcessingException, UnsupportedFileTypeException,
    handle_migration_exception, create_error_summary
)
from .core.base_converter import ConversionResult, ConversionPipeline
from .parsers.tableau_parser import TableauParser
from .converters.formula_converter import FormulaConverter

class MigrationEngine:
    """
    Universal Tableau to Power BI Migration Engine
    Handles any kind of Tableau report (.twb, .twbx, .tds, .tdsx) conversion
    """
    
    def __init__(self, config_dir: str = None, log_dir: str = None, 
                 output_dir: str = None):
        """Initialize the migration engine"""
        
        # Set up directories
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = Path(config_dir) if config_dir else self.base_dir / "config"
        self.log_dir = Path(log_dir) if log_dir else self.base_dir / "logs"
        self.output_dir = Path(output_dir) if output_dir else self.base_dir / "output"
        
        # Create directories if they don't exist
        self.log_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize core components
        self.config_manager = ConfigManager(str(self.config_dir))
        self.logger = MigrationLogger(str(self.log_dir))
        
        # Initialize conversion pipeline
        self.pipeline = ConversionPipeline(self.logger)
        
        # Track supported file types
        self.supported_file_types = ['.twb', '.twbx', '.tds', '.tdsx']
        
        # Migration statistics
        self.migration_stats = {
            'files_processed': 0,
            'successful_conversions': 0,
            'failed_conversions': 0,
            'warnings_generated': 0,
            'start_time': None,
            'end_time': None
        }
        
        self.logger.logger.info("🚀 Generic Migration Engine initialized")
        self.logger.logger.info(f"📁 Config directory: {self.config_dir}")
        self.logger.logger.info(f"📁 Output directory: {self.output_dir}")
    
    def convert_file(self, file_path: str, output_name: str = None) -> ConversionResult:
        """
        Convert any Tableau file to Power BI
        
        Args:
            file_path: Path to Tableau file (.twb, .twbx, .tds, .tdsx)
            output_name: Optional custom name for output files
            
        Returns:
            ConversionResult with success status and generated files
        """
        
        self.migration_stats['start_time'] = datetime.now()
        self.migration_stats['files_processed'] += 1
        
        try:
            # Validate input file
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileProcessingException(f"File not found: {file_path}")
            
            if file_path.suffix.lower() not in self.supported_file_types:
                raise UnsupportedFileTypeException(
                    file_path.suffix.lower(), 
                    self.supported_file_types
                )
            
            # Log file analysis start
            file_info = self._analyze_file(file_path)
            self.logger.log_file_analysis(str(file_path), file_info)
            
            # Set up output name
            if output_name is None:
                output_name = file_path.stem
            
            # Create conversion pipeline for this file
            conversion_pipeline = self._create_conversion_pipeline(file_info)
            
            # Execute conversion
            self.logger.log_component_conversion(
                component_type="MigrationEngine",
                component_name="file_conversion",
                status=ConversionStatus.STARTED,
                details={'file_path': str(file_path), 'output_name': output_name}
            )
            
            # Run the conversion pipeline
            result = conversion_pipeline.execute(str(file_path))
            
            if result.success:
                # Generate output files
                output_files = self._generate_output_files(result.data, output_name)
                result.metadata['output_files'] = output_files
                
                self.migration_stats['successful_conversions'] += 1
                self.logger.log_component_conversion(
                    component_type="MigrationEngine",
                    component_name="file_conversion",
                    status=ConversionStatus.COMPLETED,
                    details={'output_files': output_files}
                )
            else:
                self.migration_stats['failed_conversions'] += 1
                self.logger.log_component_conversion(
                    component_type="MigrationEngine",
                    component_name="file_conversion",
                    status=ConversionStatus.FAILED,
                    details={'errors': result.errors}
                )
            
            return result
            
        except MigrationException as e:
            error_info = handle_migration_exception(e, self.logger)
            self.migration_stats['failed_conversions'] += 1
            
            return ConversionResult(
                success=False,
                errors=[error_info],
                metadata={'file_path': str(file_path)}
            )
            
        except Exception as e:
            error_info = {
                'exception_type': type(e).__name__,
                'message': str(e),
                'file_path': str(file_path)
            }
            
            self.logger.log_error(
                error_type="unexpected_error",
                error_message=str(e),
                context=error_info
            )
            
            self.migration_stats['failed_conversions'] += 1
            
            return ConversionResult(
                success=False,
                errors=[error_info],
                metadata={'file_path': str(file_path)}
            )
        
        finally:
            self.migration_stats['end_time'] = datetime.now()
    
    def convert_directory(self, directory_path: str, 
                         file_pattern: str = "*", 
                         recursive: bool = True) -> List[ConversionResult]:
        """
        Convert all Tableau files in a directory
        
        Args:
            directory_path: Path to directory containing Tableau files
            file_pattern: File pattern to match (default: all files)
            recursive: Whether to search subdirectories
            
        Returns:
            List of ConversionResult objects
        """
        
        directory_path = Path(directory_path)
        if not directory_path.exists():
            raise FileProcessingException(f"Directory not found: {directory_path}")
        
        # Find all Tableau files
        tableau_files = []
        search_pattern = f"**/{file_pattern}" if recursive else file_pattern
        
        for file_path in directory_path.glob(search_pattern):
            if file_path.suffix.lower() in self.supported_file_types:
                tableau_files.append(file_path)
        
        self.logger.logger.info(f"📁 Found {len(tableau_files)} Tableau files in {directory_path}")
        
        # Convert each file
        results = []
        for file_path in tableau_files:
            self.logger.logger.info(f"🔄 Converting: {file_path.name}")
            result = self.convert_file(str(file_path))
            results.append(result)
        
        return results
    
    def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze Tableau file and extract basic information"""
        
        file_info = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_type': file_path.suffix.lower(),
            'file_size': file_path.stat().st_size,
            'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
        
        # Determine processing method based on file type
        if file_info['file_type'] in ['.twb', '.tds']:
            file_info['format'] = 'xml'
            file_info['extraction_method'] = 'direct_xml_parse'
        elif file_info['file_type'] in ['.twbx', '.tdsx']:
            file_info['format'] = 'zip_archive'
            file_info['extraction_method'] = 'unzip_then_parse'
        
        return file_info
    
    def _create_conversion_pipeline(self, file_info: Dict[str, Any]) -> ConversionPipeline:
        """Create conversion pipeline based on file type and content"""

        pipeline = ConversionPipeline(self.logger)

        # Add converters based on file type
        if file_info['file_type'] in ['.twb', '.twbx']:
            # Workbook conversion pipeline
            pipeline.add_converter(TableauParser(self.config_manager, self.logger), "parse_tableau")
            pipeline.add_converter(FormulaConverter(self.config_manager, self.logger), "convert_formulas")
            # TODO: Add more converters as they are implemented
            # pipeline.add_converter(DataSourceConverter(self.config_manager, self.logger), "convert_datasources")
            # pipeline.add_converter(VisualConverter(self.config_manager, self.logger), "convert_visuals")
            # pipeline.add_converter(LayoutConverter(self.config_manager, self.logger), "convert_layout")
            # pipeline.add_converter(PowerBIGenerator(self.config_manager, self.logger), "generate_powerbi")
        elif file_info['file_type'] in ['.tds', '.tdsx']:
            # Data source conversion pipeline
            pipeline.add_converter(TableauParser(self.config_manager, self.logger), "parse_tableau")
            pipeline.add_converter(FormulaConverter(self.config_manager, self.logger), "convert_formulas")
            # TODO: Add more converters as they are implemented
            # pipeline.add_converter(DataSourceConverter(self.config_manager, self.logger), "convert_datasources")
            # pipeline.add_converter(PowerBIGenerator(self.config_manager, self.logger), "generate_powerbi")

        return pipeline
    
    def _generate_output_files(self, conversion_data: Any, output_name: str) -> List[str]:
        """Generate Power BI output files from conversion data"""

        output_files = []

        # Create output directory for this conversion
        conversion_output_dir = self.output_dir / output_name
        conversion_output_dir.mkdir(exist_ok=True)

        if conversion_data is None:
            self.logger.logger.warning("No conversion data available - generating placeholder files")
            # Generate placeholder files if no data
            placeholder_files = [
                f"{output_name}_data.csv",
                f"{output_name}_measures.dax",
                f"{output_name}_report_structure.json",
                f"{output_name}_import_instructions.md"
            ]

            for filename in placeholder_files:
                file_path = conversion_output_dir / filename
                file_path.write_text(f"# Placeholder for {filename}\n# Generated by Generic Migration Engine\n")
                output_files.append(str(file_path))
        else:
            # Generate actual output files from conversion data
            output_files.extend(self._generate_data_files(conversion_data, conversion_output_dir, output_name))
            output_files.extend(self._generate_formula_files(conversion_data, conversion_output_dir, output_name))
            output_files.extend(self._generate_structure_files(conversion_data, conversion_output_dir, output_name))
            output_files.extend(self._generate_documentation_files(conversion_data, conversion_output_dir, output_name))

        return output_files

    def _generate_data_files(self, conversion_data: Any, output_dir: Path, output_name: str) -> List[str]:
        """Generate data-related output files"""
        files = []

        # Generate CSV data file if datasources exist
        if hasattr(conversion_data, 'get') and 'datasources' in conversion_data:
            datasources = conversion_data['datasources']
            csv_file = output_dir / f"{output_name}_data_sources.csv"

            import csv
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Data Source Name', 'Caption', 'Connection Type', 'Server',
                    'Database', 'Authentication', 'Table/Schema', 'Columns Count',
                    'Has Data', 'Power BI Connector'
                ])

                # Only process datasources that have actual data
                for ds in datasources:
                    if ds.get('columns') and len(ds.get('columns', [])) > 0:
                        connections = ds.get('connections', [])

                        # Extract connection details
                        server = ''
                        database = ''
                        auth_type = ''
                        conn_type = ''
                        table_info = ''

                        for conn in connections:
                            if conn.get('class') == 'sqlserver':
                                conn_type = 'SQL Server'
                                server = conn.get('server', '')
                                database = conn.get('dbname', '')
                                auth_type = conn.get('authentication', '')

                        # Get table information
                        relations = ds.get('relations', [])
                        if relations:
                            table_info = relations[0].get('table', relations[0].get('name', ''))

                        # Determine Power BI connector
                        powerbi_connector = self._get_powerbi_connector(conn_type)

                        writer.writerow([
                            ds.get('name', ''),
                            ds.get('caption', ''),
                            conn_type,
                            server,
                            database,
                            auth_type,
                            table_info,
                            len(ds.get('columns', [])),
                            'Yes' if ds.get('columns') else 'No',
                            powerbi_connector
                        ])

            files.append(str(csv_file))

            # Try to find and copy sample data file
            sample_data_file = self._find_sample_data_file(conversion_data)
            if sample_data_file:
                copied_data_file = output_dir / f"{output_name}_sample_data.csv"
                import shutil
                shutil.copy2(sample_data_file, copied_data_file)
                files.append(str(copied_data_file))

                # Generate data validation report
                validation_file = self._generate_data_validation_report(
                    conversion_data, sample_data_file, output_dir, output_name
                )
                if validation_file:
                    files.append(validation_file)

        return files

    def _generate_formula_files(self, conversion_data: Any, output_dir: Path, output_name: str) -> List[str]:
        """Generate formula/DAX output files"""
        files = []

        # Generate DAX measures file if converted formulas exist
        if hasattr(conversion_data, 'get') and 'converted_formulas' in conversion_data:
            converted_formulas = conversion_data['converted_formulas']
            dax_file = output_dir / f"{output_name}_measures.dax"

            with open(dax_file, 'w', encoding='utf-8') as f:
                f.write("// DAX Measures converted from Tableau\n")
                f.write("// Generated by Tableau to Power BI Migration Engine\n")
                f.write(f"// Conversion Success Rate: {conversion_data.get('conversion_summary', {}).get('success_rate', 0):.1f}%\n\n")

                for formula_result in converted_formulas:
                    field_name = formula_result.get('field_name', 'Unknown').strip('[]')
                    caption = self._get_field_caption(conversion_data, formula_result.get('field_name', ''))
                    original_formula = formula_result.get('original_formula', '')
                    dax_formula = formula_result.get('dax_formula', '')
                    field_role = formula_result.get('field_role', 'measure')
                    conversion_success = formula_result.get('conversion_success', False)
                    conversion_issues = formula_result.get('conversion_issues', [])

                    # Write measure header
                    f.write(f"// {caption or field_name} ({field_role})\n")
                    f.write(f"// Original Tableau: {original_formula}\n")

                    if conversion_success:
                        f.write(f"[{caption or field_name}] = {dax_formula}\n\n")
                    else:
                        f.write(f"// ⚠️ CONVERSION FAILED - Manual review required\n")
                        f.write(f"// Issues: {', '.join(conversion_issues)}\n")
                        f.write(f"[{caption or field_name}] = \n")
                        f.write(f"    // TODO: Manually convert this formula\n")
                        f.write(f"    // Original: {original_formula}\n\n")

            files.append(str(dax_file))

        # Fallback: Generate from calculated fields if no converted formulas
        elif hasattr(conversion_data, 'get') and 'calculated_fields' in conversion_data:
            calculated_fields = conversion_data['calculated_fields']
            dax_file = output_dir / f"{output_name}_measures.dax"

            with open(dax_file, 'w', encoding='utf-8') as f:
                f.write("// DAX Measures from Tableau (Not Converted)\n")
                f.write("// Generated by Tableau to Power BI Migration Engine\n\n")

                for field in calculated_fields:
                    field_name = field.get('name', 'Unknown').strip('[]')
                    caption = field.get('caption', field_name)
                    formula = field.get('formula', '')
                    f.write(f"// {caption}\n")
                    f.write(f"// Original Tableau: {formula}\n")
                    f.write(f"[{caption}] = \n")
                    f.write(f"    // TODO: Convert this formula to DAX\n")
                    f.write(f"    // Original: {formula}\n\n")

            files.append(str(dax_file))

        return files

    def _get_powerbi_connector(self, connection_type: str) -> str:
        """Map Tableau connection type to Power BI connector"""
        connector_mappings = {
            'SQL Server': 'SQL Server database',
            'Oracle': 'Oracle database',
            'MySQL': 'MySQL database',
            'PostgreSQL': 'PostgreSQL database',
            'Excel': 'Excel workbook',
            'CSV': 'Text/CSV',
            'Snowflake': 'Snowflake',
            'Amazon Redshift': 'Amazon Redshift',
            'Google BigQuery': 'Google BigQuery',
            'Azure SQL Database': 'Azure SQL Database'
        }
        return connector_mappings.get(connection_type, 'Generic connector')

    def _find_sample_data_file(self, conversion_data: Any) -> str:
        """Find sample data file that matches the Tableau data source"""
        # Look for CSV files in the tableau_files directory
        tableau_files_dir = self.base_dir.parent / "tableau_files"

        if tableau_files_dir.exists():
            for csv_file in tableau_files_dir.glob("*.csv"):
                if "sample" in csv_file.name.lower() and "data" in csv_file.name.lower():
                    return str(csv_file)

        return None

    def _generate_data_validation_report(self, conversion_data: Any, sample_data_file: str,
                                       output_dir: Path, output_name: str) -> str:
        """Generate data validation report comparing Tableau schema with sample data"""
        try:
            import pandas as pd

            # Read sample data
            df = pd.read_csv(sample_data_file)

            validation_file = output_dir / f"{output_name}_data_validation.md"

            with open(validation_file, 'w', encoding='utf-8') as f:
                f.write("# Data Validation Report\n\n")
                f.write(f"## Sample Data File: {Path(sample_data_file).name}\n")
                f.write(f"## Records: {len(df)} rows\n\n")

                # Get Tableau columns from parsed data
                tableau_columns = []
                if 'datasources' in conversion_data:
                    for ds in conversion_data['datasources']:
                        if ds.get('columns'):
                            tableau_columns.extend(ds['columns'])

                f.write("## Field Validation\n\n")
                f.write("| Tableau Field | Sample Data Column | Data Type Match | Status |\n")
                f.write("|---------------|-------------------|-----------------|--------|\n")

                csv_columns = df.columns.tolist()

                for col in tableau_columns:
                    tableau_name = col.get('name', '').strip('[]')
                    tableau_type = col.get('datatype', '')

                    if tableau_name in csv_columns:
                        # Check data type compatibility
                        sample_dtype = str(df[tableau_name].dtype)
                        type_match = self._check_type_compatibility(tableau_type, sample_dtype)
                        status = "✅ Match" if type_match else "⚠️ Type Mismatch"
                        f.write(f"| {tableau_name} | {tableau_name} | {tableau_type} → {sample_dtype} | {status} |\n")
                    else:
                        f.write(f"| {tableau_name} | Missing | {tableau_type} | ❌ Not Found |\n")

                # Check for extra columns in CSV
                tableau_field_names = [col.get('name', '').strip('[]') for col in tableau_columns]
                extra_columns = [col for col in csv_columns if col not in tableau_field_names]

                if extra_columns:
                    f.write(f"\n## Extra Columns in Sample Data\n")
                    for col in extra_columns:
                        f.write(f"- {col} ({df[col].dtype})\n")

                # Data quality checks
                f.write(f"\n## Data Quality Summary\n")
                f.write(f"- **Total Records**: {len(df)}\n")
                f.write(f"- **Columns**: {len(df.columns)}\n")
                f.write(f"- **Missing Values**: {df.isnull().sum().sum()}\n")
                f.write(f"- **Duplicate Rows**: {df.duplicated().sum()}\n")

                # Sample data preview
                f.write(f"\n## Sample Data Preview\n")
                f.write("```\n")
                f.write(df.head().to_string())
                f.write("\n```\n")

            return str(validation_file)

        except Exception as e:
            self.logger.logger.warning(f"Could not generate data validation report: {e}")
            return None

    def _check_type_compatibility(self, tableau_type: str, pandas_dtype: str) -> bool:
        """Check if Tableau data type is compatible with pandas dtype"""
        type_mappings = {
            'integer': ['int64', 'int32', 'int16', 'int8'],
            'real': ['float64', 'float32'],
            'string': ['object', 'string'],
            'datetime': ['datetime64', 'object'],
            'boolean': ['bool']
        }

        compatible_types = type_mappings.get(tableau_type.lower(), [])
        return any(dtype in pandas_dtype.lower() for dtype in compatible_types)

    def _get_field_caption(self, conversion_data: Any, field_name: str) -> str:
        """Get the caption for a field from the parsed data"""
        if not hasattr(conversion_data, 'get') or 'calculated_fields' not in conversion_data:
            return field_name.strip('[]')

        for field in conversion_data['calculated_fields']:
            if field.get('name') == field_name:
                return field.get('caption', field_name.strip('[]'))

        return field_name.strip('[]')

    def _generate_structure_files(self, conversion_data: Any, output_dir: Path, output_name: str) -> List[str]:
        """Generate structure/metadata output files"""
        files = []

        # Generate JSON structure file
        json_file = output_dir / f"{output_name}_structure.json"

        import json
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(conversion_data, f, indent=2, default=str)

        files.append(str(json_file))

        return files

    def _generate_documentation_files(self, conversion_data: Any, output_dir: Path, output_name: str) -> List[str]:
        """Generate documentation and instruction files"""
        files = []

        # Generate comprehensive Power BI import guide
        powerbi_guide = output_dir / f"{output_name}_PowerBI_Import_Guide.md"

        with open(powerbi_guide, 'w', encoding='utf-8') as f:
            self._write_powerbi_import_guide(f, conversion_data, output_name)

        files.append(str(powerbi_guide))

        # Generate quick reference card
        quick_ref = output_dir / f"{output_name}_Quick_Reference.md"

        with open(quick_ref, 'w', encoding='utf-8') as f:
            self._write_quick_reference(f, conversion_data, output_name)

        files.append(str(quick_ref))

        return files

    def _write_powerbi_import_guide(self, f, conversion_data: Any, output_name: str):
        """Write comprehensive Power BI import guide"""
        f.write("# 🚀 Power BI Import Guide - Step by Step\n\n")
        f.write(f"**Source Tableau File**: {conversion_data.get('file_info', {}).get('name', 'Unknown')}\n")
        f.write(f"**Generated Files**: {output_name}_*\n")
        f.write(f"**Migration Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        f.write("## 📋 Prerequisites\n")
        f.write("- [ ] Power BI Desktop installed\n")
        f.write("- [ ] Access to the original data source\n")
        f.write("- [ ] Generated migration files from this conversion\n\n")

        f.write("## 🗂️ Generated Files Overview\n")
        f.write(f"- **`{output_name}_measures.dax`** - Ready-to-use DAX formulas\n")
        f.write(f"- **`{output_name}_data_sources.csv`** - Data connection details\n")
        f.write(f"- **`{output_name}_sample_data.csv`** - Sample data for testing\n")
        f.write(f"- **`{output_name}_structure.json`** - Complete Tableau structure\n")
        f.write(f"- **`{output_name}_data_validation.md`** - Data quality report\n\n")

        # Step 1: Data Connection
        f.write("## 📊 Step 1: Connect to Data Source\n\n")

        if 'datasources' in conversion_data:
            for ds in conversion_data['datasources']:
                if ds.get('columns') and len(ds.get('columns', [])) > 0:
                    connections = ds.get('connections', [])
                    for conn in connections:
                        if conn.get('class') == 'sqlserver':
                            f.write("### SQL Server Connection\n")
                            f.write("1. Open Power BI Desktop\n")
                            f.write("2. Click **Get Data** → **SQL Server**\n")
                            f.write(f"3. **Server**: `{conn.get('server', 'sql-server-01')}`\n")
                            f.write(f"4. **Database**: `{conn.get('dbname', 'SalesDB')}`\n")
                            f.write("5. **Authentication**: Windows (if using SSPI)\n")
                            f.write("6. Click **OK** and **Connect**\n")

                            relations = ds.get('relations', [])
                            if relations:
                                table_name = relations[0].get('table', '[dbo].[Sales]')
                                f.write(f"7. Select table: **`{table_name}`**\n")
                            f.write("8. Click **Load**\n\n")
                            break

        # Alternative: Use sample data
        f.write("### Alternative: Use Sample Data (for Testing)\n")
        f.write("1. Click **Get Data** → **Text/CSV**\n")
        f.write(f"2. Browse and select: **`{output_name}_sample_data.csv`**\n")
        f.write("3. Preview the data and click **Load**\n\n")

        # Step 2: Create Measures
        f.write("## 🧮 Step 2: Create DAX Measures\n\n")

        if 'converted_formulas' in conversion_data:
            f.write("### Copy DAX Formulas\n")
            f.write(f"1. Open the file: **`{output_name}_measures.dax`**\n")
            f.write("2. In Power BI, go to **Model** view\n")
            f.write("3. Right-click on your table → **New Measure**\n")
            f.write("4. Copy each DAX formula from the file:\n\n")

            for formula in conversion_data['converted_formulas'][:3]:  # Show first 3 as examples
                field_name = formula.get('field_name', '').strip('[]')
                caption = self._get_field_caption(conversion_data, formula.get('field_name', ''))
                dax_formula = formula.get('dax_formula', '')
                f.write(f"**{caption or field_name}**:\n")
                f.write(f"```dax\n{caption or field_name} = {dax_formula}\n```\n\n")

            if len(conversion_data['converted_formulas']) > 3:
                f.write(f"... and {len(conversion_data['converted_formulas']) - 3} more measures (see the DAX file)\n\n")

        # Step 3: Create Visuals
        f.write("## 📈 Step 3: Recreate Visualizations\n\n")

        if 'worksheets' in conversion_data:
            for i, worksheet in enumerate(conversion_data['worksheets'][:4], 1):  # Show first 4
                ws_name = worksheet.get('name', f'Worksheet {i}')
                f.write(f"### {i}. {ws_name}\n")

                # Determine visual type based on shelves
                shelves = worksheet.get('view', {}).get('shelves', {})
                visual_type = self._determine_visual_type(shelves)

                f.write(f"**Visual Type**: {visual_type}\n\n")
                f.write("**Steps**:\n")
                f.write(f"1. Add a **{visual_type}** to your report canvas\n")

                # Add field mappings
                if 'rows' in shelves and shelves['rows']:
                    rows = ', '.join([self._clean_field_name(field) for field in shelves['rows']])
                    f.write(f"2. **Axis/Rows**: Drag `{rows}` to the axis\n")

                if 'columns' in shelves and shelves['columns']:
                    columns = ', '.join([self._clean_field_name(field) for field in shelves['columns']])
                    f.write(f"3. **Values/Columns**: Drag `{columns}` to values\n")

                if 'color' in shelves and shelves['color']:
                    colors = ', '.join([self._clean_field_name(field) for field in shelves['color']])
                    f.write(f"4. **Legend/Color**: Drag `{colors}` to legend\n")

                f.write("5. Format the visual as needed\n\n")

        # Step 4: Dashboard Layout
        f.write("## 🎨 Step 4: Create Dashboard Layout\n\n")

        if 'dashboards' in conversion_data:
            for dashboard in conversion_data['dashboards']:
                dash_name = dashboard.get('name', 'Dashboard')
                f.write(f"### {dash_name}\n")
                f.write("1. Create a new report page\n")
                f.write("2. Arrange your visuals according to the original layout:\n")

                zones = dashboard.get('zones', [])
                for zone in zones[:3]:  # Show first 3 zones
                    zone_name = zone.get('name', 'Layout Zone')
                    if zone_name:
                        f.write(f"   - **{zone_name}**: Position and size as needed\n")

                f.write("3. Adjust visual sizes and positions\n")
                f.write("4. Apply consistent formatting and colors\n\n")

        # Step 5: Testing and Validation
        f.write("## ✅ Step 5: Testing and Validation\n\n")
        f.write("### Data Validation\n")
        f.write(f"1. Review the **`{output_name}_data_validation.md`** file\n")
        f.write("2. Compare data counts and totals with original Tableau report\n")
        f.write("3. Test all calculated measures with sample data\n\n")

        f.write("### Visual Validation\n")
        f.write("1. Compare each visual with the original Tableau worksheet\n")
        f.write("2. Verify filters and interactions work correctly\n")
        f.write("3. Check formatting, colors, and labels\n\n")

        # Troubleshooting
        f.write("## 🔧 Troubleshooting\n\n")
        f.write("### Common Issues\n")
        f.write("- **DAX Errors**: Check field names match your data model\n")
        f.write("- **Missing Data**: Verify data source connection\n")
        f.write("- **Visual Differences**: Adjust formatting and aggregation settings\n")
        f.write("- **Performance**: Consider data model optimization\n\n")

        f.write("### Need Help?\n")
        f.write("- Review the complete structure in the JSON file\n")
        f.write("- Check Power BI documentation for specific visual types\n")
        f.write("- Test with sample data first before connecting to production\n\n")

        f.write("---\n")
        f.write("*Generated by Tableau to Power BI Migration Engine*\n")

    def _write_quick_reference(self, f, conversion_data: Any, output_name: str):
        """Write quick reference guide"""
        f.write("# 📋 Quick Reference Card\n\n")

        # Data Sources Summary
        if 'datasources' in conversion_data:
            f.write("## 📊 Data Sources\n")
            for ds in conversion_data['datasources']:
                if ds.get('columns') and len(ds.get('columns', [])) > 0:
                    f.write(f"- **{ds.get('caption', ds.get('name', 'Unknown'))}**: {len(ds.get('columns', []))} fields\n")
            f.write("\n")

        # Measures Summary
        if 'converted_formulas' in conversion_data:
            f.write("## 🧮 DAX Measures\n")
            for formula in conversion_data['converted_formulas']:
                field_name = formula.get('field_name', '').strip('[]')
                caption = self._get_field_caption(conversion_data, formula.get('field_name', ''))
                f.write(f"- **{caption or field_name}**: {formula.get('original_formula', '')[:50]}...\n")
            f.write("\n")

        # Worksheets Summary
        if 'worksheets' in conversion_data:
            f.write("## 📈 Visuals to Create\n")
            for worksheet in conversion_data['worksheets']:
                ws_name = worksheet.get('name', 'Unknown')
                shelves = worksheet.get('view', {}).get('shelves', {})
                visual_type = self._determine_visual_type(shelves)
                f.write(f"- **{ws_name}**: {visual_type}\n")
            f.write("\n")

        # File Reference
        f.write("## 📁 File Reference\n")
        f.write(f"- **DAX Measures**: `{output_name}_measures.dax`\n")
        f.write(f"- **Data Connection**: `{output_name}_data_sources.csv`\n")
        f.write(f"- **Sample Data**: `{output_name}_sample_data.csv`\n")
        f.write(f"- **Full Guide**: `{output_name}_PowerBI_Import_Guide.md`\n")

    def _determine_visual_type(self, shelves: Dict[str, Any]) -> str:
        """Determine Power BI visual type based on Tableau shelves"""
        if 'color' in shelves and 'size' in shelves:
            return "Pie Chart"
        elif 'columns' in shelves and 'rows' in shelves:
            if len(shelves.get('columns', [])) == 1 and len(shelves.get('rows', [])) == 1:
                return "Scatter Chart"
            else:
                return "Clustered Column Chart"
        elif 'rows' in shelves and shelves['rows']:
            return "Clustered Bar Chart"
        elif 'columns' in shelves and shelves['columns']:
            return "Line Chart"
        else:
            return "Table"

    def _clean_field_name(self, field_ref: str) -> str:
        """Clean Tableau field reference for display"""
        # Remove datasource prefix and brackets
        if '.' in field_ref:
            field_ref = field_ref.split('.')[-1]
        return field_ref.strip('[]').replace(':', ' ').replace('_', ' ').title()

    def get_migration_summary(self) -> Dict[str, Any]:
        """Get comprehensive migration summary"""
        
        duration = None
        if self.migration_stats['start_time'] and self.migration_stats['end_time']:
            duration = (self.migration_stats['end_time'] - self.migration_stats['start_time']).total_seconds()
        
        success_rate = 0.0
        if self.migration_stats['files_processed'] > 0:
            success_rate = (self.migration_stats['successful_conversions'] / self.migration_stats['files_processed']) * 100
        
        return {
            'engine_info': {
                'version': '1.0.0',
                'session_id': self.logger.get_session_id(),
                'config_dir': str(self.config_dir),
                'output_dir': str(self.output_dir)
            },
            'statistics': self.migration_stats,
            'duration_seconds': duration,
            'success_rate': success_rate,
            'supported_file_types': self.supported_file_types,
            'configuration_status': self.config_manager.validate_configuration()
        }
    
    def validate_environment(self) -> Dict[str, Any]:
        """Validate migration environment and configuration"""
        
        validation_results = {
            'environment_valid': True,
            'issues': [],
            'warnings': []
        }
        
        # Check configuration files
        config_validation = self.config_manager.validate_configuration()
        for config_file, is_valid in config_validation.items():
            if not is_valid:
                validation_results['issues'].append(f"Invalid configuration file: {config_file}")
                validation_results['environment_valid'] = False
        
        # Check directories
        required_dirs = [self.config_dir, self.log_dir, self.output_dir]
        for directory in required_dirs:
            if not directory.exists():
                validation_results['issues'].append(f"Missing directory: {directory}")
                validation_results['environment_valid'] = False
        
        # Check supported features
        supported_versions = self.config_manager.get_supported_tableau_versions()
        supported_visuals = self.config_manager.get_supported_visual_types()
        supported_functions = self.config_manager.get_supported_functions()
        
        validation_results['capabilities'] = {
            'supported_tableau_versions': len(supported_versions),
            'supported_visual_types': len(supported_visuals),
            'supported_function_categories': len(supported_functions)
        }
        
        return validation_results
    
    def get_supported_features(self) -> Dict[str, Any]:
        """Get information about supported features"""
        
        return {
            'file_types': self.supported_file_types,
            'tableau_versions': self.config_manager.get_supported_tableau_versions(),
            'visual_types': self.config_manager.get_supported_visual_types(),
            'function_categories': self.config_manager.get_supported_functions(),
            'data_sources': list(self.config_manager.load_connection_mappings().get('connection_mappings', {}).keys())
        }
    
    def generate_migration_report(self, output_path: str = None) -> str:
        """Generate comprehensive migration report"""
        
        if output_path is None:
            output_path = self.output_dir / f"migration_report_{self.logger.get_session_id()}.json"
        
        # Get comprehensive report data
        report_data = {
            'migration_summary': self.get_migration_summary(),
            'environment_validation': self.validate_environment(),
            'supported_features': self.get_supported_features(),
            'conversion_log': self.logger.generate_conversion_report()
        }
        
        # Save report
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        self.logger.logger.info(f"📊 Migration report saved: {output_path}")
        return str(output_path)
    
    def print_summary(self):
        """Print migration summary to console"""
        
        print("\n" + "="*80)
        print("🎯 GENERIC TABLEAU TO POWER BI MIGRATION ENGINE")
        print("="*80)
        
        summary = self.get_migration_summary()
        
        print(f"Session ID: {summary['engine_info']['session_id']}")
        print(f"Files Processed: {summary['statistics']['files_processed']}")
        print(f"Successful Conversions: {summary['statistics']['successful_conversions']}")
        print(f"Failed Conversions: {summary['statistics']['failed_conversions']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['duration_seconds']:
            print(f"Duration: {summary['duration_seconds']:.2f} seconds")
        
        print(f"\nSupported File Types: {', '.join(summary['supported_file_types'])}")
        print(f"Output Directory: {summary['engine_info']['output_dir']}")
        
        print("="*80)
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - generate final report"""
        if self.migration_stats['files_processed'] > 0:
            self.generate_migration_report()
            self.print_summary()
