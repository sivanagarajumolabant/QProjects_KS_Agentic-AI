"""
Base Converter Class for Generic Tableau to Power BI Migration Engine
Provides common functionality and interface for all conversion components.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import time

from .config_manager import ConfigManager
from .logger import MigrationLogger, ConversionStatus
from .exceptions import MigrationException, handle_migration_exception

class BaseConverter(ABC):
    """Abstract base class for all conversion components"""
    
    def __init__(self, config_manager: ConfigManager, logger: MigrationLogger):
        """Initialize base converter"""
        self.config_manager = config_manager
        self.logger = logger
        self.conversion_stats = {
            'items_processed': 0,
            'items_converted': 0,
            'items_failed': 0,
            'items_skipped': 0,
            'start_time': None,
            'end_time': None
        }
        self.errors = []
        self.warnings = []
    
    @abstractmethod
    def convert(self, input_data: Any) -> Any:
        """Convert input data to target format"""
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data before conversion"""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """Get list of supported input types"""
        pass
    
    def start_conversion(self, operation_name: str = None):
        """Start conversion process and initialize tracking"""
        self.conversion_stats['start_time'] = datetime.now()
        operation_name = operation_name or self.__class__.__name__
        self.logger.log_component_conversion(
            component_type=operation_name,
            component_name="conversion_process",
            status=ConversionStatus.STARTED
        )
    
    def end_conversion(self, operation_name: str = None):
        """End conversion process and log results"""
        self.conversion_stats['end_time'] = datetime.now()
        duration = (self.conversion_stats['end_time'] - self.conversion_stats['start_time']).total_seconds()
        
        operation_name = operation_name or self.__class__.__name__
        
        # Log performance metrics
        self.logger.log_performance_metric(
            operation=operation_name,
            duration_seconds=duration,
            details=self.conversion_stats
        )
        
        # Log completion status
        if self.conversion_stats['items_failed'] == 0:
            status = ConversionStatus.COMPLETED
        elif self.conversion_stats['items_converted'] > 0:
            status = ConversionStatus.WARNING
        else:
            status = ConversionStatus.FAILED
        
        self.logger.log_component_conversion(
            component_type=operation_name,
            component_name="conversion_process",
            status=status,
            details=self.conversion_stats
        )
    
    def convert_with_error_handling(self, input_data: Any, item_name: str = None) -> Optional[Any]:
        """Convert with comprehensive error handling"""
        item_name = item_name or "unknown_item"
        
        try:
            # Validate input
            if not self.validate_input(input_data):
                self.logger.log_warning(
                    warning_type="validation_warning",
                    warning_message=f"Input validation failed for {item_name}",
                    context={'item_name': item_name}
                )
                self.conversion_stats['items_skipped'] += 1
                return None
            
            # Perform conversion
            start_time = time.time()
            result = self.convert(input_data)
            conversion_time = time.time() - start_time
            
            # Log success
            self.logger.log_performance_metric(
                operation=f"{self.__class__.__name__}_convert_item",
                duration_seconds=conversion_time,
                details={'item_name': item_name}
            )
            
            self.conversion_stats['items_converted'] += 1
            return result
            
        except MigrationException as e:
            # Handle known migration exceptions
            error_info = handle_migration_exception(e, self.logger)
            self.errors.append(error_info)
            self.conversion_stats['items_failed'] += 1
            return None
            
        except Exception as e:
            # Handle unexpected exceptions
            error_info = {
                'exception_type': type(e).__name__,
                'message': str(e),
                'item_name': item_name,
                'converter': self.__class__.__name__
            }
            
            self.logger.log_error(
                error_type="unexpected_error",
                error_message=str(e),
                context=error_info
            )
            
            self.errors.append(error_info)
            self.conversion_stats['items_failed'] += 1
            return None
        
        finally:
            self.conversion_stats['items_processed'] += 1
    
    def batch_convert(self, input_items: List[Any], item_names: List[str] = None) -> List[Any]:
        """Convert multiple items with batch processing"""
        if item_names is None:
            item_names = [f"item_{i}" for i in range(len(input_items))]
        
        self.start_conversion(f"{self.__class__.__name__}_batch")
        
        results = []
        for i, item in enumerate(input_items):
            item_name = item_names[i] if i < len(item_names) else f"item_{i}"
            result = self.convert_with_error_handling(item, item_name)
            results.append(result)
        
        self.end_conversion(f"{self.__class__.__name__}_batch")
        
        return results
    
    def get_conversion_summary(self) -> Dict[str, Any]:
        """Get summary of conversion process"""
        duration = None
        if self.conversion_stats['start_time'] and self.conversion_stats['end_time']:
            duration = (self.conversion_stats['end_time'] - self.conversion_stats['start_time']).total_seconds()
        
        success_rate = 0.0
        if self.conversion_stats['items_processed'] > 0:
            success_rate = (self.conversion_stats['items_converted'] / self.conversion_stats['items_processed']) * 100
        
        return {
            'converter_type': self.__class__.__name__,
            'statistics': self.conversion_stats,
            'duration_seconds': duration,
            'success_rate': success_rate,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def reset_stats(self):
        """Reset conversion statistics"""
        self.conversion_stats = {
            'items_processed': 0,
            'items_converted': 0,
            'items_failed': 0,
            'items_skipped': 0,
            'start_time': None,
            'end_time': None
        }
        self.errors = []
        self.warnings = []
    
    def is_supported_type(self, input_type: str) -> bool:
        """Check if input type is supported"""
        return input_type in self.get_supported_types()
    
    def get_config_value(self, config_key: str, default_value: Any = None) -> Any:
        """Get configuration value with fallback"""
        try:
            # Try to get from specific configuration methods
            if hasattr(self.config_manager, f'get_{config_key}'):
                return getattr(self.config_manager, f'get_{config_key}')()
            else:
                return default_value
        except Exception:
            return default_value
    
    def log_conversion_step(self, step_name: str, details: Dict[str, Any] = None):
        """Log a conversion step"""
        self.logger.log_component_conversion(
            component_type=self.__class__.__name__,
            component_name=step_name,
            status=ConversionStatus.IN_PROGRESS,
            details=details
        )
    
    def add_warning(self, warning_message: str, context: Dict[str, Any] = None):
        """Add a warning to the conversion process"""
        warning_info = {
            'message': warning_message,
            'context': context or {},
            'converter': self.__class__.__name__,
            'timestamp': datetime.now().isoformat()
        }
        
        self.warnings.append(warning_info)
        self.logger.log_warning(
            warning_type="conversion_warning",
            warning_message=warning_message,
            context=context
        )

class ConversionResult:
    """Container for conversion results with metadata"""
    
    def __init__(self, success: bool, data: Any = None, errors: List[Dict] = None, 
                 warnings: List[Dict] = None, metadata: Dict[str, Any] = None):
        self.success = success
        self.data = data
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def has_errors(self) -> bool:
        """Check if result has errors"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if result has warnings"""
        return len(self.warnings) > 0
    
    def get_error_summary(self) -> str:
        """Get summary of errors"""
        if not self.errors:
            return "No errors"
        
        error_types = {}
        for error in self.errors:
            error_type = error.get('exception_type', 'unknown')
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return f"{len(self.errors)} errors: " + ", ".join([f"{count} {error_type}" for error_type, count in error_types.items()])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            'success': self.success,
            'data': self.data,
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'has_errors': self.has_errors(),
            'has_warnings': self.has_warnings(),
            'error_summary': self.get_error_summary()
        }

