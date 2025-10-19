from typing import Dict, Optional, Tuple
from lxml import etree

# Namespace URIs used by TR-069 / CWMP over SOAP 1.1
SOAP_ENV = "http://schemas.xmlsoap.org/soap/envelope/"
SOAP_ENC = "http://schemas.xmlsoap.org/soap/encoding/"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
XSD = "http://www.w3.org/2001/XMLSchema"
CWMP = "urn:dslforum-org:cwmp-1-0"

NSMAP = {
    "soapenv": SOAP_ENV,
    "SOAP-ENC": SOAP_ENC,
    "xsi": XSI,
    "xsd": XSD,
    "cwmp": CWMP,
}


def _first_element_child(parent: etree._Element) -> Optional[etree._Element]:
    for child in parent:
        if isinstance(child.tag, str):
            return child
    return None


def parse_cwmp_request(xml_bytes: bytes) -> Dict[str, Optional[str]]:
    """Parse incoming SOAP XML and extract CWMP method and header fields.

    Returns a dict with keys: method_name, cwmp_id, xml_root.
    """
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        raise ValueError(f"Invalid XML: {exc}") from exc

    body = root.find("{http://schemas.xmlsoap.org/soap/envelope/}Body")
    header = root.find("{http://schemas.xmlsoap.org/soap/envelope/}Header")

    if body is None:
        raise ValueError("SOAP Body not found")

    method_el = _first_element_child(body)
    method_name: Optional[str] = None
    if method_el is not None:
        method_name = etree.QName(method_el).localname

    cwmp_id: Optional[str] = None
    if header is not None:
        id_el = header.find(f"{{{CWMP}}}ID")
        if id_el is not None and id_el.text is not None:
            cwmp_id = id_el.text.strip()

    return {
        "method_name": method_name,
        "cwmp_id": cwmp_id,
        "xml_root": root,
    }


def build_envelope(body_child: etree._Element, cwmp_id: Optional[str]) -> bytes:
    """Build a SOAP 1.1 envelope with CWMP headers and given body child element.

    The returned value is a UTF-8 encoded XML bytes payload ready to send.
    """
    envelope = etree.Element(etree.QName(SOAP_ENV, "Envelope"), nsmap=NSMAP)

    header = etree.SubElement(envelope, etree.QName(SOAP_ENV, "Header"))
    if cwmp_id:
        id_el = etree.SubElement(header, etree.QName(CWMP, "ID"))
        id_el.set(etree.QName(SOAP_ENV, "mustUnderstand"), "1")
        id_el.text = cwmp_id

    # It's acceptable to omit HoldRequests unless flow control is needed.
    # hold_el = etree.SubElement(header, etree.QName(CWMP, "HoldRequests"))
    # hold_el.text = "0"

    body = etree.SubElement(envelope, etree.QName(SOAP_ENV, "Body"))
    body.append(body_child)

    return etree.tostring(
        envelope,
        xml_declaration=True,
        encoding="utf-8",
        pretty_print=True,
    )


def build_inform_response(max_envelopes: int = 1) -> etree._Element:
    """Create cwmp:InformResponse element."""
    resp = etree.Element(etree.QName(CWMP, "InformResponse"))
    max_env_el = etree.SubElement(resp, "MaxEnvelopes")
    max_env_el.text = str(max_envelopes)
    return resp


SUPPORTED_ACS_METHODS = [
    # Common ACS-initiated RPCs this ACS may choose to send to CPEs
    "GetParameterValues",
    "SetParameterValues",
    "AddObject",
    "DeleteObject",
    "Reboot",
    "Download",
    "Upload",
    "FactoryReset",
]


def build_get_rpc_methods_response(methods: Optional[list] = None) -> etree._Element:
    """Create cwmp:GetRPCMethodsResponse listing RPCs supported by the ACS."""
    if methods is None:
        methods = SUPPORTED_ACS_METHODS

    resp = etree.Element(etree.QName(CWMP, "GetRPCMethodsResponse"))

    method_list_el = etree.SubElement(resp, "MethodList")
    # Array typing per SOAP encoding
    method_list_el.set(etree.QName(XSI, "type"), "SOAP-ENC:Array")
    method_list_el.set(etree.QName(SOAP_ENC, "arrayType"), f"xsd:string[{len(methods)}]")

    for name in methods:
        item = etree.SubElement(method_list_el, "string")
        item.text = name

    return resp


def build_fault(fault_code: str, fault_string: str, detail_text: Optional[str] = None) -> etree._Element:
    """Create a SOAP 1.1 Fault with cwmp:Fault detail.

    fault_code: e.g. "Client" or "Server"
    fault_string: human-readable string
    detail_text: optional cwmp fault details
    """
    fault = etree.Element("Fault")

    fault_code_el = etree.SubElement(fault, "faultcode")
    fault_code_el.text = fault_code

    fault_string_el = etree.SubElement(fault, "faultstring")
    fault_string_el.text = fault_string

    detail_el = etree.SubElement(fault, "detail")
    cwmp_fault = etree.SubElement(detail_el, etree.QName(CWMP, "Fault"))

    fault_struct_code = etree.SubElement(cwmp_fault, "FaultCode")
    fault_struct_code.text = "9000"  # Generic fault code per TR-069 appendix (placeholder)

    fault_struct_string = etree.SubElement(cwmp_fault, "FaultString")
    fault_struct_string.text = detail_text or fault_string

    return fault
