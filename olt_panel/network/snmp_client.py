from __future__ import annotations

from typing import Optional

from pysnmp.hlapi import (  # type: ignore
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    getCmd,
)


class SNMPClient:
    def __init__(self, host: str, community: str = "public", port: int = 161, timeout_s: int = 2, retries: int = 1):
        self.host = host
        self.community = community
        self.port = port
        self.timeout_s = timeout_s
        self.retries = retries

    def get(self, oid: str) -> Optional[str]:
        iterator = getCmd(
            SnmpEngine(),
            CommunityData(self.community, mpModel=0),
            UdpTransportTarget((self.host, self.port), timeout=self.timeout_s, retries=self.retries),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
        )
        error_indication, error_status, error_index, var_binds = next(iterator)
        if error_indication or error_status:
            return None
        for name, val in var_binds:
            return str(val)
        return None