class ConversionPipeline:
    """Pipeline for chaining multiple converters"""
    
    def __init__(self, logger: MigrationLogger):
        self.logger = logger
        self.converters = []
        self.pipeline_stats = {
            'total_stages': 0,
            'completed_stages': 0,
            'failed_stages': 0
        }
    
    def add_converter(self, converter: BaseConverter, stage_name: str = None):
        """Add converter to pipeline"""
        stage_name = stage_name or converter.__class__.__name__
        self.converters.append({
            'converter': converter,
            'stage_name': stage_name
        })
        self.pipeline_stats['total_stages'] += 1
    
    def execute(self, input_data: Any) -> ConversionResult:
        """Execute conversion pipeline"""
        self.logger.log_component_conversion(
            component_type="ConversionPipeline",
            component_name="pipeline_execution",
            status=ConversionStatus.STARTED
        )
        
        current_data = input_data
        all_errors = []
        all_warnings = []
        pipeline_metadata = {}
        
        for stage in self.converters:
            converter = stage['converter']
            stage_name = stage['stage_name']
            
            try:
                self.logger.log_component_conversion(
                    component_type="PipelineStage",
                    component_name=stage_name,
                    status=ConversionStatus.STARTED
                )
                
                # Execute converter
                result = converter.convert_with_error_handling(current_data, stage_name)
                
                if result is not None:
                    current_data = result
                    self.pipeline_stats['completed_stages'] += 1
                    
                    self.logger.log_component_conversion(
                        component_type="PipelineStage",
                        component_name=stage_name,
                        status=ConversionStatus.COMPLETED
                    )
                else:
                    self.pipeline_stats['failed_stages'] += 1
                    
                    self.logger.log_component_conversion(
                        component_type="PipelineStage",
                        component_name=stage_name,
                        status=ConversionStatus.FAILED
                    )
                
                # Collect errors and warnings
                summary = converter.get_conversion_summary()
                all_errors.extend(summary['errors'])
                all_warnings.extend(summary['warnings'])
                pipeline_metadata[stage_name] = summary
                
            except Exception as e:
                self.pipeline_stats['failed_stages'] += 1
                error_info = {
                    'stage_name': stage_name,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
                all_errors.append(error_info)
                
                self.logger.log_error(
                    error_type="pipeline_stage_error",
                    error_message=str(e),
                    context=error_info
                )
        
        # Determine overall success
        success = self.pipeline_stats['failed_stages'] == 0 and current_data is not None
        
        self.logger.log_component_conversion(
            component_type="ConversionPipeline",
            component_name="pipeline_execution",
            status=ConversionStatus.COMPLETED if success else ConversionStatus.FAILED,
            details=self.pipeline_stats
        )
        
        return ConversionResult(
            success=success,
            data=current_data,
            errors=all_errors,
            warnings=all_warnings,
            metadata=pipeline_metadata
        )
