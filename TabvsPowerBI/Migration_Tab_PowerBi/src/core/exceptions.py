"""
Custom Exceptions for Generic Tableau to Power BI Migration Engine
Provides specific exception types for different migration scenarios.
"""

from typing import Dict, Any, List, Optional

class MigrationException(Exception):
    """Base exception for all migration-related errors"""
    
    def __init__(self, message: str, context: Dict[str, Any] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)
    
    def get_context(self) -> Dict[str, Any]:
        """Get error context information"""
        return self.context
    
    def get_detailed_message(self) -> str:
        """Get detailed error message with context"""
        if self.context:
            context_str = ", ".join([f"{k}: {v}" for k, v in self.context.items()])
            return f"{self.message} (Context: {context_str})"
        return self.message

class FileProcessingException(MigrationException):
    """Exception for file processing errors"""
    
    def __init__(self, message: str, file_path: str = None, file_type: str = None):
        context = {}
        if file_path:
            context['file_path'] = file_path
        if file_type:
            context['file_type'] = file_type
        super().__init__(message, context)

class UnsupportedFileTypeException(FileProcessingException):
    """Exception for unsupported file types"""
    
    def __init__(self, file_type: str, supported_types: List[str] = None):
        message = f"Unsupported file type: {file_type}"
        if supported_types:
            message += f". Supported types: {', '.join(supported_types)}"
        super().__init__(message, file_type=file_type)

class CorruptedFileException(FileProcessingException):
    """Exception for corrupted or invalid files"""
    
    def __init__(self, file_path: str, reason: str = None):
        message = f"Corrupted or invalid file: {file_path}"
        if reason:
            message += f". Reason: {reason}"
        super().__init__(message, file_path=file_path)

class TableauVersionException(MigrationException):
    """Exception for Tableau version compatibility issues"""
    
    def __init__(self, version: str, supported_versions: List[str] = None):
        message = f"Unsupported Tableau version: {version}"
        if supported_versions:
            message += f". Supported versions: {', '.join(supported_versions)}"
        context = {'tableau_version': version, 'supported_versions': supported_versions}
        super().__init__(message, context)

class DataSourceException(MigrationException):
    """Exception for data source conversion errors"""
    
    def __init__(self, message: str, source_type: str = None, connection_details: Dict[str, Any] = None):
        context = {}
        if source_type:
            context['source_type'] = source_type
        if connection_details:
            context['connection_details'] = connection_details
        super().__init__(message, context)

class UnsupportedDataSourceException(DataSourceException):
    """Exception for unsupported data source types"""
    
    def __init__(self, source_type: str, supported_types: List[str] = None):
        message = f"Unsupported data source type: {source_type}"
        if supported_types:
            message += f". Supported types: {', '.join(supported_types)}"
        super().__init__(message, source_type=source_type)

class FormulaConversionException(MigrationException):
    """Exception for formula conversion errors"""
    
    def __init__(self, message: str, original_formula: str = None, 
                 tableau_function: str = None, conversion_issues: List[str] = None):
        context = {}
        if original_formula:
            context['original_formula'] = original_formula
        if tableau_function:
            context['tableau_function'] = tableau_function
        if conversion_issues:
            context['conversion_issues'] = conversion_issues
        super().__init__(message, context)

class UnsupportedFunctionException(FormulaConversionException):
    """Exception for unsupported Tableau functions"""
    
    def __init__(self, function_name: str, supported_functions: List[str] = None):
        message = f"Unsupported Tableau function: {function_name}"
        if supported_functions:
            message += f". Supported functions: {', '.join(supported_functions[:10])}"
            if len(supported_functions) > 10:
                message += "..."
        super().__init__(message, tableau_function=function_name)

class DAXSyntaxException(FormulaConversionException):
    """Exception for DAX syntax errors"""
    
    def __init__(self, dax_formula: str, syntax_errors: List[str]):
        message = f"Invalid DAX syntax in formula: {dax_formula[:100]}..."
        context = {
            'dax_formula': dax_formula,
            'syntax_errors': syntax_errors
        }
        super().__init__(message, **context)

class VisualConversionException(MigrationException):
    """Exception for visual conversion errors"""
    
    def __init__(self, message: str, visual_type: str = None, worksheet_name: str = None,
                 visual_config: Dict[str, Any] = None):
        context = {}
        if visual_type:
            context['visual_type'] = visual_type
        if worksheet_name:
            context['worksheet_name'] = worksheet_name
        if visual_config:
            context['visual_config'] = visual_config
        super().__init__(message, context)

