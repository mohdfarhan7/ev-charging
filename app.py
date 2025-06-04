import asyncio
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
import httpx
import websockets
from ocpp.routing import on
from ocpp.v16 import ChargePoint as OcppChargePoint
from ocpp.v16.enums import RegistrationStatus
from ocpp.v16 import call_result
import threading

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ev-charger")

app = FastAPI()

# Charger Status Storage
charger_status = {
    "charger_id": "EV123",
    "status": "Available",
    "current_session": None
}

# OCPP ChargePoint
class ChargePoint(OcppChargePoint):
    @on("BootNotification")
    async def on_boot_notification(self, charge_point_model, charge_point_vendor, **kwargs):
        logger.info(f"BootNotification from {self.id}: {charge_point_model}, {charge_point_vendor}")
        return call_result.BootNotificationPayload(
            current_time=datetime.utcnow().isoformat(),
            interval=10,
            status=RegistrationStatus.accepted
        )

    @on("Heartbeat")
    async def on_heartbeat(self):
        logger.info(f"Heartbeat received from {self.id}")
        return call_result.HeartbeatPayload(current_time=datetime.utcnow().isoformat())

# OCPP WebSocket Server
async def ocpp_server(websocket, path):
    charge_point_id = path.strip("/")
    cp = ChargePoint(charge_point_id, websocket)
    await cp.start()

def start_ocpp_server():
    async def run():
        server = await websockets.serve(ocpp_server, "0.0.0.0", 9000, subprotocols=["ocpp1.6"])
        logger.info("OCPP Server running on ws://0.0.0.0:9000")
        await server.wait_closed()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run())

# Run OCPP Server in background
ocpp_thread = threading.Thread(target=start_ocpp_server, daemon=True)
ocpp_thread.start()

# FastAPI Endpoints
@app.get("/")
def home():
    return {"message": "EV Charger Simulator Running"}

@app.get("/connect-charger")
def connect_charger(charger_id: str):
    return {
        "status": "True",
        "charger_id": charger_id,
        "message": "Charger connected successfully.",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/start-session")
def start_session(charger_id: str):
    if charger_status["status"] == "Charging":
        raise HTTPException(status_code=400, detail="Charger is already in use")
    start_time = datetime.utcnow().isoformat()
    charger_status["status"] = "Charging"
    charger_status["current_session"] = {
        "charger_id": charger_id,
        "start_time": start_time
    }
    logger.info(f"Started charging session for user {charger_id}")
    return {
        "status": "True",
        "message": "Charging started",
        "session": charger_status["current_session"]
    }

@app.get("/charging-ui-status")
def charging_ui_status():
    return {
        "status": "True",
        "status_lab": "Charging",
        "battery_level": 0.2,
        "estimated_time_left": "19 min approx",
        "session_duration": "0 min ago",
        "charging_cost": "$0.00",
        "station_name": "EV Station A1",
        "map_location": {
            "lat": 28.6139,
            "lon": 77.209
        }
    }

@app.post("/stop-session")
def stop_session(charger_id: str):
    if charger_status["status"] != "Charging" or not charger_status["current_session"]:
        raise HTTPException(status_code=400, detail="No active session to stop")
    if charger_status["current_session"]["charger_id"] != charger_id:
        raise HTTPException(status_code=400, detail="Charger ID does not match the active session")
    session = charger_status["current_session"]
    session["end_time"] = datetime.utcnow().isoformat()
    charger_status["status"] = "Available"
    charger_status["current_session"] = None
    logger.info(f"Stopped charging session for user {session['charger_id']}")
    return {
        "status": "True",
        "message": "Charging stopped",
        "last_session": session,
        "battery_level": 0.6000000000000001,
        "charging_cost": "$0.12"
    }

@app.get("/status")
def get_status():
    return charger_status

@app.get("/get-charger-third-party-data")
async def get_charger_metadata():
    try:
        timeout = httpx.Timeout(10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get("https://jsonplaceholder.typicode.com/posts")
            response.raise_for_status()
            data = response.json()
            logger.info("Successfully fetched charger metadata from third-party API.")
            return data
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(status_code=500, detail=f"Request error: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error: {e.response.text}")
    except httpx.TimeoutException as e:
        logger.error(f"Timeout error: {e}")
        raise HTTPException(status_code=408, detail="Request timed out")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")
