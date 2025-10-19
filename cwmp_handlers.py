"""
CWMP (TR-069) Protocol Handlers
Implementation of CWMP RPC methods and message handlers
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class CWMPHandlers:
    """CWMP RPC method handlers"""
    
    def __init__(self):
        self.namespace = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'cwmp': 'urn:dslforum-org:cwmp-1-0'
        }
    
    def create_get_rpc_methods(self) -> str:
        """Create GetRPCMethods request"""
        soap_env = '''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">{}</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:GetRPCMethods/>
    </soap:Body>
</soap:Envelope>'''.format(str(uuid.uuid4()))
        return soap_env
    
    def create_get_parameter_values(self, parameters: List[str]) -> str:
        """Create GetParameterValues request"""
        param_list = ""
        for i, param in enumerate(parameters):
            param_list += f'''
            <ParameterNames arrayType="xsd:string[{len(parameters)}]">
                <string>{param}</string>
            </ParameterNames>'''
        
        soap_env = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">{str(uuid.uuid4())}</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:GetParameterValues>
            <ParameterNames soap-enc:arrayType="xsd:string[{len(parameters)}]" xmlns:soap-enc="http://schemas.xmlsoap.org/soap/encoding/">
                {chr(10).join(f'<string>{param}</string>' for param in parameters)}
            </ParameterNames>
        </cwmp:GetParameterValues>
    </soap:Body>
</soap:Envelope>'''
        return soap_env
    
    def create_set_parameter_values(self, parameters: Dict[str, Any]) -> str:
        """Create SetParameterValues request"""
        param_structs = ""
        for name, value in parameters.items():
            param_structs += f'''
            <ParameterValueStruct>
                <Name>{name}</Name>
                <Value xsi:type="xsd:string">{value}</Value>
            </ParameterValueStruct>'''
        
        soap_env = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">{str(uuid.uuid4())}</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:SetParameterValues>
            <ParameterList soap-enc:arrayType="cwmp:ParameterValueStruct[{len(parameters)}]" xmlns:soap-enc="http://schemas.xmlsoap.org/soap/encoding/">
                {param_structs}
            </ParameterList>
            <ParameterKey></ParameterKey>
        </cwmp:SetParameterValues>
    </soap:Body>
</soap:Envelope>'''
        return soap_env
    
    def create_add_object(self, object_name: str) -> str:
        """Create AddObject request"""
        soap_env = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">{str(uuid.uuid4())}</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:AddObject>
            <ObjectName>{object_name}</ObjectName>
            <ParameterKey></ParameterKey>
        </cwmp:AddObject>
    </soap:Body>
</soap:Envelope>'''
        return soap_env
    
    def create_delete_object(self, object_name: str) -> str:
        """Create DeleteObject request"""
        soap_env = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">{str(uuid.uuid4())}</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:DeleteObject>
            <ObjectName>{object_name}</ObjectName>
            <ParameterKey></ParameterKey>
        </cwmp:DeleteObject>
    </soap:Body>
</soap:Envelope>'''
        return soap_env
    
    def create_reboot(self) -> str:
        """Create Reboot request"""
        soap_env = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">{str(uuid.uuid4())}</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:Reboot>
            <CommandKey>reboot_{datetime.now().strftime('%Y%m%d_%H%M%S')}</CommandKey>
        </cwmp:Reboot>
    </soap:Body>
</soap:Envelope>'''
        return soap_env
    
    def create_factory_reset(self) -> str:
        """Create FactoryReset request"""
        soap_env = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">{str(uuid.uuid4())}</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:FactoryReset/>
    </soap:Body>
</soap:Envelope>'''
        return soap_env
    
    def create_download(self, file_type: str, url: str, username: str = "", password: str = "") -> str:
        """Create Download request"""
        soap_env = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">{str(uuid.uuid4())}</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:Download>
            <CommandKey>download_{datetime.now().strftime('%Y%m%d_%H%M%S')}</CommandKey>
            <FileType>{file_type}</FileType>
            <URL>{url}</URL>
            <Username>{username}</Username>
            <Password>{password}</Password>
            <FileSize>0</FileSize>
            <TargetFileName></TargetFileName>
            <DelaySeconds>0</DelaySeconds>
            <SuccessURL></SuccessURL>
            <FailureURL></FailureURL>
        </cwmp:Download>
    </soap:Body>
</soap:Envelope>'''
        return soap_env
    
    def create_upload(self, file_type: str, url: str, username: str = "", password: str = "") -> str:
        """Create Upload request"""
        soap_env = f'''<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:cwmp="urn:dslforum-org:cwmp-1-0">
    <soap:Header>
        <cwmp:ID soap:mustUnderstand="1">{str(uuid.uuid4())}</cwmp:ID>
    </soap:Header>
    <soap:Body>
        <cwmp:Upload>
            <CommandKey>upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}</CommandKey>
            <FileType>{file_type}</FileType>
            <URL>{url}</URL>
            <Username>{username}</Username>
            <Password>{password}</Password>
            <DelaySeconds>0</DelaySeconds>
        </cwmp:Upload>
    </soap:Body>
</soap:Envelope>'''
        return soap_env
    
    def parse_inform_response(self, xml_data: str) -> Dict[str, Any]:
        """Parse InformResponse message"""
        try:
            root = ET.fromstring(xml_data)
            
            # Find InformResponse
            inform_response = None
            for elem in root.iter():
                if 'InformResponse' in elem.tag:
                    inform_response = elem
                    break
            
            if inform_response is not None:
                max_envelopes = 1
                for child in inform_response:
                    if 'MaxEnvelopes' in child.tag:
                        max_envelopes = int(child.text or 1)
                
                return {
                    'message_type': 'InformResponse',
                    'max_envelopes': max_envelopes
                }
            
            return {'message_type': 'Unknown'}
            
        except ET.ParseError as e:
            logger.error(f"Error parsing InformResponse: {e}")
            return {'error': str(e)}
    
    def parse_get_parameter_values_response(self, xml_data: str) -> Dict[str, Any]:
        """Parse GetParameterValuesResponse message"""
        try:
            root = ET.fromstring(xml_data)
            parameters = {}
            
            for elem in root.iter():
                if 'ParameterValueStruct' in elem.tag:
                    name = None
                    value = None
                    for child in elem:
                        if 'Name' in child.tag:
                            name = child.text
                        elif 'Value' in child.tag:
                            value = child.text
                    
                    if name and value is not None:
                        parameters[name] = value
            
            return {
                'message_type': 'GetParameterValuesResponse',
                'parameters': parameters
            }
            
        except ET.ParseError as e:
            logger.error(f"Error parsing GetParameterValuesResponse: {e}")
            return {'error': str(e)}
    
    def parse_set_parameter_values_response(self, xml_data: str) -> Dict[str, Any]:
        """Parse SetParameterValuesResponse message"""
        try:
            root = ET.fromstring(xml_data)
            
            status = 0
            for elem in root.iter():
                if 'Status' in elem.tag:
                    status = int(elem.text or 0)
            
            return {
                'message_type': 'SetParameterValuesResponse',
                'status': status
            }
            
        except ET.ParseError as e:
            logger.error(f"Error parsing SetParameterValuesResponse: {e}")
            return {'error': str(e)}
    
    def parse_fault_response(self, xml_data: str) -> Dict[str, Any]:
        """Parse SOAP Fault response"""
        try:
            root = ET.fromstring(xml_data)
            
            fault_code = ""
            fault_string = ""
            
            for elem in root.iter():
                if 'faultcode' in elem.tag:
                    fault_code = elem.text or ""
                elif 'faultstring' in elem.tag:
                    fault_string = elem.text or ""
            
            return {
                'message_type': 'Fault',
                'fault_code': fault_code,
                'fault_string': fault_string
            }
            
        except ET.ParseError as e:
            logger.error(f"Error parsing Fault response: {e}")
            return {'error': str(e)}

class CWMPMessageBuilder:
    """Helper class to build CWMP messages"""
    
    @staticmethod
    def prettify_xml(xml_string: str) -> str:
        """Format XML string for better readability"""
        try:
            parsed = minidom.parseString(xml_string)
            return parsed.toprettyxml(indent="  ")
        except Exception:
            return xml_string
    
    @staticmethod
    def extract_soap_header_id(xml_data: str) -> Optional[str]:
        """Extract SOAP header ID from message"""
        try:
            root = ET.fromstring(xml_data)
            for elem in root.iter():
                if 'ID' in elem.tag:
                    return elem.text
            return None
        except ET.ParseError:
            return None
    
    @staticmethod
    def validate_cwmp_message(xml_data: str) -> bool:
        """Validate CWMP message format"""
        try:
            root = ET.fromstring(xml_data)
            
            # Check for SOAP envelope
            if 'Envelope' not in root.tag:
                return False
            
            # Check for required namespaces
            required_ns = ['soap', 'cwmp']
            for ns in required_ns:
                if ns not in str(root.attrib):
                    return False
            
            return True
            
        except ET.ParseError:
            return False