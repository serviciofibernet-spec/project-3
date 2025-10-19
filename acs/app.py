from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, Response

from . import cwmp
from .storage import DeviceStore


app = FastAPI(title="Python TR-069 ACS", version="0.1.0")
store = DeviceStore()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/devices")
async def list_devices() -> list[dict]:
    return store.list_devices()


@app.get("/devices/{serial}")
async def get_device(serial: str) -> dict:
    device = store.get_device(serial)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@app.post("/cwmp")
async def cwmp_endpoint(request: Request) -> Response:
    raw = await request.body()
    if raw is None or not raw.strip():
        return Response(status_code=204)

    try:
        method_name, cwmp_id, method_elem, cwmp_ns = cwmp.parse_request(raw)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Invalid SOAP: {exc}")

    if not method_name:
        return Response(status_code=204)

    if method_name == "Inform":
        inform_data = cwmp.parse_inform(method_elem)
        store.upsert_inform(inform_data)
        xml = cwmp.build_inform_response(cwmp_id, cwmp_ns)
        return Response(content=xml, media_type="text/xml; charset=utf-8")

    if method_name == "TransferComplete":
        xml = cwmp.build_transfer_complete_response(cwmp_id, cwmp_ns)
        return Response(content=xml, media_type="text/xml; charset=utf-8")

    # No tasks for the device; end session
    return Response(status_code=204)
