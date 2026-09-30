"""
Central Event Engine for Crisis Command AI.
Provides an asynchronous and synchronous event bus where every important system change
is dispatched as a structured, auditable event to subscribed agents and WebSocket clients.
"""
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime
import uuid
import asyncio
import logging

logger = logging.getLogger("event_engine")

# Canonical Event Types per Crisis Command AI specification
EVENT_TYPES = {
    "INCIDENT_CREATED": "INCIDENT_CREATED",
    "INCIDENT_UPDATED": "INCIDENT_UPDATED",
    "HAZARD_CHANGED": "HAZARD_CHANGED",
    "WIND_CHANGED": "WIND_CHANGED",
    "ROAD_BLOCKED": "ROAD_BLOCKED",
    "ROAD_REOPENED": "ROAD_REOPENED",
    "RESOURCE_ASSIGNED": "RESOURCE_ASSIGNED",
    "RESOURCE_UNAVAILABLE": "RESOURCE_UNAVAILABLE",
    "GPS_UPDATED": "GPS_UPDATED",
    "ROUTE_CHANGED": "ROUTE_CHANGED",
    "ETA_CHANGED": "ETA_CHANGED",
    "CASUALTY_REPORTED": "CASUALTY_REPORTED",
    "HOSPITAL_CAPACITY_CHANGED": "HOSPITAL_CAPACITY_CHANGED",
    "SHELTER_CAPACITY_CHANGED": "SHELTER_CAPACITY_CHANGED",
    "EVACUATION_RECOMMENDED": "EVACUATION_RECOMMENDED",
    "RESPONSE_REPLANNED": "RESPONSE_REPLANNED",
    "ALERT_CREATED": "ALERT_CREATED",
    "APPROVAL_REQUESTED": "APPROVAL_REQUESTED",
    "APPROVAL_DECIDED": "APPROVAL_DECIDED"
}

class EventEngine:
    def __init__(self):
        # Event subscribers: event_type -> list of callback functions
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        # Chronological audit log of all events
        self._event_history: List[Dict[str, Any]] = []
        # Maximum event history to retain in-memory
        self.max_history = 1000
        # Active WebSocket listener queues
        self._ws_listeners: Set[asyncio.Queue] = set()

    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """Registers a callback for a specific event type, or '*' for all events."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def register_ws_queue(self, queue: asyncio.Queue):
        """Registers a WebSocket broadcast queue."""
        self._ws_listeners.add(queue)

    def unregister_ws_queue(self, queue: asyncio.Queue):
        """Unregisters a WebSocket broadcast queue."""
        self._ws_listeners.discard(queue)

    def emit(
        self,
        event_type: str,
        incident_id: str,
        source: str,
        severity: str = "INFO",
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Dispatches an event synchronously, records it to the audit log,
        and pushes it to async WebSocket queues.
        """
        now = datetime.now()
        event_id = f"EVT-{now.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        
        event = {
            "event_id": event_id,
            "incident_id": incident_id,
            "timestamp": now.isoformat(),
            "time_formatted": now.strftime("%H:%M:%S"),
            "type": event_type,
            "source": source,
            "severity": severity.upper(), # INFO, WARNING, HIGH, CRITICAL, SUCCESS
            "data": data or {}
        }

        # Store in audit history (newest first)
        self._event_history.insert(0, event)
        if len(self._event_history) > self.max_history:
            self._event_history.pop()

        # Call typed subscribers
        callbacks = self._subscribers.get(event_type, []) + self._subscribers.get("*", [])
        for cb in callbacks:
            try:
                cb(event)
            except Exception as e:
                logger.error(f"Error in event subscriber {cb}: {e}")

        # Broadcast to active WebSockets non-blockingly
        for q in list(self._ws_listeners):
            try:
                q.put_nowait(event)
            except Exception:
                pass

        return event

    def get_history(self, incident_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Returns recent audit events, optionally filtered by incident_id."""
        if not incident_id:
            return self._event_history[:limit]
        clean_id = incident_id.strip().upper()
        return [e for e in self._event_history if e.get("incident_id", "").upper() == clean_id][:limit]

# Singleton instance
event_engine = EventEngine()
