"""
WebSocket endpoint for real-time travel alerts.
Clients subscribe to a route + date and receive live risk/weather updates.
"""
import asyncio
import json
from datetime import date, datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List

router = APIRouter(tags=["WebSocket"])

# Active connections: {channel_key: [WebSocket]}
_connections: Dict[str, List[WebSocket]] = {}


def _channel_key(source: str, destination: str, travel_date: date) -> str:
    return f"{source.lower()}:{destination.lower()}:{travel_date.isoformat()}"


@router.websocket("/ws/alerts/{source}/{destination}/{travel_date}")
async def travel_alerts(
    websocket: WebSocket,
    source: str,
    destination: str,
    travel_date: str,
):
    """
    Real-time travel alert WebSocket.

    Connect to receive live updates for a specific route + date.
    Message format:
        {"type": "risk_update" | "weather_alert" | "ping", "data": {...}}

    Usage (JS):
        const ws = new WebSocket("ws://localhost:8000/ws/alerts/Chennai/Bangalore/2025-10-14")
        ws.onmessage = (e) => console.log(JSON.parse(e.data))
    """
    await websocket.accept()
    try:
        d = date.fromisoformat(travel_date)
    except ValueError:
        await websocket.send_json({"type": "error", "message": "Invalid date format"})
        await websocket.close()
        return

    key = _channel_key(source, destination, d)
    _connections.setdefault(key, []).append(websocket)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "channel": key,
            "message": f"Subscribed to alerts for {source} → {destination} on {travel_date}",
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Keep-alive loop with periodic pings
        while True:
            try:
                # Wait for client message (ping/pong) or timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
            except asyncio.TimeoutError:
                # Send server-side ping
                await websocket.send_json({"type": "ping", "timestamp": datetime.utcnow().isoformat()})

    except WebSocketDisconnect:
        pass
    finally:
        if key in _connections:
            _connections[key] = [ws for ws in _connections[key] if ws != websocket]


async def broadcast_alert(source: str, destination: str, travel_date: date, payload: dict):
    """Broadcast an alert to all subscribers of a route channel."""
    key = _channel_key(source, destination, travel_date)
    dead = []
    for ws in _connections.get(key, []):
        try:
            await ws.send_json({"type": "alert", "data": payload, "timestamp": datetime.utcnow().isoformat()})
        except Exception:
            dead.append(ws)
    # Clean dead connections
    if dead and key in _connections:
        _connections[key] = [ws for ws in _connections[key] if ws not in dead]
