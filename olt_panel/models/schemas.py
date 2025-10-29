from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ActionResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    output: Optional[str] = None
    data: Optional[dict[str, Any]] = None


class CommandRequest(BaseModel):
    commands: list[str] = Field(default_factory=list, description="Commands to execute sequentially over SSH")
    stop_on_error: bool = Field(default=False, description="Stop at first error keyword match")


class ONUAddRequest(BaseModel):
    device_name: str | None = Field(default=None, description="Optional override; otherwise path param used")
    pon_port: str = Field(description="PON OLT port, e.g. 1/1/1")
    onu_id: int = Field(ge=1, description="ONU ID to assign on that PON port")
    serial_number: str = Field(description="ONU serial number")
    description: str | None = Field(default=None, description="ONU description/label")
    line_profile: str | None = Field(default=None, description="Line profile name (if used)")
    service_profile: str | None = Field(default=None, description="Service profile name (if used)")


class ONUDeleteRequest(BaseModel):
    device_name: str | None = Field(default=None)
    pon_port: str = Field(description="PON OLT port, e.g. 1/1/1")
    onu_id: int = Field(ge=1)
