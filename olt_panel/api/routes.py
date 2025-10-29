from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, HTTPException, Query

from ..models import ActionResponse, CommandRequest, ONUAddRequest, ONUDeleteRequest
from ..services import get_olt_service

router = APIRouter()


@router.get("/health", response_model=dict)
def health() -> dict:
    return {"status": "ok"}


@router.get("/olt/devices", response_model=list[dict])
def list_devices() -> list[dict]:
    service = get_olt_service()
    devices = service.list_devices()
    return [
        {
            "name": d.name,
            "host": d.host,
            "port": d.port,
            "driver": d.driver,
        }
        for d in devices
    ]


@router.get("/olt/{device_name}/version", response_model=ActionResponse)
def get_version(device_name: str) -> ActionResponse:
    service = get_olt_service()
    try:
        driver = service.get_driver(device_name)
        out = driver.get_version()
        return ActionResponse(success=True, output=out)
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/olt/{device_name}/onus", response_model=ActionResponse)
def list_onus(device_name: str, pon_port: Optional[str] = Query(default=None)) -> ActionResponse:
    service = get_olt_service()
    try:
        driver = service.get_driver(device_name)
        out = driver.list_onus(pon_port=pon_port)
        return ActionResponse(success=True, output=out)
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.post("/olt/{device_name}/onu", response_model=ActionResponse)
def add_onu(device_name: str, payload: ONUAddRequest = Body(...)) -> ActionResponse:
    service = get_olt_service()
    try:
        driver = service.get_driver(device_name)
        out = driver.add_onu(
            pon_port=payload.pon_port,
            onu_id=payload.onu_id,
            serial_number=payload.serial_number,
            description=payload.description,
            line_profile=payload.line_profile,
            service_profile=payload.service_profile,
        )
        return ActionResponse(success=True, output=out)
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.delete("/olt/{device_name}/onu", response_model=ActionResponse)
def delete_onu(device_name: str, payload: ONUDeleteRequest = Body(...)) -> ActionResponse:
    service = get_olt_service()
    try:
        driver = service.get_driver(device_name)
        out = driver.delete_onu(pon_port=payload.pon_port, onu_id=payload.onu_id)
        return ActionResponse(success=True, output=out)
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.post("/olt/{device_name}/command", response_model=ActionResponse)
def run_commands(device_name: str, payload: CommandRequest = Body(...)) -> ActionResponse:
    service = get_olt_service()
    try:
        driver = service.get_driver(device_name)
        out = driver.send_raw_commands(payload.commands, stop_on_error=payload.stop_on_error)
        return ActionResponse(success=True, output=out)
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))
