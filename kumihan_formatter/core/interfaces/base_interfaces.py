"""Base interfaces for consistent architecture patterns

This module defines abstract base classes that establish consistent
naming conventions and behavioral patterns across all components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Union
from pathlib import Path

from ..common import KumihanError, ErrorContext

T = TypeVar('T')
InputType = TypeVar('InputType')
OutputType = TypeVar('OutputType')


class BaseManager(ABC):
    """Base class for Manager components
    
    Managers coordinate multiple components and handle high-level operations.
    They delegate work to Handlers and Processors but don't perform the work themselves.
    
    Naming convention: *Manager (e.g., ConfigManager, TemplateManager)
    """
    
    def __init__(self, name: str):
        """Initialize manager with a name"""
        self.name = name
        self._initialized = False
        self._components: Dict[str, Any] = {}
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the manager and its components
        
        Returns:
            bool: True if initialization successful
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """Cleanup and shutdown the manager
        
        Returns:
            bool: True if shutdown successful
        """
        pass
    
    def register_component(self, name: str, component: Any) -> None:
        """Register a component with this manager"""
        self._components[name] = component
    
    def get_component(self, name: str) -> Optional[Any]:
        """Get a registered component by name"""
        return self._components.get(name)
    
    def is_initialized(self) -> bool:
        """Check if manager is initialized"""
        return self._initialized


class BaseHandler(ABC):
    """Base class for Handler components
    
    Handlers process specific types of operations and contain business logic.
    They handle individual operations but don't coordinate multiple components.
    
    Naming convention: *Handler (e.g., ErrorHandler, FileHandler)
    """
    
    def __init__(self, name: str):
        """Initialize handler with a name"""
        self.name = name
        self._error_count = 0
        self._last_error: Optional[KumihanError] = None
    
    @abstractmethod
    def handle(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """Handle the input and return result
        
        Args:
            input_data: Data to process
            context: Optional context information
            
        Returns:
            Processed result
            
        Raises:
            KumihanError: If handling fails
        """
        pass
    
    def get_error_count(self) -> int:
        """Get number of errors encountered"""
        return self._error_count
    
    def get_last_error(self) -> Optional[KumihanError]:
        """Get the last error that occurred"""
        return self._last_error
    
    def _record_error(self, error: KumihanError) -> None:
        """Record an error for statistics"""
        self._error_count += 1
        self._last_error = error


class BaseProcessor(ABC, Generic[InputType, OutputType]):
    """Base class for Processor components
    
    Processors transform data from one format to another.
    They are stateless and focus on pure data transformation.
    
    Naming convention: *Processor (e.g., TextProcessor, ImageProcessor)
    """
    
    @abstractmethod
    def process(self, input_data: InputType) -> OutputType:
        """Process input data and return transformed output
        
        Args:
            input_data: Input data to transform
            
        Returns:
            Transformed output data
            
        Raises:
            KumihanError: If processing fails
        """
        pass
    
    def can_process(self, input_data: Any) -> bool:
        """Check if this processor can handle the input
        
        Args:
            input_data: Data to check
            
        Returns:
            bool: True if this processor can handle the input
        """
        return True
    
    def get_output_type(self) -> type:
        """Get the expected output type
        
        Returns:
            type: Output type class
        """
        return object


class BaseValidator(ABC):
    """Base class for Validator components
    
    Validators check data for correctness and compliance.
    They return validation results without modifying the input.
    
    Naming convention: *Validator (e.g., SyntaxValidator, FileValidator)
    """
    
    def __init__(self, name: str):
        """Initialize validator with a name"""
        self.name = name
        self._validation_count = 0
        self._error_count = 0
    
    @abstractmethod
    def validate(self, input_data: Any) -> List[KumihanError]:
        """Validate input data
        
        Args:
            input_data: Data to validate
            
        Returns:
            List[KumihanError]: List of validation errors (empty if valid)
        """
        pass
    
    def is_valid(self, input_data: Any) -> bool:
        """Check if input data is valid
        
        Args:
            input_data: Data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        errors = self.validate(input_data)
        self._validation_count += 1
        if errors:
            self._error_count += len(errors)
        return len(errors) == 0
    
    def get_validation_stats(self) -> Dict[str, int]:
        """Get validation statistics
        
        Returns:
            Dict with validation and error counts
        """
        return {
            'validations': self._validation_count,
            'errors': self._error_count
        }


class BaseRenderer(ABC, Generic[T]):
    """Base class for Renderer components
    
    Renderers convert structured data into output formats (HTML, PDF, etc.).
    They focus on presentation and formatting.
    
    Naming convention: *Renderer (e.g., HTMLRenderer, PDFRenderer)
    """
    
    def __init__(self, output_format: str):
        """Initialize renderer with output format"""
        self.output_format = output_format
        self._render_count = 0
    
    @abstractmethod
    def render(self, data: T) -> str:
        """Render data to output format
        
        Args:
            data: Structured data to render
            
        Returns:
            str: Rendered output
            
        Raises:
            KumihanError: If rendering fails
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[type]:
        """Get list of data types this renderer supports
        
        Returns:
            List[type]: Supported input types
        """
        pass
    
    def can_render(self, data: Any) -> bool:
        """Check if this renderer can handle the data
        
        Args:
            data: Data to check
            
        Returns:
            bool: True if this renderer can handle the data
        """
        supported_types = self.get_supported_types()
        return any(isinstance(data, t) for t in supported_types)
    
    def get_render_count(self) -> int:
        """Get number of renders performed"""
        return self._render_count
    
    def _increment_render_count(self) -> None:
        """Increment render counter"""
        self._render_count += 1


class BaseParser(ABC, Generic[T]):
    """Base class for Parser components
    
    Parsers convert raw input (text, files) into structured data.
    They handle syntax analysis and data extraction.
    
    Naming convention: *Parser (e.g., KumihanParser, JSONParser)
    """
    
    def __init__(self, name: str):
        """Initialize parser with a name"""
        self.name = name
        self._parse_count = 0
        self._error_count = 0
    
    @abstractmethod
    def parse(self, input_data: Union[str, Path]) -> T:
        """Parse input data into structured format
        
        Args:
            input_data: Raw input to parse
            
        Returns:
            T: Parsed structured data
            
        Raises:
            KumihanError: If parsing fails
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of input formats this parser supports
        
        Returns:
            List[str]: Supported format extensions (e.g., ['.txt', '.md'])
        """
        pass
    
    def can_parse(self, input_data: Union[str, Path]) -> bool:
        """Check if this parser can handle the input
        
        Args:
            input_data: Input to check
            
        Returns:
            bool: True if this parser can handle the input
        """
        if isinstance(input_data, Path):
            return input_data.suffix in self.get_supported_formats()
        return True  # Assume string input is always parseable
    
    def get_parse_stats(self) -> Dict[str, int]:
        """Get parsing statistics
        
        Returns:
            Dict with parse and error counts
        """
        return {
            'parses': self._parse_count,
            'errors': self._error_count
        }
    
    def _increment_parse_count(self) -> None:
        """Increment parse counter"""
        self._parse_count += 1
    
    def _increment_error_count(self) -> None:
        """Increment error counter"""
        self._error_count += 1