class UnsupportedVisualTypeException(VisualConversionException):
    """Exception for unsupported visual types"""
    
    def __init__(self, visual_type: str, supported_types: List[str] = None):
        message = f"Unsupported visual type: {visual_type}"
        if supported_types:
            message += f". Supported types: {', '.join(supported_types)}"
        super().__init__(message, visual_type=visual_type)

class LayoutConversionException(MigrationException):
    """Exception for dashboard layout conversion errors"""
    
    def __init__(self, message: str, dashboard_name: str = None, 
                 layout_config: Dict[str, Any] = None):
        context = {}
        if dashboard_name:
            context['dashboard_name'] = dashboard_name
        if layout_config:
            context['layout_config'] = layout_config
        super().__init__(message, context)

class ValidationException(MigrationException):
    """Exception for validation errors"""
    
    def __init__(self, message: str, validation_type: str = None, 
                 component: str = None, validation_errors: List[str] = None):
        context = {}
        if validation_type:
            context['validation_type'] = validation_type
        if component:
            context['component'] = component
        if validation_errors:
            context['validation_errors'] = validation_errors
        super().__init__(message, context)

class DataValidationException(ValidationException):
    """Exception for data validation errors"""
    
    def __init__(self, message: str, expected_value: Any = None, 
                 actual_value: Any = None, field_name: str = None):
        context = {}
        if expected_value is not None:
            context['expected_value'] = expected_value
        if actual_value is not None:
            context['actual_value'] = actual_value
        if field_name:
            context['field_name'] = field_name
        super().__init__(message, validation_type="data_validation", **context)

class ConfigurationException(MigrationException):
    """Exception for configuration errors"""
    
    def __init__(self, message: str, config_file: str = None, 
                 missing_keys: List[str] = None):
        context = {}
        if config_file:
            context['config_file'] = config_file
        if missing_keys:
            context['missing_keys'] = missing_keys
        super().__init__(message, context)

class PowerBIGenerationException(MigrationException):
    """Exception for Power BI file generation errors"""
    
    def __init__(self, message: str, generation_type: str = None, 
                 output_format: str = None):
        context = {}
        if generation_type:
            context['generation_type'] = generation_type
        if output_format:
            context['output_format'] = output_format
        super().__init__(message, context)

class PerformanceException(MigrationException):
    """Exception for performance-related issues"""
    
    def __init__(self, message: str, operation: str = None, 
                 duration_seconds: float = None, memory_usage_mb: float = None):
        context = {}
        if operation:
            context['operation'] = operation
        if duration_seconds:
            context['duration_seconds'] = duration_seconds
        if memory_usage_mb:
            context['memory_usage_mb'] = memory_usage_mb
        super().__init__(message, context)

# Exception handling utilities

def handle_migration_exception(exception: MigrationException, logger=None) -> Dict[str, Any]:
    """Handle migration exception and return error information"""
    error_info = {
        'exception_type': type(exception).__name__,
        'message': exception.message,
        'context': exception.get_context(),
        'detailed_message': exception.get_detailed_message()
    }
    
    if logger:
        logger.log_error(
            error_type=error_info['exception_type'],
            error_message=error_info['message'],
            context=error_info['context']
        )
    
    return error_info

def create_error_summary(exceptions: List[MigrationException]) -> Dict[str, Any]:
    """Create summary of multiple exceptions"""
    if not exceptions:
        return {'total_errors': 0, 'error_types': {}, 'critical_errors': []}
    
    error_types = {}
    critical_errors = []
    
    for exc in exceptions:
        exc_type = type(exc).__name__
        error_types[exc_type] = error_types.get(exc_type, 0) + 1
        
        # Consider certain exceptions as critical
        if isinstance(exc, (CorruptedFileException, TableauVersionException, 
                           UnsupportedFileTypeException)):
            critical_errors.append({
                'type': exc_type,
                'message': exc.message,
                'context': exc.get_context()
            })
    
    return {
        'total_errors': len(exceptions),
        'error_types': error_types,
        'critical_errors': critical_errors,
        'has_critical_errors': len(critical_errors) > 0
    }

def is_recoverable_error(exception: MigrationException) -> bool:
    """Determine if an error is recoverable and conversion can continue"""
    recoverable_types = (
        FormulaConversionException,
        VisualConversionException,
        ValidationException,
        DataValidationException
    )
    
    non_recoverable_types = (
        CorruptedFileException,
        UnsupportedFileTypeException,
        TableauVersionException,
        ConfigurationException
    )
    
    if isinstance(exception, non_recoverable_types):
        return False
    elif isinstance(exception, recoverable_types):
        return True
    else:
        # Default to recoverable for unknown exception types
        return True
