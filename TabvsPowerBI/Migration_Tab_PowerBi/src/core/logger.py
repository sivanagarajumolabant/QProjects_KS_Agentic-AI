"""
Universal Logging System for Tableau to Power BI Migration Engine
Provides comprehensive logging for any type of conversion process.
"""

import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum

class LogLevel(Enum):
    """Log levels for migration process"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ConversionStatus(Enum):
    """Status types for conversion components"""
    STARTED = "STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    WARNING = "WARNING"

class MigrationLogger:
    """Universal logger for any Tableau to Power BI migration"""
    
    def __init__(self, log_dir: str = None, log_level: LogLevel = LogLevel.INFO):
        """Initialize migration logger"""
        self.log_level = log_level
        
        # Set up log directory
        if log_dir is None:
            self.log_dir = Path(__file__).parent.parent.parent / "logs"
        else:
            self.log_dir = Path(log_dir)
        
        self.log_dir.mkdir(exist_ok=True)
        
        # Initialize logging components
        self.session_id = self._generate_session_id()
        self.conversion_log = []
        self.error_log = []
        self.performance_log = []
        self.validation_log = []
        
        # Set up file logger
        self._setup_file_logger()
        
        # Track conversion statistics
        self.stats = {
            'start_time': datetime.now(),
            'files_processed': 0,
            'components_converted': 0,
            'errors_encountered': 0,
            'warnings_generated': 0
        }
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID for this conversion"""
        return f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _setup_file_logger(self):
        """Set up file-based logging"""
        log_file = self.log_dir / f"{self.session_id}.log"
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.log_level.value),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()  # Also log to console
            ]
        )
        
        self.logger = logging.getLogger(f"migration_{self.session_id}")
    
    def log_file_analysis(self, file_path: str, file_info: Dict[str, Any]):
        """Log analysis of any Tableau file"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'file_analysis',
            'file_path': file_path,
            'file_info': file_info,
            'status': ConversionStatus.STARTED.value
        }
        
        self.conversion_log.append(log_entry)
        self.logger.info(f"Analyzing file: {file_path}")
        self.logger.info(f"File type: {file_info.get('type', 'unknown')}")
        self.logger.info(f"File size: {file_info.get('size', 'unknown')} bytes")
        
        self.stats['files_processed'] += 1
    
    def log_component_conversion(self, component_type: str, component_name: str, 
                                status: ConversionStatus, details: Dict[str, Any] = None):
        """Log conversion of any component (worksheet, datasource, etc.)"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'component_conversion',
            'component_type': component_type,
            'component_name': component_name,
            'status': status.value,
            'details': details or {}
        }
        
        self.conversion_log.append(log_entry)
        
        if status == ConversionStatus.COMPLETED:
            self.logger.info(f"✅ Converted {component_type}: {component_name}")
            self.stats['components_converted'] += 1
        elif status == ConversionStatus.FAILED:
            self.logger.error(f"❌ Failed to convert {component_type}: {component_name}")
            self.stats['errors_encountered'] += 1
        elif status == ConversionStatus.WARNING:
            self.logger.warning(f"⚠️ Warning in {component_type}: {component_name}")
            self.stats['warnings_generated'] += 1
        else:
            self.logger.info(f"🔄 {status.value}: {component_type} - {component_name}")
    
    def log_formula_conversion(self, original_formula: str, converted_formula: str, 
                              success: bool, issues: List[str] = None):
        """Log conversion of any Tableau formula to DAX"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'formula_conversion',
            'original_formula': original_formula,
            'converted_formula': converted_formula,
            'success': success,
            'issues': issues or []
        }
        
        self.conversion_log.append(log_entry)
        
        if success:
            self.logger.info(f"✅ Formula converted: {original_formula[:50]}...")
        else:
            self.logger.error(f"❌ Formula conversion failed: {original_formula[:50]}...")
            if issues:
                for issue in issues:
                    self.logger.error(f"   Issue: {issue}")
    
    def log_visual_mapping(self, tableau_visual: str, powerbi_visual: str, 
                          mapping_success: bool, compatibility_notes: List[str] = None):
        """Log mapping of any visual type"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'visual_mapping',
            'tableau_visual': tableau_visual,
            'powerbi_visual': powerbi_visual,
            'mapping_success': mapping_success,
            'compatibility_notes': compatibility_notes or []
        }
        
        self.conversion_log.append(log_entry)
        
        if mapping_success:
            self.logger.info(f"✅ Visual mapped: {tableau_visual} → {powerbi_visual}")
        else:
            self.logger.warning(f"⚠️ Visual mapping issue: {tableau_visual}")
        
        if compatibility_notes:
            for note in compatibility_notes:
                self.logger.info(f"   Note: {note}")
    
    def log_data_source_conversion(self, source_type: str, target_type: str, 
                                  connection_details: Dict[str, Any], success: bool):
        """Log conversion of any data source"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'data_source_conversion',
            'source_type': source_type,
            'target_type': target_type,
            'connection_details': connection_details,
            'success': success
        }
        
        self.conversion_log.append(log_entry)
        
        if success:
            self.logger.info(f"✅ Data source converted: {source_type} → {target_type}")
        else:
            self.logger.error(f"❌ Data source conversion failed: {source_type}")
    
    def log_performance_metric(self, operation: str, duration_seconds: float, 
                              details: Dict[str, Any] = None):
        """Log performance metrics for any operation"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'duration_seconds': duration_seconds,
            'details': details or {}
        }
        
        self.performance_log.append(log_entry)
        self.logger.debug(f"⏱️ {operation}: {duration_seconds:.2f}s")
    
    def log_validation_result(self, validation_type: str, component: str, 
                             passed: bool, issues: List[str] = None):
        """Log validation results for any component"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'validation_type': validation_type,
            'component': component,
            'passed': passed,
            'issues': issues or []
        }
        
        self.validation_log.append(log_entry)
        
        if passed:
            self.logger.info(f"✅ Validation passed: {validation_type} - {component}")
        else:
            self.logger.error(f"❌ Validation failed: {validation_type} - {component}")
            if issues:
                for issue in issues:
                    self.logger.error(f"   Issue: {issue}")
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Log any error during conversion"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {}
        }
        
        self.error_log.append(error_entry)
        self.logger.error(f"❌ {error_type}: {error_message}")
        self.stats['errors_encountered'] += 1
    
    def log_warning(self, warning_type: str, warning_message: str, context: Dict[str, Any] = None):
        """Log any warning during conversion"""
        warning_entry = {
            'timestamp': datetime.now().isoformat(),
            'warning_type': warning_type,
            'warning_message': warning_message,
            'context': context or {}
        }
        
        self.conversion_log.append(warning_entry)
        self.logger.warning(f"⚠️ {warning_type}: {warning_message}")
        self.stats['warnings_generated'] += 1
    
    def generate_conversion_report(self) -> Dict[str, Any]:
        """Generate comprehensive conversion report"""
        end_time = datetime.now()
        duration = (end_time - self.stats['start_time']).total_seconds()
        
        report = {
            'session_info': {
                'session_id': self.session_id,
                'start_time': self.stats['start_time'].isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration
            },
            'statistics': {
                'files_processed': self.stats['files_processed'],
                'components_converted': self.stats['components_converted'],
                'errors_encountered': self.stats['errors_encountered'],
                'warnings_generated': self.stats['warnings_generated'],
                'success_rate': self._calculate_success_rate()
            },
            'conversion_log': self.conversion_log,
            'error_log': self.error_log,
            'performance_log': self.performance_log,
            'validation_log': self.validation_log
        }
        
        return report
    
    def save_conversion_report(self, output_path: str = None) -> str:
        """Save conversion report to file"""
        if output_path is None:
            output_path = self.log_dir / f"{self.session_id}_report.json"
        
        report = self.generate_conversion_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"📊 Conversion report saved: {output_path}")
        return str(output_path)
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate"""
        total_operations = self.stats['components_converted'] + self.stats['errors_encountered']
        if total_operations == 0:
            return 100.0
        
        return (self.stats['components_converted'] / total_operations) * 100.0
    
    def print_summary(self):
        """Print conversion summary to console"""
        print("\n" + "="*60)
        print("🎯 CONVERSION SUMMARY")
        print("="*60)
        print(f"Session ID: {self.session_id}")
        print(f"Files Processed: {self.stats['files_processed']}")
        print(f"Components Converted: {self.stats['components_converted']}")
        print(f"Errors: {self.stats['errors_encountered']}")
        print(f"Warnings: {self.stats['warnings_generated']}")
        print(f"Success Rate: {self._calculate_success_rate():.1f}%")
        
        duration = (datetime.now() - self.stats['start_time']).total_seconds()
        print(f"Duration: {duration:.2f} seconds")
        print("="*60)
    
    def get_session_id(self) -> str:
        """Get current session ID"""
        return self.session_id
    
    def get_log_directory(self) -> str:
        """Get log directory path"""
        return str(self.log_dir)
