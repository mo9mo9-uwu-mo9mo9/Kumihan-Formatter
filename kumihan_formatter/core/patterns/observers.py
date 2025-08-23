"""Observer実装例"""

import logging
from typing import List

from ..utilities.logger import get_logger
from .observer import Event, EventType, Observer


class ParsingObserver(Observer):
    """パーシング監視オブザーバー"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def handle_event(self, event: Event) -> None:
        if event.event_type == EventType.PARSING_STARTED:
            self.logger.info(
                f"Parsing started: {event.data.get('content_length', 0)} characters"
            )
        elif event.event_type == EventType.PARSING_COMPLETED:
            self.logger.info(
                f"Parsing completed in {event.data.get('duration', 0):.3f}s"
            )
        elif event.event_type == EventType.PARSING_ERROR:
            self.logger.error(
                f"Parsing failed: {event.data.get('error', 'Unknown error')}"
            )

    def get_supported_events(self) -> List[EventType]:
        return [
            EventType.PARSING_STARTED,
            EventType.PARSING_COMPLETED,
            EventType.PARSING_ERROR,
        ]


class RenderingObserver(Observer):
    """レンダリング監視オブザーバー"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def handle_event(self, event: Event) -> None:
        if event.event_type == EventType.RENDERING_STARTED:
            self.logger.info(
                f"Rendering started: format={event.data.get('format', 'unknown')}"
            )
        elif event.event_type == EventType.RENDERING_COMPLETED:
            self.logger.info(
                f"Rendering completed: {event.data.get('output_size', 0)} bytes"
            )
        elif event.event_type == EventType.RENDERING_ERROR:
            self.logger.error(
                f"Rendering failed: {event.data.get('error', 'Unknown error')}"
            )

    def get_supported_events(self) -> List[EventType]:
        return [
            EventType.RENDERING_STARTED,
            EventType.RENDERING_COMPLETED,
            EventType.RENDERING_ERROR,
        ]
