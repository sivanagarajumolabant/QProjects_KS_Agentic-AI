"""
Generic Formula Converter - Converts any Tableau calculation to DAX
Handles all types of Tableau formulas including LOD expressions, table calculations, and complex functions.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from ..core.base_converter import BaseConverter
from ..core.config_manager import ConfigManager
from ..core.logger import MigrationLogger
from ..core.exceptions import FormulaConversionException, UnsupportedFunctionException, DAXSyntaxException

class FormulaConverter(BaseConverter):
    """Generic converter for any Tableau formula to DAX"""
    
    def __init__(self, config_manager: ConfigManager, logger: MigrationLogger):
        super().__init__(config_manager, logger)
        self.function_mappings = config_manager.load_function_mappings()
        self.conversion_patterns = self.function_mappings.get('conversion_patterns', {})
        self.complex_conversions = self.function_mappings.get('complex_conversions', {})
        
        # Regex patterns for parsing Tableau formulas
        self.patterns = {
            'function_call': r'([A-Z_]+)\s*\(',
            'field_reference': r'\[([^\]]+)\]',
            'string_literal': r'"([^"]*)"',
            'number_literal': r'\b\d+\.?\d*\b',
            'lod_expression': r'\{(FIXED|INCLUDE|EXCLUDE)\s+([^:]+):\s*([^}]+)\}',
            'if_statement': r'IF\s+(.+?)\s+THEN\s+(.+?)\s+(?:ELSEIF\s+(.+?)\s+THEN\s+(.+?)\s+)*(?:ELSE\s+(.+?)\s+)?END',
            'case_statement': r'CASE\s+(.+?)\s+(?:WHEN\s+(.+?)\s+THEN\s+(.+?)\s+)+(?:ELSE\s+(.+?)\s+)?END'
        }
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate that input is a valid Tableau formula or parsed data structure"""
        if not isinstance(input_data, (str, dict)):
            return False

        if isinstance(input_data, dict):
            # Check if it's a single formula/calculated field
            if 'formula' in input_data or 'calculation' in input_data:
                return True
            # Check if it's a parsed Tableau data structure with calculated fields
            if 'calculated_fields' in input_data:
                return True
            # Check if it has any formula-related content
            return any(key in input_data for key in ['formula', 'calculation', 'calculated_fields'])

        # Basic validation for formula string
        return len(input_data.strip()) > 0
    
    def get_supported_types(self) -> List[str]:
        """Get list of supported formula types"""
        return ['string_formula', 'calculated_field', 'lod_expression', 'table_calculation']
    
    def convert(self, input_data: Any) -> Dict[str, Any]:
        """
        Convert any Tableau formula to DAX

        Args:
            input_data: Tableau formula (string), calculated field (dict), or parsed Tableau data structure

        Returns:
            Dictionary containing DAX formula and conversion metadata
        """
        # Handle parsed Tableau data structure
        if isinstance(input_data, dict) and 'calculated_fields' in input_data:
            return self._convert_calculated_fields_from_parsed_data(input_data)

        # Handle single formula or calculated field
        if isinstance(input_data, dict):
            formula = input_data.get('formula', input_data.get('calculation', ''))
            field_name = input_data.get('name', 'Unknown')
            field_role = input_data.get('role', 'measure')
        else:
            formula = str(input_data)
            field_name = 'Unknown'
            field_role = 'measure'

        return self._convert_single_formula(formula, field_name, field_role)

    def _convert_calculated_fields_from_parsed_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert calculated fields from parsed Tableau data structure"""
        calculated_fields = parsed_data.get('calculated_fields', [])

        if not calculated_fields:
            return {
                'converted_formulas': [],
                'conversion_summary': {
                    'total_fields': 0,
                    'successful_conversions': 0,
                    'failed_conversions': 0
                },
                'original_data': parsed_data
            }

        converted_formulas = []
        successful_conversions = 0
        failed_conversions = 0

        self.log_conversion_step("batch_formula_conversion", {
            'total_calculated_fields': len(calculated_fields)
        })

        for field in calculated_fields:
            try:
                # Convert individual calculated field
                conversion_result = self._convert_single_calculated_field(field)
                converted_formulas.append(conversion_result)

                if conversion_result.get('conversion_success', False):
                    successful_conversions += 1
                else:
                    failed_conversions += 1

            except Exception as e:
                failed_conversions += 1
                error_result = {
                    'field_name': field.get('name', 'Unknown'),
                    'original_formula': field.get('formula', ''),
                    'dax_formula': '',
                    'conversion_success': False,
                    'conversion_issues': [f"Conversion error: {str(e)}"],
                    'field_role': field.get('role', 'measure')
                }
                converted_formulas.append(error_result)

        # Return the enhanced parsed data with converted formulas
        result = parsed_data.copy()
        result['converted_formulas'] = converted_formulas
        result['conversion_summary'] = {
            'total_fields': len(calculated_fields),
            'successful_conversions': successful_conversions,
            'failed_conversions': failed_conversions,
            'success_rate': (successful_conversions / len(calculated_fields)) * 100 if calculated_fields else 0
        }

        return result

    def _convert_single_calculated_field(self, field: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a single calculated field to DAX"""
        formula = field.get('formula', field.get('calculation', ''))
        field_name = field.get('name', 'Unknown')
        field_role = field.get('role', 'measure')

        if not formula:
            return {
                'field_name': field_name,
                'original_formula': '',
                'dax_formula': '',
                'conversion_success': False,
                'conversion_issues': ['No formula found'],
                'field_role': field_role
            }

        # Use the existing single formula conversion logic
        return self._convert_single_formula(formula, field_name, field_role)

    def _convert_single_formula(self, formula: str, field_name: str, field_role: str) -> Dict[str, Any]:
        """Convert a single formula string to DAX"""

        self.log_conversion_step("formula_analysis", {
            'field_name': field_name,
            'original_formula': formula[:100] + '...' if len(formula) > 100 else formula,
            'field_role': field_role
        })

        try:
            # Analyze formula structure
            formula_analysis = self._analyze_formula(formula)

            # Convert based on formula type
            if formula_analysis['type'] == 'lod_expression':
                dax_formula = self._convert_lod_expression(formula, formula_analysis)
            elif formula_analysis['type'] == 'table_calculation':
                dax_formula = self._convert_table_calculation(formula, formula_analysis)
            elif formula_analysis['type'] == 'conditional':
                dax_formula = self._convert_conditional_logic(formula, formula_analysis)
            else:
                dax_formula = self._convert_standard_formula(formula, formula_analysis)

            # Validate DAX syntax
            validation_result = self._validate_dax_syntax(dax_formula)

            conversion_result = {
                'original_formula': formula,
                'dax_formula': dax_formula,
                'field_name': field_name,
                'field_role': field_role,
                'formula_type': formula_analysis['type'],
                'functions_used': formula_analysis['functions'],
                'fields_referenced': formula_analysis['fields'],
                'conversion_success': validation_result['valid'],
                'conversion_issues': validation_result['issues'],
                'conversion_notes': formula_analysis.get('notes', [])
            }

            if conversion_result['conversion_success']:
                self.logger.log_formula_conversion(
                    original_formula=formula,
                    converted_formula=dax_formula,
                    success=True
                )
            else:
                self.logger.log_formula_conversion(
                    original_formula=formula,
                    converted_formula=dax_formula,
                    success=False,
                    issues=validation_result['issues']
                )

            return conversion_result

        except Exception as e:
            error_msg = f"Failed to convert formula: {str(e)}"
            self.logger.log_formula_conversion(
                original_formula=formula,
                converted_formula="",
                success=False,
                issues=[error_msg]
            )

            return {
                'original_formula': formula,
                'dax_formula': "",
                'field_name': field_name,
                'field_role': field_role,
                'formula_type': 'unknown',
                'functions_used': [],
                'fields_referenced': [],
                'conversion_success': False,
                'conversion_issues': [error_msg],
                'conversion_notes': []
            }

    def _analyze_formula(self, formula: str) -> Dict[str, Any]:
        """Analyze Tableau formula structure and components"""
        analysis = {
            'type': 'standard',
            'functions': [],
            'fields': [],
            'literals': [],
            'operators': [],
            'notes': []
        }
        
        # Check for LOD expressions
        lod_matches = re.findall(self.patterns['lod_expression'], formula, re.IGNORECASE)
        if lod_matches:
            analysis['type'] = 'lod_expression'
            analysis['lod_type'] = lod_matches[0][0].upper()
            analysis['lod_dimensions'] = [dim.strip() for dim in lod_matches[0][1].split(',')]
            analysis['lod_expression'] = lod_matches[0][2]
        
        # Check for conditional logic
        elif re.search(self.patterns['if_statement'], formula, re.IGNORECASE):
            analysis['type'] = 'conditional'
            analysis['conditional_type'] = 'if_statement'
        elif re.search(self.patterns['case_statement'], formula, re.IGNORECASE):
            analysis['type'] = 'conditional'
            analysis['conditional_type'] = 'case_statement'
        
        # Check for table calculations
        table_calc_functions = ['RANK', 'RUNNING_SUM', 'RUNNING_AVG', 'WINDOW_SUM', 'WINDOW_AVG', 'LOOKUP', 'PREVIOUS_VALUE']
        for func in table_calc_functions:
            if func in formula.upper():
                analysis['type'] = 'table_calculation'
                analysis['table_calc_type'] = func
                break
        
        # Extract functions
        function_matches = re.findall(self.patterns['function_call'], formula, re.IGNORECASE)
        analysis['functions'] = [func.upper() for func in function_matches]
        
        # Extract field references
        field_matches = re.findall(self.patterns['field_reference'], formula)
        analysis['fields'] = field_matches
        
        # Extract string literals
        string_matches = re.findall(self.patterns['string_literal'], formula)
        analysis['literals'].extend(string_matches)
        
        # Extract number literals
        number_matches = re.findall(self.patterns['number_literal'], formula)
        analysis['literals'].extend(number_matches)
        
        return analysis
    
    def _convert_standard_formula(self, formula: str, analysis: Dict[str, Any]) -> str:
        """Convert standard Tableau formula to DAX"""
        dax_formula = formula
        
        # Convert functions
        for tableau_function in analysis['functions']:
            dax_function = self.config_manager.get_function_mapping(tableau_function)
            if dax_function:
                # Replace function name (case-insensitive)
                pattern = r'\b' + re.escape(tableau_function) + r'\b'
                dax_formula = re.sub(pattern, dax_function, dax_formula, flags=re.IGNORECASE)
            else:
                self.add_warning(f"Unsupported function: {tableau_function}")
        
        # Convert field references
        for field in analysis['fields']:
            # Convert [FieldName] to Table[FieldName] format
            tableau_field = f"[{field}]"
            dax_field = f"Sales[{field}]"  # Default table name - should be dynamic
            dax_formula = dax_formula.replace(tableau_field, dax_field)
        
        # Handle division by zero with DIVIDE function
        if '/' in dax_formula:
            dax_formula = self._convert_division_to_divide(dax_formula)
        
        return dax_formula
    
    def _convert_lod_expression(self, formula: str, analysis: Dict[str, Any]) -> str:
        """Convert Tableau LOD expression to DAX"""
        lod_type = analysis.get('lod_type', 'FIXED')
        dimensions = analysis.get('lod_dimensions', [])
        expression = analysis.get('lod_expression', '')
        
        # Convert the inner expression first
        inner_dax = self._convert_standard_formula(expression, self._analyze_formula(expression))
        
        if lod_type == 'FIXED':
            # {FIXED [Dimension] : SUM([Measure])} -> CALCULATE(SUM(Table[Measure]), ALLEXCEPT(Table, Table[Dimension]))
            if dimensions:
                dimension_refs = ', '.join([f"Sales[{dim.strip('[]')}]" for dim in dimensions])
                dax_formula = f"CALCULATE({inner_dax}, ALLEXCEPT(Sales, {dimension_refs}))"
            else:
                dax_formula = f"CALCULATE({inner_dax}, ALL(Sales))"
        
        elif lod_type == 'INCLUDE':
            # {INCLUDE [Dimension] : AVG([Measure])} -> CALCULATE(AVG(Table[Measure]), VALUES(Table[Dimension]))
            if dimensions:
                dimension_refs = ', '.join([f"VALUES(Sales[{dim.strip('[]')}])" for dim in dimensions])
                dax_formula = f"CALCULATE({inner_dax}, {dimension_refs})"
            else:
                dax_formula = inner_dax
        
        elif lod_type == 'EXCLUDE':
            # {EXCLUDE [Dimension] : COUNT([Field])} -> CALCULATE(COUNT(Table[Field]), ALL(Table[Dimension]))
            if dimensions:
                dimension_refs = ', '.join([f"ALL(Sales[{dim.strip('[]')}])" for dim in dimensions])
                dax_formula = f"CALCULATE({inner_dax}, {dimension_refs})"
            else:
                dax_formula = inner_dax
        
        else:
            dax_formula = inner_dax
        
        return dax_formula
    
    def _convert_table_calculation(self, formula: str, analysis: Dict[str, Any]) -> str:
        """Convert Tableau table calculation to DAX"""
        calc_type = analysis.get('table_calc_type', '')
        
        if calc_type == 'RANK':
            # RANK(SUM([Sales])) -> RANKX(ALL(Table), SUM(Table[Sales]))
            inner_expr = self._extract_function_argument(formula, 'RANK')
            inner_dax = self._convert_standard_formula(inner_expr, self._analyze_formula(inner_expr))
            dax_formula = f"RANKX(ALL(Sales), {inner_dax})"
        
        elif calc_type == 'RUNNING_SUM':
            # RUNNING_SUM(SUM([Sales])) -> CALCULATE(SUM(Table[Sales]), FILTER(ALL(Table), Table[Date] <= EARLIER(Table[Date])))
            inner_expr = self._extract_function_argument(formula, 'RUNNING_SUM')
            inner_dax = self._convert_standard_formula(inner_expr, self._analyze_formula(inner_expr))
            dax_formula = f"CALCULATE({inner_dax}, FILTER(ALL(Sales), Sales[OrderDate] <= EARLIER(Sales[OrderDate])))"
        
        elif calc_type == 'LOOKUP':
            # LOOKUP(SUM([Sales]), -1) -> CALCULATE(SUM(Table[Sales]), FILTER(ALL(Table), Table[Date] = EARLIER(Table[Date]) - 1))
            dax_formula = "LOOKUPVALUE(Sales[SalesAmount], Sales[OrderDate], EARLIER(Sales[OrderDate]) - 1)"
        
        else:
            # Fallback to standard conversion
            dax_formula = self._convert_standard_formula(formula, analysis)
        
        return dax_formula
    
    def _convert_conditional_logic(self, formula: str, analysis: Dict[str, Any]) -> str:
        """Convert Tableau conditional logic (IF/CASE) to DAX"""
        conditional_type = analysis.get('conditional_type', 'if_statement')
        
        if conditional_type == 'if_statement':
            # Convert IF THEN ELSE to DAX IF
            dax_formula = self._convert_if_statement(formula)
        elif conditional_type == 'case_statement':
            # Convert CASE WHEN to DAX SWITCH
            dax_formula = self._convert_case_statement(formula)
        else:
            dax_formula = self._convert_standard_formula(formula, analysis)
        
        return dax_formula
    
    def _convert_if_statement(self, formula: str) -> str:
        """Convert Tableau IF statement to DAX IF"""
        # Simple IF THEN ELSE pattern
        if_pattern = r'IF\s+(.+?)\s+THEN\s+(.+?)\s+ELSE\s+(.+?)\s+END'
        match = re.search(if_pattern, formula, re.IGNORECASE | re.DOTALL)
        
        if match:
            condition = match.group(1).strip()
            true_value = match.group(2).strip()
            false_value = match.group(3).strip()
            
            # Convert field references in condition
            condition = self._convert_field_references(condition)
            true_value = self._convert_field_references(true_value)
            false_value = self._convert_field_references(false_value)
            
            return f"IF({condition}, {true_value}, {false_value})"
        
        return formula
    
    def _convert_case_statement(self, formula: str) -> str:
        """Convert Tableau CASE statement to DAX SWITCH"""
        # This is a simplified conversion - full implementation would handle multiple WHEN clauses
        case_pattern = r'CASE\s+(.+?)\s+WHEN\s+(.+?)\s+THEN\s+(.+?)\s+ELSE\s+(.+?)\s+END'
        match = re.search(case_pattern, formula, re.IGNORECASE | re.DOTALL)
        
        if match:
            field = match.group(1).strip()
            when_value = match.group(2).strip()
            then_value = match.group(3).strip()
            else_value = match.group(4).strip()
            
            # Convert field references
            field = self._convert_field_references(field)
            then_value = self._convert_field_references(then_value)
            else_value = self._convert_field_references(else_value)
            
            return f"SWITCH({field}, {when_value}, {then_value}, {else_value})"
        
        return formula
    
    def _convert_field_references(self, text: str) -> str:
        """Convert [FieldName] references to Table[FieldName] format"""
        field_pattern = r'\[([^\]]+)\]'
        
        def replace_field(match):
            field_name = match.group(1)
            return f"Sales[{field_name}]"  # Default table name - should be dynamic
        
        return re.sub(field_pattern, replace_field, text)
    
    def _convert_division_to_divide(self, formula: str) -> str:
        """Convert division operations to DIVIDE function for safe division"""
        # Simple pattern for A / B -> DIVIDE(A, B, 0)
        division_pattern = r'([^/]+)\s*/\s*([^/]+)'
        
        def replace_division(match):
            numerator = match.group(1).strip()
            denominator = match.group(2).strip()
            return f"DIVIDE({numerator}, {denominator}, 0)"
        
        return re.sub(division_pattern, replace_division, formula)
    
    def _extract_function_argument(self, formula: str, function_name: str) -> str:
        """Extract the argument from a function call"""
        pattern = f'{function_name}\\s*\\(([^)]+)\\)'
        match = re.search(pattern, formula, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""
    
    def _validate_dax_syntax(self, dax_formula: str) -> Dict[str, Any]:
        """Basic validation of DAX syntax"""
        issues = []
        
        # Check for balanced parentheses
        if dax_formula.count('(') != dax_formula.count(')'):
            issues.append("Unbalanced parentheses")
        
        # Check for balanced brackets
        if dax_formula.count('[') != dax_formula.count(']'):
            issues.append("Unbalanced brackets")
        
        # Check for empty formula
        if not dax_formula.strip():
            issues.append("Empty formula")
        
        # Check for common DAX syntax issues
        if '=' in dax_formula and not dax_formula.strip().startswith('='):
            issues.append("Assignment operator found - may need to be comparison")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    def batch_convert_formulas(self, calculated_fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert multiple calculated fields in batch"""
        self.start_conversion("batch_formula_conversion")
        
        results = []
        for field in calculated_fields:
            field_name = field.get('name', 'Unknown')
            result = self.convert_with_error_handling(field, field_name)
            results.append(result)
        
        self.end_conversion("batch_formula_conversion")
        
        return results
