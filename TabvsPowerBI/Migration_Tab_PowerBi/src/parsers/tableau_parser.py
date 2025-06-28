"""
Generic Tableau Parser - Handles any Tableau file (.twb, .twbx, .tds, .tdsx)
Extracts metadata from any Tableau workbook or data source automatically.
"""

import xml.etree.ElementTree as ET
import zipfile
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import re

from ..core.base_converter import BaseConverter
from ..core.config_manager import ConfigManager
from ..core.logger import MigrationLogger
from ..core.exceptions import (
    FileProcessingException, CorruptedFileException, 
    TableauVersionException, UnsupportedFileTypeException
)

class TableauParser(BaseConverter):
    """Generic parser for any Tableau file format"""
    
    def __init__(self, config_manager: ConfigManager, logger: MigrationLogger):
        super().__init__(config_manager, logger)
        self.supported_extensions = ['.twb', '.twbx', '.tds', '.tdsx']
        self.xml_namespaces = {
            'user': 'http://www.tableausoftware.com/xml/user'
        }
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate that input is a valid Tableau file path"""
        if not isinstance(input_data, (str, Path)):
            return False
        
        file_path = Path(input_data)
        if not file_path.exists():
            return False
        
        return file_path.suffix.lower() in self.supported_extensions
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported Tableau file types"""
        return self.supported_extensions
    
    def convert(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Parse any Tableau file and extract complete metadata
        
        Args:
            file_path: Path to Tableau file
            
        Returns:
            Dictionary containing all extracted metadata
        """
        file_path = Path(file_path)
        
        self.log_conversion_step("file_analysis", {
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'file_type': file_path.suffix
        })
        
        # Extract XML content based on file type
        if file_path.suffix.lower() in ['.twb', '.tds']:
            xml_content = self._read_xml_file(file_path)
        elif file_path.suffix.lower() in ['.twbx', '.tdsx']:
            xml_content = self._extract_xml_from_archive(file_path)
        else:
            raise UnsupportedFileTypeException(file_path.suffix, self.supported_extensions)
        
        # Parse XML and extract metadata
        root = ET.fromstring(xml_content)
        
        # Detect Tableau version
        version = self._detect_tableau_version(root)
        self.log_conversion_step("version_detection", {'version': version})
        
        # Extract all components
        metadata = {
            'file_info': {
                'path': str(file_path),
                'name': file_path.name,
                'type': file_path.suffix.lower(),
                'size': file_path.stat().st_size
            },
            'tableau_version': version,
            'datasources': self._extract_datasources(root),
            'worksheets': self._extract_worksheets(root),
            'dashboards': self._extract_dashboards(root),
            'parameters': self._extract_parameters(root),
            'calculated_fields': self._extract_calculated_fields(root),
            'filters': self._extract_filters(root),
            'formatting': self._extract_formatting(root)
        }
        
        self.log_conversion_step("metadata_extraction_complete", {
            'datasources_count': len(metadata['datasources']),
            'worksheets_count': len(metadata['worksheets']),
            'dashboards_count': len(metadata['dashboards']),
            'calculated_fields_count': len(metadata['calculated_fields'])
        })
        
        return metadata
    
    def _read_xml_file(self, file_path: Path) -> str:
        """Read XML content from .twb or .tds file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                return f.read()
        except Exception as e:
            raise CorruptedFileException(str(file_path), str(e))
    
    def _extract_xml_from_archive(self, file_path: Path) -> str:
        """Extract XML content from .twbx or .tdsx archive"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Find the main XML file
                xml_files = [f for f in zip_file.namelist() 
                           if f.endswith('.twb') or f.endswith('.tds')]
                
                if not xml_files:
                    raise CorruptedFileException(str(file_path), "No XML file found in archive")
                
                # Read the first XML file found
                with zip_file.open(xml_files[0]) as xml_file:
                    return xml_file.read().decode('utf-8')
                    
        except zipfile.BadZipFile:
            raise CorruptedFileException(str(file_path), "Invalid ZIP archive")
        except Exception as e:
            raise CorruptedFileException(str(file_path), str(e))
    
    def _detect_tableau_version(self, root: ET.Element) -> str:
        """Detect Tableau version from XML"""
        # Try to get version from workbook element
        version = root.get('version', '')
        
        if not version:
            # Try to get from other elements
            version_elements = root.findall('.//version')
            if version_elements:
                version = version_elements[0].text or ''
        
        if not version:
            version = 'unknown'
        
        # Validate version is supported
        version_info = self.config_manager.get_tableau_version_info(version)
        if not version_info.get('supported', True):
            self.add_warning(f"Tableau version {version} may not be fully supported")
        
        return version
    
    def _extract_datasources(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract all data sources from any Tableau file"""
        datasources = []
        
        # Find all datasource elements
        ds_elements = root.findall('.//datasource')
        
        for ds_element in ds_elements:
            datasource = {
                'name': ds_element.get('name', 'Unknown'),
                'caption': ds_element.get('caption', ''),
                'version': ds_element.get('version', ''),
                'inline': ds_element.get('inline', 'false') == 'true',
                'connections': self._extract_connections(ds_element),
                'columns': self._extract_columns(ds_element),
                'relations': self._extract_relations(ds_element),
                'aliases': self._extract_aliases(ds_element)
            }
            datasources.append(datasource)
        
        return datasources
    
    def _extract_connections(self, ds_element: ET.Element) -> List[Dict[str, Any]]:
        """Extract connection information from datasource"""
        connections = []
        
        # Find connection elements
        conn_elements = ds_element.findall('.//connection')
        
        for conn_element in conn_elements:
            connection = {
                'class': conn_element.get('class', ''),
                'server': conn_element.get('server', ''),
                'dbname': conn_element.get('dbname', ''),
                'username': conn_element.get('username', ''),
                'authentication': conn_element.get('authentication', ''),
                'port': conn_element.get('port', ''),
                'schema': conn_element.get('schema', ''),
                'warehouse': conn_element.get('warehouse', ''),
                'service': conn_element.get('service', ''),
                'filename': conn_element.get('filename', ''),
                'directory': conn_element.get('directory', ''),
                'properties': {attr: value for attr, value in conn_element.attrib.items()}
            }
            connections.append(connection)
        
        return connections
    
    def _extract_columns(self, ds_element: ET.Element) -> List[Dict[str, Any]]:
        """Extract column/field definitions from datasource"""
        columns = []
        
        # Find column elements
        col_elements = ds_element.findall('.//column')
        
        for col_element in col_elements:
            column = {
                'name': col_element.get('name', ''),
                'caption': col_element.get('caption', ''),
                'datatype': col_element.get('datatype', ''),
                'role': col_element.get('role', ''),
                'type': col_element.get('type', ''),
                'aggregation': col_element.get('aggregation', ''),
                'hidden': col_element.get('hidden', 'false') == 'true',
                'calculation': self._extract_calculation(col_element),
                'default_format': col_element.get('default-format', ''),
                'semantic_role': col_element.get('semantic-role', ''),
                'geographic_role': col_element.get('geographic-role', '')
            }
            columns.append(column)
        
        return columns
    
    def _extract_calculation(self, col_element: ET.Element) -> Optional[Dict[str, Any]]:
        """Extract calculation formula from column element"""
        calc_element = col_element.find('calculation')
        if calc_element is not None:
            return {
                'class': calc_element.get('class', ''),
                'formula': calc_element.get('formula', ''),
                'formula_text': calc_element.text or ''
            }
        return None
    
    def _extract_relations(self, ds_element: ET.Element) -> List[Dict[str, Any]]:
        """Extract table relations and joins"""
        relations = []
        
        # Find relation elements
        rel_elements = ds_element.findall('.//relation')
        
        for rel_element in rel_elements:
            relation = {
                'connection': rel_element.get('connection', ''),
                'name': rel_element.get('name', ''),
                'table': rel_element.get('table', ''),
                'type': rel_element.get('type', ''),
                'join': rel_element.get('join', ''),
                'text': rel_element.text or ''
            }
            relations.append(relation)
        
        return relations
    
    def _extract_aliases(self, ds_element: ET.Element) -> Dict[str, str]:
        """Extract field aliases"""
        aliases = {}
        
        # Find aliases element
        aliases_element = ds_element.find('aliases')
        if aliases_element is not None:
            for alias in aliases_element.findall('alias'):
                key = alias.get('key', '')
                value = alias.get('value', '')
                if key and value:
                    aliases[key] = value
        
        return aliases
    
    def _extract_worksheets(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract all worksheets from workbook"""
        worksheets = []
        
        # Find worksheets container
        worksheets_element = root.find('worksheets')
        if worksheets_element is None:
            return worksheets
        
        # Find all worksheet elements
        ws_elements = worksheets_element.findall('worksheet')
        
        for ws_element in ws_elements:
            worksheet = {
                'name': ws_element.get('name', ''),
                'view': self._extract_view(ws_element),
                'table': self._extract_table_config(ws_element),
                'style': self._extract_style(ws_element)
            }
            worksheets.append(worksheet)
        
        return worksheets
    
    def _extract_view(self, ws_element: ET.Element) -> Dict[str, Any]:
        """Extract view configuration from worksheet"""
        view_element = ws_element.find('.//view')
        if view_element is None:
            return {}
        
        return {
            'datasources': self._extract_view_datasources(view_element),
            'shelves': self._extract_shelves(view_element),
            'filters': self._extract_view_filters(view_element),
            'sorts': self._extract_sorts(view_element),
            'marks': self._extract_marks(view_element)
        }
    
    def _extract_shelves(self, view_element: ET.Element) -> Dict[str, List[str]]:
        """Extract field assignments to shelves (rows, columns, color, etc.)"""
        shelves = {}
        
        shelves_element = view_element.find('shelves')
        if shelves_element is not None:
            for shelf in shelves_element.findall('shelf'):
                shelf_name = shelf.get('name', '')
                fields = [field.text for field in shelf.findall('field') if field.text]
                shelves[shelf_name] = fields
        
        return shelves
    
    def _extract_view_datasources(self, view_element: ET.Element) -> List[str]:
        """Extract datasource references from view"""
        datasources = []
        
        ds_element = view_element.find('datasources')
        if ds_element is not None:
            for ds in ds_element.findall('datasource'):
                name = ds.get('name', '')
                if name:
                    datasources.append(name)
        
        return datasources
    
    def _extract_view_filters(self, view_element: ET.Element) -> List[Dict[str, Any]]:
        """Extract filters from view"""
        # This will be implemented based on filter structure
        return []
    
    def _extract_sorts(self, view_element: ET.Element) -> List[Dict[str, Any]]:
        """Extract sort configurations"""
        sorts = []
        
        sorts_element = view_element.find('shelf-sorts')
        if sorts_element is not None:
            for sort in sorts_element.findall('shelf-sort-rule'):
                sort_config = {
                    'field': sort.get('field', ''),
                    'ascending': sort.get('is-ascending', 'true') == 'true'
                }
                sorts.append(sort_config)
        
        return sorts
    
    def _extract_marks(self, view_element: ET.Element) -> Dict[str, Any]:
        """Extract mark configuration"""
        # This will be implemented based on marks structure
        return {}
    
    def _extract_table_config(self, ws_element: ET.Element) -> Dict[str, Any]:
        """Extract table configuration from worksheet"""
        # This will be implemented based on table structure
        return {}
    
    def _extract_style(self, ws_element: ET.Element) -> Dict[str, Any]:
        """Extract style/formatting from worksheet"""
        # This will be implemented based on style structure
        return {}
    
    def _extract_dashboards(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract all dashboards from workbook"""
        dashboards = []
        
        # Find dashboards container
        dashboards_element = root.find('dashboards')
        if dashboards_element is None:
            return dashboards
        
        # Find all dashboard elements
        db_elements = dashboards_element.findall('dashboard')
        
        for db_element in db_elements:
            dashboard = {
                'name': db_element.get('name', ''),
                'size': self._extract_dashboard_size(db_element),
                'zones': self._extract_zones(db_element),
                'device_layouts': self._extract_device_layouts(db_element)
            }
            dashboards.append(dashboard)
        
        return dashboards
    
    def _extract_dashboard_size(self, db_element: ET.Element) -> Dict[str, Any]:
        """Extract dashboard size configuration"""
        size_element = db_element.find('size')
        if size_element is not None:
            return {
                'maxheight': size_element.get('maxheight', ''),
                'maxwidth': size_element.get('maxwidth', ''),
                'minheight': size_element.get('minheight', ''),
                'minwidth': size_element.get('minwidth', '')
            }
        return {}
    
    def _extract_zones(self, db_element: ET.Element) -> List[Dict[str, Any]]:
        """Extract dashboard zones/layout"""
        zones = []
        
        zones_element = db_element.find('zones')
        if zones_element is not None:
            for zone in zones_element.findall('zone'):
                zone_config = {
                    'id': zone.get('id', ''),
                    'name': zone.get('name', ''),
                    'type': zone.get('type', ''),
                    'param': zone.get('param', ''),
                    'x': zone.get('x', ''),
                    'y': zone.get('y', ''),
                    'w': zone.get('w', ''),
                    'h': zone.get('h', '')
                }
                zones.append(zone_config)
        
        return zones
    
    def _extract_device_layouts(self, db_element: ET.Element) -> List[Dict[str, Any]]:
        """Extract device-specific layouts"""
        # This will be implemented based on device layout structure
        return []
    
    def _extract_parameters(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract parameters from any Tableau file"""
        parameters = []
        
        # Parameters are usually defined as columns with param-domain-type
        param_elements = root.findall('.//column[@param-domain-type]')
        
        for param_element in param_elements:
            parameter = {
                'name': param_element.get('name', ''),
                'caption': param_element.get('caption', ''),
                'datatype': param_element.get('datatype', ''),
                'param_domain_type': param_element.get('param-domain-type', ''),
                'value': param_element.get('value', ''),
                'members': self._extract_parameter_members(param_element)
            }
            parameters.append(parameter)
        
        return parameters
    
    def _extract_parameter_members(self, param_element: ET.Element) -> List[Dict[str, str]]:
        """Extract parameter member values"""
        members = []
        
        members_element = param_element.find('members')
        if members_element is not None:
            for member in members_element.findall('member'):
                member_info = {
                    'alias': member.get('alias', ''),
                    'value': member.get('value', '')
                }
                members.append(member_info)
        
        return members
    
    def _extract_calculated_fields(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract all calculated fields from any Tableau file"""
        calculated_fields = []
        
        # Find all columns with calculations
        calc_elements = root.findall('.//column[calculation]')
        
        for calc_element in calc_elements:
            calculation = calc_element.find('calculation')
            if calculation is not None:
                calc_field = {
                    'name': calc_element.get('name', ''),
                    'caption': calc_element.get('caption', ''),
                    'datatype': calc_element.get('datatype', ''),
                    'role': calc_element.get('role', ''),
                    'type': calc_element.get('type', ''),
                    'formula': calculation.get('formula', ''),
                    'class': calculation.get('class', ''),
                    'formula_text': calculation.text or ''
                }
                calculated_fields.append(calc_field)
        
        return calculated_fields
    
    def _extract_filters(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract filters from any Tableau file"""
        # This will be implemented based on filter structure
        return []
    
    def _extract_formatting(self, root: ET.Element) -> Dict[str, Any]:
        """Extract formatting information"""
        # This will be implemented based on formatting structure
        return {}
