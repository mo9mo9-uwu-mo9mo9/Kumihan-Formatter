"""Error handler base class extracted from error_framework.py

This module contains the base error handler interface and implementation
to maintain the 300-line limit for error_framework.py.
"""

from abc import ABC, abstractmethod
from typing import Any

from .error_base import KumihanError


class BaseErrorHandler(ABC):
    """Abstract base class for error handlers"""

    @abstractmethod
    def handle_error(self, error: KumihanError) -> None:
        """Handle an error

        Args:
            error: The error to handle
        """
        pass

    @abstractmethod
    def can_handle(self, error: KumihanError) -> bool:
        """Check if this handler can handle the error

        Args:
            error: The error to check

        Returns:
            bool: True if this handler can handle the error
        """
        pass

    def get_handler_info(self) -> dict[str, Any]:
        """Get handler information

        Returns:
            dict: Handler information
        """
        return {
            "handler_type": self.__class__.__name__,
            "can_handle": "Abstract method",
        }


class DefaultErrorHandler(BaseErrorHandler):
    """Default error handler that logs errors"""

    def __init__(self, logger: Any = None) -> None:
        """Initialize default error handler

        Args:
            logger: Optional logger instance
        """
        self.logger = logger

    def handle_error(self, error: KumihanError) -> None:
        """Handle an error by logging it

        Args:
            error: The error to handle
        """
        if self.logger:
            if error.is_critical():
                self.logger.critical(str(error))
            elif error.severity.value == "error":
                self.logger.error(str(error))
            elif error.severity.value == "warning":
                self.logger.warning(str(error))
            else:
                self.logger.info(str(error))
        else:
            # Fallback to print if no logger
            print(f"ERROR: {error}")

    def can_handle(self, error: KumihanError) -> bool:
        """Check if this handler can handle the error

        Args:
            error: The error to check

        Returns:
            bool: Always True (default handler)
        """
        return True

    def get_handler_info(self) -> dict[str, Any]:
        """Get handler information"""
        return {
            "handler_type": "DefaultErrorHandler",
            "can_handle": "All errors",
            "has_logger": self.logger is not None,
        }


class ErrorHandlerChain:
    """Chain of error handlers"""

    def __init__(self) -> None:
        """Initialize error handler chain"""
        self.handlers: list[BaseErrorHandler] = []

    def add_handler(self, handler: BaseErrorHandler) -> None:
        """Add a handler to the chain

        Args:
            handler: Handler to add
        """
        self.handlers.append(handler)

    def handle_error(self, error: KumihanError) -> bool:
        """Handle an error using the chain

        Args:
            error: Error to handle

        Returns:
            bool: True if error was handled
        """
        for handler in self.handlers:
            if handler.can_handle(error):
                handler.handle_error(error)
                return True

    def get_chain_info(self) -> dict[str, Any]:
        """Get information about the handler chain"""
        return {
            "handler_count": len(self.handlers),
            "handlers": [handler.get_handler_info() for handler in self.handlers],
        }
