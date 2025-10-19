from __future__ import annotations

from typing import Dict, Optional, Tuple
import xml.etree.ElementTree as ET

SOAP_ENV_URI = "http://schemas.xmlsoap.org/soap/envelope/"
CWMP_DEFAULT_URI = "urn:dslforum-org:cwmp-1-2"

# Register common namespaces for pretty output
ET.register_namespace("SOAP-ENV", SOAP_ENV_URI)
ET.register_namespace("cwmp", CWMP_DEFAULT_URI)
ET.register_namespace("xsd", "http://www.w3.org/2001/XMLSchema")
ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")


def get_localname(tag: str) -> str:
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def find_child_by_localname(parent: ET.Element, localname: str) -> Optional[ET.Element]:
    for child in list(parent):
        if get_localname(child.tag) == localname:
            return child
    return None


def parse_request(xml_bytes: bytes) -> Tuple[str, Optional[str], ET.Element, str]:
    """
    Parse an incoming CWMP SOAP request.

    Returns: (method_name, cwmp_id, method_elem, cwmp_namespace_uri)
    - method_name: e.g. "Inform", "TransferComplete"; "" if empty body
    - cwmp_id: the cwmp:ID value if present, else None
    - method_elem: the first element in Body (if present)
    - cwmp_namespace_uri: CWMP namespace URI to reuse in responses
    """
    root = ET.fromstring(xml_bytes)

    header = find_child_by_localname(root, "Header")
    body = find_child_by_localname(root, "Body")
    if body is None:
        raise ValueError("SOAP Body not found")

    cwmp_id = None
    cwmp_ns_uri = CWMP_DEFAULT_URI

    if header is not None:
        id_elem = None
        for child in list(header):
            if get_localname(child.tag) == "ID":
                id_elem = child
                break
        if id_elem is not None:
            cwmp_id = (id_elem.text or "").strip() or None
            if id_elem.tag.startswith("{"):
                cwmp_ns_uri = id_elem.tag[1:].split("}", 1)[0] or cwmp_ns_uri

    method_elem = None
    for child in list(body):
        # skip text/whitespace nodes; ElementTree returns only elements here
        method_elem = child
        break

    if method_elem is None:
        return "", cwmp_id, body, cwmp_ns_uri

    if method_elem.tag.startswith("{"):
        cwmp_ns_uri = method_elem.tag[1:].split("}", 1)[0] or cwmp_ns_uri

    method_name = get_localname(method_elem.tag)
    return method_name, cwmp_id, method_elem, cwmp_ns_uri


def build_envelope(cwmp_ns_uri: str, cwmp_id: Optional[str]) -> Tuple[ET.Element, ET.Element]:
    """Create a SOAP Envelope with Header (echo cwmp:ID if provided) and Body."""
    # Ensure response uses request CWMP namespace for maximum compatibility
    ET.register_namespace("cwmp", cwmp_ns_uri)

    env = ET.Element(f"{{{SOAP_ENV_URI}}}Envelope")

    header = ET.SubElement(env, f"{{{SOAP_ENV_URI}}}Header")
    if cwmp_id:
        id_elem = ET.SubElement(header, f"{{{cwmp_ns_uri}}}ID")
        id_elem.set(f"{{{SOAP_ENV_URI}}}mustUnderstand", "1")
        id_elem.text = cwmp_id

    body = ET.SubElement(env, f"{{{SOAP_ENV_URI}}}Body")
    return env, body


def build_inform_response(cwmp_id: Optional[str], cwmp_ns_uri: str, max_envelopes: int = 1) -> bytes:
    env, body = build_envelope(cwmp_ns_uri, cwmp_id)
    resp = ET.SubElement(body, f"{{{cwmp_ns_uri}}}InformResponse")
    max_env = ET.SubElement(resp, "MaxEnvelopes")
    max_env.text = str(max_envelopes)
    return serialize_xml(env)


def build_transfer_complete_response(cwmp_id: Optional[str], cwmp_ns_uri: str) -> bytes:
    env, body = build_envelope(cwmp_ns_uri, cwmp_id)
    ET.SubElement(body, f"{{{cwmp_ns_uri}}}TransferCompleteResponse")
    return serialize_xml(env)


def parse_inform(method_elem: ET.Element) -> Dict:
    """Extract useful data from an Inform RPC for storage."""
    device_id_data = {
        "manufacturer": "",
        "oui": "",
        "productClass": "",
        "serialNumber": "",
    }

    device_id_elem = find_child_by_localname(method_elem, "DeviceId")
    if device_id_elem is not None:
        man = find_child_by_localname(device_id_elem, "Manufacturer")
        oui = find_child_by_localname(device_id_elem, "OUI")
        pclass = find_child_by_localname(device_id_elem, "ProductClass")
        sn = find_child_by_localname(device_id_elem, "SerialNumber")
        device_id_data["manufacturer"] = (man.text or "").strip() if man is not None else ""
        device_id_data["oui"] = (oui.text or "").strip() if oui is not None else ""
        device_id_data["productClass"] = (pclass.text or "").strip() if pclass is not None else ""
        device_id_data["serialNumber"] = (sn.text or "").strip() if sn is not None else ""

    events: list[Dict[str, str]] = []
    event_list_elem = find_child_by_localname(method_elem, "Event")
    if event_list_elem is not None:
        for ev in list(event_list_elem):
            if get_localname(ev.tag) != "EventStruct":
                continue
            code = find_child_by_localname(ev, "EventCode")
            cmdk = find_child_by_localname(ev, "CommandKey")
            events.append(
                {
                    "eventCode": (code.text or "").strip() if code is not None else "",
                    "commandKey": (cmdk.text or "").strip() if cmdk is not None else "",
                }
            )

    params: Dict[str, str] = {}
    plist = find_child_by_localname(method_elem, "ParameterList")
    if plist is not None:
        for p in list(plist):
            if get_localname(p.tag) != "ParameterValueStruct":
                continue
            name_elem = find_child_by_localname(p, "Name")
            value_elem = find_child_by_localname(p, "Value")
            if name_elem is None or value_elem is None:
                continue
            name = (name_elem.text or "").strip()
            value = (value_elem.text or "").strip()
            if name:
                params[name] = value

    return {
        "deviceId": device_id_data,
        "events": events,
        "parameterValues": params,
    }


def serialize_xml(elem: ET.Element) -> bytes:
    xml_bytes = ET.tostring(elem, encoding="utf-8")
    return b"<?xml version=\"1.0\" encoding=\"utf-8\"?>" + xml_bytes
