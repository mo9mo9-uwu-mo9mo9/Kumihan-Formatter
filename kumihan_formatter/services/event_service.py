"""Event service implementation

This module provides event-driven architecture support
with event publishing, subscription, and lifecycle management.
"""

import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..core.common import ErrorCategory, KumihanError
from ..core.interfaces import EventService


class EventServiceImpl(EventService):
    """Event service implementation for event-driven architecture

    Provides event publishing, subscription management, and
    event lifecycle tracking with error handling.
    """

    def __init__(self):
        """Initialize event service"""
        self._subscribers: Dict[str, Dict[str, Callable]] = defaultdict(dict)
        self._event_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000
        self._stats = {"events_emitted": 0, "events_processed": 0, "errors": 0, "subscribers_count": 0}

    def emit(self, event_name: str, data: Any = None) -> None:
        """Emit an event to all subscribers

        Args:
            event_name: Name of the event
            data: Optional event data
        """
        event = {"name": event_name, "data": data, "timestamp": datetime.now(), "id": str(uuid.uuid4())}

        # Add to history
        self._add_to_history(event)

        # Update stats
        self._stats["events_emitted"] += 1

        # Notify subscribers
        if event_name in self._subscribers:
            for subscriber_id, handler in self._subscribers[event_name].items():
                try:
                    handler(data)
                    self._stats["events_processed"] += 1
                except Exception as e:
                    self._stats["errors"] += 1
                    self._handle_subscriber_error(event_name, subscriber_id, handler, e)

    def subscribe(self, event_name: str, handler: Callable[[Any], None]) -> str:
        """Subscribe to an event

        Args:
            event_name: Name of the event
            handler: Event handler function

        Returns:
            str: Subscription ID
        """
        subscription_id = str(uuid.uuid4())
        self._subscribers[event_name][subscription_id] = handler
        self._stats["subscribers_count"] += 1

        # Emit subscription event
        self.emit("system.subscription.added", {"event_name": event_name, "subscription_id": subscription_id})

        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from an event

        Args:
            subscription_id: Subscription ID from subscribe()

        Returns:
            bool: True if unsubscribed successfully
        """
        # Find and remove subscription
        for event_name, subscribers in self._subscribers.items():
            if subscription_id in subscribers:
                del subscribers[subscription_id]
                self._stats["subscribers_count"] -= 1

                # Clean up empty event entries
                if not subscribers:
                    del self._subscribers[event_name]

                # Emit unsubscription event
                self.emit("system.subscription.removed", {"event_name": event_name, "subscription_id": subscription_id})

                return True

        return False

    def get_event_stats(self) -> Dict[str, Any]:
        """Get event statistics

        Returns:
            Dict[str, Any]: Event statistics
        """
        return {
            **self._stats,
            "active_events": len(self._subscribers),
            "total_subscriptions": sum(len(subs) for subs in self._subscribers.values()),
            "history_size": len(self._event_history),
        }

    # Extended functionality

    def subscribe_once(self, event_name: str, handler: Callable[[Any], None]) -> str:
        """Subscribe to an event for one-time execution

        Args:
            event_name: Name of the event
            handler: Event handler function

        Returns:
            str: Subscription ID
        """

        def one_time_handler(data):
            try:
                handler(data)
            finally:
                # Automatically unsubscribe after execution
                self.unsubscribe(subscription_id)

        subscription_id = self.subscribe(event_name, one_time_handler)
        return subscription_id

    def subscribe_with_filter(
        self, event_name: str, handler: Callable[[Any], None], filter_func: Callable[[Any], bool]
    ) -> str:
        """Subscribe to an event with a filter condition

        Args:
            event_name: Name of the event
            handler: Event handler function
            filter_func: Function that returns True if event should be processed

        Returns:
            str: Subscription ID
        """

        def filtered_handler(data):
            if filter_func(data):
                handler(data)

        return self.subscribe(event_name, filtered_handler)

    def emit_async(self, event_name: str, data: Any = None) -> None:
        """Emit an event asynchronously (non-blocking)

        Args:
            event_name: Name of the event
            data: Optional event data
        """
        # For now, implement as synchronous
        # In a real implementation, this would use threading or asyncio
        self.emit(event_name, data)

    def get_subscribers(self, event_name: str) -> List[str]:
        """Get list of subscriber IDs for an event

        Args:
            event_name: Name of the event

        Returns:
            List[str]: Subscriber IDs
        """
        return list(self._subscribers.get(event_name, {}).keys())

    def get_all_events(self) -> List[str]:
        """Get list of all event names with subscribers

        Returns:
            List[str]: Event names
        """
        return list(self._subscribers.keys())

    def clear_subscribers(self, event_name: Optional[str] = None) -> int:
        """Clear subscribers for an event or all events

        Args:
            event_name: Event name to clear (all if None)

        Returns:
            int: Number of subscribers removed
        """
        if event_name:
            if event_name in self._subscribers:
                count = len(self._subscribers[event_name])
                del self._subscribers[event_name]
                self._stats["subscribers_count"] -= count
                return count
            return 0
        else:
            total_count = sum(len(subs) for subs in self._subscribers.values())
            self._subscribers.clear()
            self._stats["subscribers_count"] = 0
            return total_count

    def get_event_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get event history

        Args:
            limit: Maximum number of events to return

        Returns:
            List[Dict[str, Any]]: Event history
        """
        history = self._event_history.copy()
        if limit:
            history = history[-limit:]
        return history

    def clear_event_history(self) -> None:
        """Clear event history"""
        self._event_history.clear()

    def has_subscribers(self, event_name: str) -> bool:
        """Check if event has subscribers

        Args:
            event_name: Event name to check

        Returns:
            bool: True if event has subscribers
        """
        return event_name in self._subscribers and bool(self._subscribers[event_name])

    def wait_for_event(self, event_name: str, timeout: Optional[float] = None) -> Optional[Any]:
        """Wait for a specific event to be emitted

        Args:
            event_name: Event name to wait for
            timeout: Timeout in seconds (None for no timeout)

        Returns:
            Optional[Any]: Event data when received, None if timeout
        """
        # This is a simplified synchronous implementation
        # A real implementation would use threading.Event or asyncio.Event

        result = {"data": None, "received": False}

        def event_waiter(data):
            result["data"] = data
            result["received"] = True

        subscription_id = self.subscribe_once(event_name, event_waiter)

        # In a real implementation, we would wait with timeout here
        # For now, just return None (timeout)
        return None

    def create_event_chain(self, events: List[str]) -> str:
        """Create a chain of events that trigger in sequence

        Args:
            events: List of event names to chain

        Returns:
            str: Chain ID
        """
        chain_id = str(uuid.uuid4())

        def create_chain_handler(next_event, chain_data):
            def handler(data):
                # Combine chain data with current event data
                combined_data = {"chain_id": chain_id, "chain_data": chain_data, "current_data": data}
                self.emit(next_event, combined_data)

            return handler

        # Set up chain handlers
        for i in range(len(events) - 1):
            current_event = events[i]
            next_event = events[i + 1]

            handler = create_chain_handler(next_event, {"position": i})
            self.subscribe(current_event, handler)

        return chain_id

    def _add_to_history(self, event: Dict[str, Any]) -> None:
        """Add event to history with size management"""
        self._event_history.append(event)

        # Trim history if it exceeds maximum size
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size :]

    def _handle_subscriber_error(
        self, event_name: str, subscriber_id: str, handler: Callable, error: Exception
    ) -> None:
        """Handle errors in event subscribers"""
        error_event = {
            "event_name": event_name,
            "subscriber_id": subscriber_id,
            "error": str(error),
            "handler": str(handler),
        }

        # Emit error event (but don't create infinite loop)
        if event_name != "system.subscriber.error":
            self.emit("system.subscriber.error", error_event)

    def set_max_history_size(self, size: int) -> None:
        """Set maximum event history size

        Args:
            size: Maximum number of events to keep in history
        """
        self._max_history_size = max(0, size)

        # Trim current history if needed
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size :]
